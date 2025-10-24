from __future__ import annotations

from typing import Sequence, TypeGuard, overload

import vapoursynth as vs
from jetpytools import FuncExcept

from ..enums import FieldBased
from ..exceptions import (
    FormatsRefClipMismatchError,
    ResolutionsRefClipMismatchError,
    UnsupportedFieldBasedError,
    VariableFormatError,
    VariableResolutionError,
)
from ..types import ConstantFormatVideoNode, VideoNodeT

__all__ = [
    "check_correct_subsampling",
    "check_progressive",
    "check_ref_clip",
    "check_variable",
    "check_variable_format",
    "check_variable_resolution",
]


def check_ref_clip(
    src: vs.VideoNode, ref: vs.VideoNode | None, func: FuncExcept | None = None
) -> ConstantFormatVideoNode:
    """
    Function for ensuring the ref clip's format matches that of the input clip.

    If no ref clip can be found, this function will simply do nothing.

    Args:
        src: Input clip.
        ref: Reference clip. Default: None.

    Raises:
        VariableFormatError: The format of either clip is variable.
        VariableResolutionError: The resolution of either clip is variable.
        FormatsRefClipMismatchError: The formats of the two clips do not match.
        ResolutionsRefClipMismatchError: The resolutions of the two clips do not match.

    Returns:
        Ref clip.
    """
    func = func or check_ref_clip

    assert check_variable(src, func)

    if ref is None:
        return src

    assert check_variable(ref, func)

    FormatsRefClipMismatchError.check(func, src, ref)
    ResolutionsRefClipMismatchError.check(func, src, ref)

    return ref


@overload
def check_variable_format(clip: vs.VideoNode, func: FuncExcept) -> TypeGuard[ConstantFormatVideoNode]: ...


@overload
def check_variable_format(
    clip: Sequence[vs.VideoNode], func: FuncExcept
) -> TypeGuard[Sequence[ConstantFormatVideoNode]]: ...


def check_variable_format(
    clip: vs.VideoNode | Sequence[vs.VideoNode], func: FuncExcept
) -> TypeGuard[ConstantFormatVideoNode] | TypeGuard[Sequence[ConstantFormatVideoNode]]:
    """
    Check for variable format and return an error if found.

    Raises:
        VariableFormatError: The clip is of a variable format.
    """
    clip = [clip] if isinstance(clip, vs.VideoNode) else clip

    for c in clip:
        if c.format is None:
            raise VariableFormatError(func)

    return True


def check_variable_resolution(clip: VideoNodeT, func: FuncExcept) -> TypeGuard[VideoNodeT]:
    """
    Check for variable width or height and return an error if found.

    Raises:
        VariableResolutionError: The clip has a variable resolution.
    """

    if 0 in (clip.width, clip.height):
        raise VariableResolutionError(func)

    return True


def check_variable(clip: vs.VideoNode, func: FuncExcept) -> TypeGuard[ConstantFormatVideoNode]:
    """
    Check for variable format and a variable resolution and return an error if found.

    Raises:
        VariableFormatError: The clip is of a variable format.
        VariableResolutionError: The clip has a variable resolution.
    """

    check_variable_format(clip, func)
    check_variable_resolution(clip, func)

    return True


def check_correct_subsampling(
    clip: vs.VideoNode, width: int | None = None, height: int | None = None, func: FuncExcept | None = None
) -> None:
    """
    Check if the subsampling is correct and return an error if it's not.

    Args:
        clip: Clip to check.
        width: Output width.
        height: Output height.
        func: Function returned for custom error handling. This should only be set by VS package developers.

    Raises:
        InvalidSubsamplingError: The clip has invalid subsampling.
    """
    from ..exceptions import InvalidSubsamplingError

    if clip.format and (
        (width is not None and width % (1 << clip.format.subsampling_w))
        or (height is not None and height % (1 << clip.format.subsampling_h))
    ):
        raise InvalidSubsamplingError(
            func or check_correct_subsampling,
            clip,
            "The {subsampling} subsampling is not supported for this resolution!",
            reason={"width": width, "height": height},
        )


def check_progressive(clip: VideoNodeT, func: FuncExcept) -> TypeGuard[VideoNodeT]:
    """
    Check if the clip is progressive and return an error if it's not.

    Args:
        clip: Clip to check.
        func: Function returned for custom error handling. This should only be set by VS package developers.

    Raises:
        UnsupportedFieldBasedError: The clip is interlaced.
    """

    if FieldBased.from_video(clip, func=func).is_inter:
        raise UnsupportedFieldBasedError("Only progressive video is supported!", func)

    return True
