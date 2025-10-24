from __future__ import annotations

from contextlib import AbstractContextManager, suppress
from dataclasses import dataclass
from functools import cache, partial, wraps
from math import exp
from types import GenericAlias
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Concatenate,
    Generic,
    Union,
    overload,
)

from jetpytools import P, classproperty
from typing_extensions import Self, TypeIs, TypeVar, TypeVarTuple, Unpack

from vsexprtools import norm_expr
from vstools import (
    ConstantFormatVideoNode,
    CustomRuntimeError,
    CustomValueError,
    HoldsVideoFormat,
    Matrix,
    MatrixLike,
    Transfer,
    VideoFormatLike,
    VSFunctionNoArgs,
    cachedproperty,
    check_variable_format,
    depth,
    get_video_format,
    vs,
    vs_object,
)

from .abstract import (
    Bobber,
    BobberLike,
    ComplexDescaler,
    ComplexDescalerLike,
    ComplexKernel,
    ComplexKernelLike,
    ComplexScaler,
    ComplexScalerLike,
    CustomComplexKernel,
    CustomComplexKernelLike,
    Descaler,
    DescalerLike,
    Kernel,
    KernelLike,
    Resampler,
    ResamplerLike,
    Scaler,
    ScalerLike,
)
from .abstract.base import BaseScaler, BaseScalerMeta, _BaseScalerT
from .kernels import Catrom, Point
from .types import Center, LeftShift, Slope, TopShift

__all__ = [
    "BaseMixedScaler",
    "BaseScalerSpecializer",
    "LinearLight",
    "MixedScalerProcess",
    "NoScale",
    "NoScaleLike",
    "is_complex_descaler_like",
    "is_complex_kernel_like",
    "is_complex_scaler_like",
    "is_custom_complex_kernel_like",
    "is_descaler_like",
    "is_kernel_like",
    "is_noscale_like",
    "is_resampler_like",
    "is_scaler_like",
    "resample_to",
]


@cache
def _add_specializer_in_str(cls: BaseScalerSpecializerMeta) -> None:
    if cls.__specializer__:
        cls.__name__ += f"[{cls.__specializer__.__name__}]"


class BaseScalerSpecializerMeta(BaseScalerMeta):
    """
    Meta class for BaseScalerSpecializer to handle specialization logic.
    """

    __specializer__: type[BaseScaler] | None

    def __new__(  # noqa: PYI019
        mcls: type[_BaseScalerSpecializerMetaT],
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        *,
        specializer: type[BaseScaler] | None = None,
        **kwargs: Any,
    ) -> _BaseScalerSpecializerMetaT:
        if specializer is not None:
            bases = (specializer, *bases)
            namespace["__orig_bases__"] = (specializer, *namespace["__orig_bases__"])

            with suppress(KeyError):
                del namespace["kernel_radius"]

        obj = super().__new__(mcls, name, bases, namespace, **kwargs)
        obj.__specializer__ = specializer

        return obj

    @property
    def __isspecialized__(self) -> bool:
        return bool(self.__specializer__)


_BaseScalerTs = TypeVarTuple("_BaseScalerTs")
_BaseScalerSpecializerMetaT = TypeVar("_BaseScalerSpecializerMetaT", bound=BaseScalerSpecializerMeta)
_ScalerT = TypeVar("_ScalerT", bound=Scaler)
_ScalerWithCatromDefaultT = TypeVar("_ScalerWithCatromDefaultT", bound=Scaler, default=Catrom)


class BaseScalerSpecializer(BaseScaler, Generic[_BaseScalerT], metaclass=BaseScalerSpecializerMeta, abstract=True):
    """
    An abstract base class to provide specialization logic for Scaler-like classes.
    """

    _default_scaler: ClassVar[type[BaseScaler]]

    if not TYPE_CHECKING:

        def __new__(cls, *args: Any, **kwargs: Any) -> Self:
            if not cls.__isspecialized__:
                return cls.__class_getitem__(cls._default_scaler)(*args, **kwargs)

            return super().__new__(cls, *args, **kwargs)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()

        for k in kwargs.copy():
            if hasattr(self, k):
                setattr(self, k, kwargs.pop(k))

        self.kwargs = kwargs

    def __str__(self) -> str:
        _add_specializer_in_str(self.__class__)
        return super().__str__()

    def __class_getitem__(cls, base_scaler: Any) -> GenericAlias:
        """
        Specialize this class with a given scaler kernel.

        Args:
            base_scaler: A BaseScaler type used to specialize this class.

        Returns:
            A new subclass using the provided kernel.
        """
        if isinstance(base_scaler, TypeVar):
            return GenericAlias(cls, (base_scaler,))

        specialized_scaler = BaseScalerSpecializerMeta(
            cls.__name__, (cls,), cls.__dict__.copy(), specializer=base_scaler, partial_abstract=True
        )

        return GenericAlias(specialized_scaler, (base_scaler,))


class NoScale(BaseScalerSpecializer[_ScalerWithCatromDefaultT], Scaler, partial_abstract=True):
    """
    A utility scaler class that performs no scaling on the input clip.

    If used without a specified scaler, it defaults to inheriting from `Catrom`.
    """

    _default_scaler = Catrom

    def scale(
        self,
        clip: vs.VideoNode,
        width: int | None = None,
        height: int | None = None,
        shift: tuple[TopShift, LeftShift] = (0, 0),
        **kwargs: Any,
    ) -> vs.VideoNode | ConstantFormatVideoNode:
        """
        Return the input clip unscaled, validating that the dimensions are consistent.

        Args:
            clip: The source clip.
            width: Optional width to validate against the clip's width.
            height: Optional height to validate against the clip's height.
            shift: Subpixel shift (top, left).
            **kwargs: Additional arguments forwarded to the scale function.

        Raises:
            CustomValueError: If `width` or `height` differ from the clip's dimensions.
        """
        width, height = self._wh_norm(clip, width, height)

        if width != clip.width or height != clip.height:
            raise CustomValueError(
                "When using NoScale, `width` and `height` must match the clip's dimensions.",
                self.__class__,
                (width, height),
            )

        if shift == (0, 0) and not kwargs and not self.kwargs:
            return clip

        return super().scale(clip, width, height, shift, **kwargs)

    @classmethod
    def from_scaler(cls, scaler: ScalerLike) -> type[NoScale[Scaler]]:
        """
        Create a specialized NoScale class using a specific scaler.

        Args:
            scaler: A Scaler instance, type or string used as a base for specialization.

        Returns:
            A dynamically created NoScale subclass based on the given scaler.
        """
        return NoScale[Scaler.from_param(scaler)]  # type: ignore[return-value,misc]


NoScaleLike = str | type[NoScale[_ScalerT]] | NoScale[_ScalerT]
"""
Type alias for anything that can resolve to a NoScale scaler.

This includes:
 - A string identifier.
 - A class type subclassing `NoScale`.
 - An instance of `NoScale`.
"""


class BaseMixedScalerMeta(BaseScalerSpecializerMeta, Generic[Unpack[_BaseScalerTs]]):
    """
    Meta class for BaseMixedScaler to handle mixed scaling logic.
    """

    __others__: tuple[Unpack[_BaseScalerTs]]

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        *others: Unpack[_BaseScalerTs],
        specializer: type[BaseScaler] | None = None,
        **kwargs: Any,
    ) -> BaseMixedScalerMeta[Unpack[_BaseScalerTs]]:
        obj = super().__new__(mcls, name, bases, namespace, specializer=specializer, **kwargs)

        if others:
            obj.__others__ = others
        else:
            for t in namespace["__orig_bases__"]:
                if (os := getattr(t, "__others__", ())) or (
                    isinstance(t, GenericAlias) and (os := getattr(t.__origin__, "__others__", ()))
                ):
                    obj.__others__ = os
                    break
            else:
                obj.__others__ = ()  # type: ignore[assignment]

        return obj


class BaseMixedScaler(
    BaseScalerSpecializer[_BaseScalerT],
    Generic[_BaseScalerT, Unpack[_BaseScalerTs]],
    metaclass=BaseMixedScalerMeta,
    abstract=True,
):
    """
    An abstract base class to provide mixed or chained scaling for Scaler-like classes.
    """

    @classproperty
    @classmethod
    def _others(cls) -> tuple[Unpack[_BaseScalerTs]]:
        # Workaround as we can't specify the bound values of a TypeVarTuple yet
        return tuple(o() for o in cls.__others__)  # type: ignore[operator]

    def __class_getitem__(cls, scalers: Any) -> GenericAlias:
        """
        Specialize this class with a given scaler kernel.

        Args:
            base_scaler: A BaseScaler type(s) used to specialize this class.

        Returns:
            A new subclass using the provided kernel.
        """
        if isinstance(scalers, tuple):
            specializer, *others = scalers
        else:
            specializer = scalers
            others = []

        if isinstance(specializer, TypeVar):
            cls.__others__ = tuple(others) or cls.__others__
            return GenericAlias(cls, (specializer, *cls.__others__))

        mixed_spe = BaseMixedScalerMeta.__new__(
            BaseMixedScalerMeta,
            cls.__name__,
            (cls,),
            cls.__dict__.copy(),
            *others,
            specializer=specializer,
            partial_abstract=True,
        )

        return GenericAlias(mixed_spe, (specializer, *others))


class MixedScalerProcess(BaseMixedScaler[_ScalerT, Unpack[_BaseScalerTs]], Scaler, abstract=True):
    """
    An abstract class for chained scaling with an additional processing step.
    """

    def __init__(self, *, function: VSFunctionNoArgs[vs.VideoNode, vs.VideoNode], **kwargs: Any) -> None:
        """
        Initialize the MixedScalerProcess.

        Args:
            function: A function to apply on the scaling pipeline.
            **kwargs: Keyword arguments that configure the internal scaling behavior.
        """
        super().__init__(**kwargs)

        self.function = function


@dataclass
class LinearLightProcessing(vs_object):
    ll: LinearLight

    def get_linear(self) -> vs.VideoNode:
        """
        Getter for `linear` cached property.
        """
        wclip = self.ll._resampler.resample(
            self.ll._wclip,
            vs.RGBS if self.ll._wclip.format.color_family in (vs.YUV, vs.RGB) else vs.GRAYS,
            matrix_in=self.ll._matrix,
            transfer_in=self.ll._curve,
            transfer=Transfer.LINEAR,
        )

        if self.ll.sigmoid:
            wclip = norm_expr(
                wclip,
                "{center} 1 {slope} / 1 x 0 max 1 min {scale} * {offset} + / 1 - log * -",
                center=self.ll._scenter,
                slope=self.ll._sslope,
                scale=self.ll._sscale,
                offset=self.ll._soffset,
                func=self.__class__,
            )

        return wclip

    def set_linear(self, processed: vs.VideoNode) -> None:
        """
        Setter for `linear` cached property.
        """
        if self.ll._exited:
            raise CustomRuntimeError(
                "You can't set .linear after going out of the context manager!", func=self.__class__
            )
        self._linear = processed

    linear = cachedproperty[vs.VideoNode](get_linear, set_linear)
    """
    Cached property to use for linear light processing.
    """

    @cachedproperty
    def out(self) -> vs.VideoNode:
        if not self.ll._exited:
            raise CustomRuntimeError(
                "You can't get .out while still inside of the context manager!", func=self.__class__
            )

        if not hasattr(self, "_linear"):
            raise CustomValueError("You need to set .linear before getting .out!", self.__class__)

        if self.ll.sigmoid:
            processed = norm_expr(
                self._linear,
                "1 1 {slope} {center} x 0 max 1 min - * exp + / {offset} - {scale} /",
                slope=self.ll._sslope,
                center=self.ll._scenter,
                offset=self.ll._soffset,
                scale=self.ll._sscale,
                func=self.__class__,
            )
        else:
            processed = self._linear

        processed = vs.core.resize2.Point(processed, transfer_in=Transfer.LINEAR, transfer=self.ll._curve)

        return resample_to(processed, self.ll._fmt, self.ll._matrix, self.ll._resampler)

    def __vs_del__(self, core_id: int) -> None:
        del self._linear
        cachedproperty.clear_cache(self)


@dataclass
class LinearLight(AbstractContextManager[LinearLightProcessing], vs_object):
    """
    Utility class for processing a clip in linear format.

    Usage:
        ```py
        with LinearLight(clip, ...) as ll:
            ll.linear = function(ll.linear, ...)
        out = ll.out
        ```
    """

    clip: vs.VideoNode
    """Input clip."""

    sigmoid: bool | tuple[Slope, Center] = False
    """
    Whether to use sigmoid transfer curve. Can be True, False, or a tuple of (slope, center).
    `True` applies the defaults values (6.5, 0.75).
    Keep in mind sigmoid slope has to be in range 1.0-20.0. (inclusive)
    and sigmoid center has to be in range 0.0-1.0 (inclusive).
    """

    resampler: ResamplerLike = Catrom
    """Resampler for converting to linear format and converting back to input clip format."""

    out_fmt: int | VideoFormatLike | HoldsVideoFormat | None = None
    """Optional output format."""

    @overload
    @classmethod
    def from_func(
        cls,
        func: Callable[Concatenate[vs.VideoNode, P], vs.VideoNode],
        /,
        sigmoid: bool | tuple[Slope, Center] = False,
        resampler: ResamplerLike = Catrom,
        out_fmt: int | VideoFormatLike | HoldsVideoFormat | None = None,
    ) -> Callable[Concatenate[vs.VideoNode, P], vs.VideoNode]:
        """
        Example:
            ``` py
            @LinearLight.from_func
            def decorated_function(clip: vs.VideoNode, ...) -> vs.VideoNode:
                ...
            ```
        """

    @overload
    @classmethod
    def from_func(
        cls,
        /,
        *,
        sigmoid: bool | tuple[Slope, Center] = False,
        resampler: ResamplerLike = Catrom,
        out_fmt: int | VideoFormatLike | HoldsVideoFormat | None = None,
    ) -> Callable[
        [Callable[Concatenate[vs.VideoNode, P], vs.VideoNode]], Callable[Concatenate[vs.VideoNode, P], vs.VideoNode]
    ]:
        """
        Example:
            ``` py
            @LinearLight.from_func(sigmoid=(6.5, 0.75))
            def decorated_function(clip: vs.VideoNode, ...) -> vs.VideoNode:
                ...
            ```
        """

    @classmethod
    def from_func(
        cls,
        func: Callable[Concatenate[vs.VideoNode, P], vs.VideoNode] | None = None,
        /,
        sigmoid: bool | tuple[Slope, Center] = False,
        resampler: ResamplerLike = Catrom,
        out_fmt: int | VideoFormatLike | HoldsVideoFormat | None = None,
    ) -> Union[
        Callable[Concatenate[vs.VideoNode, P], vs.VideoNode],
        Callable[
            [Callable[Concatenate[vs.VideoNode, P], vs.VideoNode]], Callable[Concatenate[vs.VideoNode, P], vs.VideoNode]
        ],
    ]:
        """
        Decorator version of LinearLight.
        """

        if func is None:
            return partial(cls.from_func, sigmoid=sigmoid, resampler=resampler, out_fmt=out_fmt)

        @wraps(func)
        def _wrapped(clip: vs.VideoNode, *args: P.args, **kwargs: P.kwargs) -> vs.VideoNode:
            with cls(clip, sigmoid, resampler, out_fmt) as ll:
                ll.linear = func(clip, *args, **kwargs)
            return ll.out

        return _wrapped

    def __enter__(self) -> LinearLightProcessing:
        assert check_variable_format(self.clip, self.__class__)

        if self.sigmoid is not False:
            if self.sigmoid is True:
                self.sigmoid = (6.5, 0.75)

            self._sslope, self._scenter = self.sigmoid

            if not 1.0 <= self._sslope <= 20.0:
                raise CustomValueError("sigmoid slope has to be in range 1.0-20.0 (inclusive).", self.__class__)

            if not 0.0 <= self._scenter <= 1.0:
                raise CustomValueError("sigmoid center has to be in range 0.0-1.0 (inclusive).", self.__class__)

            self._soffset = 1.0 / (1 + exp(self._sslope * self._scenter))
            self._sscale = 1.0 / (1 + exp(self._sslope * (self._scenter - 1))) - self._soffset

        self._fmt = self.out_fmt or self.clip.format

        self._wclip = self.clip
        self._curve = Transfer.from_video(self.clip)
        self._matrix = Matrix.from_video(self.clip)
        self._resampler = Resampler.ensure_obj(self.resampler)

        self._exited = False

        return LinearLightProcessing(self)

    def __exit__(self, *args: object, **kwargs: Any) -> None:
        self._exited = True

    def __vs_del__(self, core_id: int) -> None:
        for name in ("clip", "out_fmt", "_fmt", "_wclip"):
            with suppress(AttributeError):
                delattr(self, name)


def resample_to(
    clip: vs.VideoNode,
    out_fmt: int | VideoFormatLike | HoldsVideoFormat,
    matrix: MatrixLike | None = None,
    resampler: ResamplerLike = Catrom,
) -> vs.VideoNode:
    out_fmt = get_video_format(out_fmt)
    assert clip.format

    resampler = Resampler.from_param(resampler)

    if out_fmt == clip.format:
        return clip

    if out_fmt.color_family is clip.format.color_family:
        return depth(clip, out_fmt)

    if out_fmt.subsampling_w == out_fmt.subsampling_h == 0:
        return Point().resample(clip, out_fmt, matrix)

    return resampler().resample(clip, out_fmt, matrix)


def _is_base_scaler_like(obj: Any, base_scaler: type[BaseScaler]) -> bool:
    if isinstance(obj, base_scaler) or (isinstance(obj, BaseScalerMeta) and issubclass(obj, base_scaler)):
        return True

    if isinstance(obj, str):
        try:
            base_scaler.from_param(obj)
        except base_scaler._err_class:
            return False
        else:
            return True

    return False


def is_scaler_like(obj: Any) -> TypeIs[ScalerLike]:
    """Returns true if obj is a ScalerLike"""
    return _is_base_scaler_like(obj, Scaler)


def is_descaler_like(obj: Any) -> TypeIs[DescalerLike]:
    """Returns true if obj is a DescalerLike"""
    return _is_base_scaler_like(obj, Descaler)


def is_resampler_like(obj: Any) -> TypeIs[ResamplerLike]:
    """Returns true if obj is a ResamplerLike"""
    return _is_base_scaler_like(obj, Resampler)


def is_kernel_like(obj: Any) -> TypeIs[KernelLike]:
    """Returns true if obj is a KernelLike"""
    return _is_base_scaler_like(obj, Kernel)


def is_bobber_like(obj: Any) -> TypeIs[BobberLike]:
    """Returns true if obj is a BobberLike"""
    return _is_base_scaler_like(obj, Bobber)


def is_complex_scaler_like(obj: Any) -> TypeIs[ComplexScalerLike]:
    """Returns true if obj is a ComplexScalerLike"""
    return _is_base_scaler_like(obj, ComplexScaler)


def is_complex_descaler_like(obj: Any) -> TypeIs[ComplexDescalerLike]:
    """Returns true if obj is a ComplexDescalerLike"""
    return _is_base_scaler_like(obj, ComplexDescaler)


def is_complex_kernel_like(obj: Any) -> TypeIs[ComplexKernelLike]:
    """Returns true if obj is a ComplexKernelLike"""
    return _is_base_scaler_like(obj, ComplexKernel)


def is_custom_complex_kernel_like(obj: Any) -> TypeIs[CustomComplexKernelLike]:
    """Returns true if obj is a CustomComplexKernelLike"""
    return _is_base_scaler_like(obj, CustomComplexKernel)


def is_noscale_like(obj: Any) -> TypeIs[NoScaleLike[Scaler]]:
    """Returns true if obj is a NoScaleLike"""
    return _is_base_scaler_like(obj, NoScale)
