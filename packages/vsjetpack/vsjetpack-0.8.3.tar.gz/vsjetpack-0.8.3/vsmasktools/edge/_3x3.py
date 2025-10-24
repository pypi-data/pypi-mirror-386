"""
2D matrices.
"""

from __future__ import annotations

import math
from abc import ABC
from typing import Any, ClassVar, Sequence

from jetpytools import interleave_arr, to_arr
from typing_extensions import deprecated

from vsexprtools import ExprList, ExprOp, norm_expr
from vstools import ConstantFormatVideoNode, Planes, join, split, vs

from ..morpho import Morpho
from ..types import XxpandMode
from ._abstract import (
    EdgeDetect,
    EdgeMasksEdgeDetect,
    EuclideanDistance,
    MagnitudeEdgeMasks,
    MagnitudeMatrix,
    MatrixEdgeDetect,
    Max,
    NormalizeProcessor,
    RidgeDetect,
    SingleMatrix,
    TCannyEdgeDetect,
)

# ruff: noqa: RUF022

__all__ = [
    "Matrix3x3",
    # Single matrix
    "Laplacian1",
    "Laplacian2",
    "Laplacian3",
    "Laplacian4",
    "Kayyali",
    # Euclidean Distance
    "Cross",
    "Prewitt",
    "PrewittStd",
    "PrewittTCanny",
    "Sobel",
    "SobelStd",
    "SobelTCanny",
    "ASobel",
    "Scharr",
    "RScharr",
    "ScharrTCanny",
    "Kroon",
    "KroonTCanny",
    "FreyChenG41",
    "FreyChen",
    # Max
    "Robinson3",
    "Robinson5",
    "TheToof",
    "Kirsch",
    "KirschTCanny",
    # Misc
    "MinMax",
]


class Matrix3x3(EdgeDetect, ABC):
    """
    Abstract base class for 3x3 convolution-based edge detectors.
    """


# Single matrix
class Laplacian1(SingleMatrix, Matrix3x3):
    """
    Pierre-Simon de Laplace operator 1st implementation.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[0, -1, 0, -1, 4, -1, 0, -1, 0]]


class Laplacian2(SingleMatrix, Matrix3x3):
    """
    Pierre-Simon de Laplace operator 2nd implementation.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[1, -2, 1, -2, 4, -2, 1, -2, 1]]


class Laplacian3(SingleMatrix, Matrix3x3):
    """
    Pierre-Simon de Laplace operator 3rd implementation.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[2, -1, 2, -1, -4, -1, 2, -1, 2]]


class Laplacian4(SingleMatrix, Matrix3x3):
    """
    Pierre-Simon de Laplace operator 4th implementation.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[-1, -1, -1, -1, 8, -1, -1, -1, -1]]


class Kayyali(SingleMatrix, Matrix3x3):
    """
    Kayyali operator.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[6, 0, -6, 0, 0, 0, -6, 0, 6]]


# Euclidean Distance
class Cross(EdgeMasksEdgeDetect, RidgeDetect, EuclideanDistance, Matrix3x3):
    """
    "HotDoG" Operator from AVS ExTools by Dogway.
    Plain and simple cross first order derivative.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[1, 0, 0, 0, 0, 0, 0, 0, -1], [0, 0, -1, 0, 0, 0, 1, 0, 0]]


class Prewitt(EdgeMasksEdgeDetect, RidgeDetect, EuclideanDistance, Matrix3x3):
    """
    Judith M. S. Prewitt operator.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[1, 0, -1, 1, 0, -1, 1, 0, -1], [1, 1, 1, 0, 0, 0, -1, -1, -1]]


@deprecated(
    "PrewittStd is deprecated and will be removed in a future version. "
    "Please use Prewitt and install the 'edgemasks' plugin instead.",
    category=DeprecationWarning,
)
class PrewittStd(Matrix3x3):
    """
    Judith M. S. Prewitt Vapoursynth plugin operator.
    """

    def _compute_edge_mask(
        self,
        clip: ConstantFormatVideoNode,
        *,
        multi: float | Sequence[float] = 1.0,
        planes: Planes = None,
        **kwargs: Any,
    ) -> ConstantFormatVideoNode:
        if not isinstance(multi, Sequence):
            return clip.std.Prewitt(planes, multi)

        return norm_expr(clip.std.Prewitt(planes), "x {multi} *", planes, func=self.__class__, multi=multi, **kwargs)


@deprecated(
    "PrewittTCanny is deprecated and will be removed in a future version. "
    "Please use Prewitt and install the 'edgemasks' plugin instead.",
    category=DeprecationWarning,
)
class PrewittTCanny(TCannyEdgeDetect, Matrix3x3):
    """
    Judith M. S. Prewitt TCanny plugin operator.
    """

    _op = 1
    _scale = 2.0


class Sobel(EdgeMasksEdgeDetect, RidgeDetect, EuclideanDistance, Matrix3x3):
    """
    Sobel-Feldman operator.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[1, 0, -1, 2, 0, -2, 1, 0, -1], [1, 2, 1, 0, 0, 0, -1, -2, -1]]


@deprecated(
    "SobelStd is deprecated and will be removed in a future version. "
    "Please use Sobel and install the 'edgemasks' plugin instead.",
    category=DeprecationWarning,
)
class SobelStd(Matrix3x3):
    """
    Sobel-Feldman Vapoursynth plugin operator.
    """

    def _compute_edge_mask(
        self,
        clip: ConstantFormatVideoNode,
        *,
        multi: float | Sequence[float] = 1.0,
        planes: Planes = None,
        **kwargs: Any,
    ) -> ConstantFormatVideoNode:
        if not isinstance(multi, Sequence):
            return clip.std.Sobel(planes, multi)

        return norm_expr(clip.std.Sobel(planes), "x {multi} *", planes, func=self.__class__, multi=multi, **kwargs)


@deprecated(
    "SobelTCanny is deprecated and will be removed in a future version. "
    "Please use Sobel and install the 'edgemasks' plugin instead.",
    category=DeprecationWarning,
)
class SobelTCanny(TCannyEdgeDetect, Matrix3x3):
    """
    Sobel-Feldman Vapoursynth plugin operator.
    """

    _op = 2


class ASobel(Matrix3x3, EdgeDetect):
    """
    ASobel from the `AWarpSharp2` VapourSynth plugin.
    """

    def _compute_edge_mask(
        self,
        clip: vs.VideoNode,
        *,
        multi: float | Sequence[float] = 1.0,
        planes: Planes = None,
        **kwargs: Any,
    ) -> ConstantFormatVideoNode:
        expr = (
            "x[-1,-1] x[1,-1] + 2 / x[0,-1] + 2 / AVG_UP!",
            "x[-1,1] x[1,1] + 2 / x[0,1] + 2 / AVG_DOWN!",
            "x[-1,-1] x[-1,1] + 2 / x[-1,0] + 2 / AVG_LEFT!",
            "x[1,-1] x[1,1] + 2 / x[1,0] + 2 / AVG_RIGHT!",
            "AVG_UP@ AVG_DOWN@ - abs DIFF_V!",
            "AVG_LEFT@ AVG_RIGHT@ - abs DIFF_H!",
            "DIFF_V@ DIFF_H@ + mask_max min DIFF_V@ DIFF_H@ max + mask_max min A!",
            "A@ 2 * mask_max min A@ + mask_max min 2 * mask_max min",
        )

        return norm_expr(
            clip,
            [expr, "{multi}"],
            planes,
            func=self.__class__,
            multi=[f"{m} *" if m != 1.0 else "" for m in to_arr(multi)],
            **kwargs,
        )


class Scharr(EdgeMasksEdgeDetect, RidgeDetect, EuclideanDistance, Matrix3x3):
    """
    Original H. Scharr optimised operator which attempts
    to achieve the perfect rotational symmetry with coefficients 3 and 10.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[-3, 0, 3, -10, 0, 10, -3, 0, 3], [-3, -10, -3, 0, 0, 0, 3, 10, 3]]
    divisors: ClassVar[Sequence[float] | None] = [3, 3]


class RScharr(EdgeMasksEdgeDetect, RidgeDetect, EuclideanDistance, Matrix3x3):
    """
    Refined H. Scharr operator to more accurately calculate
    1st derivatives for a 3x3 kernel with coeffs 47 and 162.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [
        [-47, 0, 47, -162, 0, 162, -47, 0, 47],
        [-47, -162, -47, 0, 0, 0, 47, 162, 47],
    ]
    divisors: ClassVar[Sequence[float] | None] = [47, 47]


@deprecated(
    "ScharrTCanny is deprecated and will be removed in a future version. "
    "Please use Scharr and install the 'edgemasks' plugin instead.",
    category=DeprecationWarning,
)
class ScharrTCanny(TCannyEdgeDetect, Matrix3x3):
    """
    H. Scharr optimised TCanny Vapoursynth plugin operator.
    """

    _op = 3
    _scale = 1 / 3


class Kroon(EdgeMasksEdgeDetect, RidgeDetect, EuclideanDistance, Matrix3x3):
    """
    Dirk-Jan Kroon operator.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [
        [-17, 0, 17, -61, 0, 61, -17, 0, 17],
        [-17, -61, -17, 0, 0, 0, 17, 61, 17],
    ]
    divisors: ClassVar[Sequence[float] | None] = [17, 17]


@deprecated(
    "KroonTCanny is deprecated and will be removed in a future version. "
    "Please use Kroon and install the 'edgemasks' plugin instead.",
    category=DeprecationWarning,
)
class KroonTCanny(TCannyEdgeDetect, Matrix3x3):
    """
    Dirk-Jan Kroon TCanny Vapoursynth plugin operator.
    """

    _op = 4
    _scale = 1 / 17


class FreyChen(NormalizeProcessor, MatrixEdgeDetect):
    """
    Chen Frei operator. 3x3 matrices properly implemented.
    """

    sqrt2 = math.sqrt(2)
    matrices: ClassVar[Sequence[Sequence[float]]] = [
        [1, sqrt2, 1, 0, 0, 0, -1, -sqrt2, -1],
        [1, 0, -1, sqrt2, 0, -sqrt2, 1, 0, -1],
        [0, -1, sqrt2, 1, 0, -1, -sqrt2, 1, 0],
        [sqrt2, -1, 0, -1, 0, 1, 0, 1, -sqrt2],
        [0, 1, 0, -1, 0, -1, 0, 1, 0],
        [-1, 0, 1, 0, 0, 0, 1, 0, -1],
        [1, -2, 1, -2, 4, -2, 1, -2, 1],
        [-2, 1, -2, 1, 4, 1, -2, 1, -2],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    divisors: ClassVar[Sequence[float] | None] = [2 * sqrt2, 2 * sqrt2, 2 * sqrt2, 2 * sqrt2, 2, 2, 6, 6, 3]

    def _merge_edge(self, exprs: Sequence[ExprList], clip: vs.VideoNode, **kwargs: Any) -> ConstantFormatVideoNode:
        cmats = interleave_arr(exprs, [f"M{i}!" for i in range(len(exprs))], 1)
        M = "M0@ dup * M1@ dup * + M2@ dup * + M3@ dup * +"  # noqa: N806
        S = f"M4@ dup * M5@ dup * + M6@ dup * + M7@ dup * + M8@ dup * + {M} +"  # noqa: N806
        return norm_expr(clip, [cmats, f"{M} {S} / sqrt"], kwargs.get("planes"), func=self.__class__)


class FreyChenG41(RidgeDetect, EuclideanDistance, Matrix3x3):
    """
    "Chen Frei" operator. 3x3 matrices from G41Fun.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [[-7, 0, 7, -10, 0, 10, -7, 0, 7], [-7, -10, -7, 0, 0, 0, 7, 10, 7]]
    divisors: ClassVar[Sequence[float] | None] = [7, 7]


# Max
class Robinson3(MagnitudeEdgeMasks, Max, Matrix3x3):
    """
    Robinson compass operator level 3.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [
        [1, 1, 1, 0, 0, 0, -1, -1, -1],  # N
        [1, 1, 0, 1, 0, -1, 0, -1, -1],  # NW
        [1, 0, -1, 1, 0, -1, 1, 0, -1],  # W
        [0, -1, -1, 1, 0, -1, 1, 1, 0],  # SW
        [],
        [],
        [],
        [],
    ]


class Robinson5(MagnitudeEdgeMasks, Max, Matrix3x3):
    """
    Robinson compass operator level 5.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [
        [1, 2, 1, 0, 0, 0, -1, -2, -1],  # N
        [2, 1, 0, 1, 0, -1, 0, -1, -2],  # NW
        [1, 0, -1, 2, 0, -2, 1, 0, -1],  # W
        [0, -1, -2, 1, 0, -1, 2, 1, 0],  # SW
        [],
        [],
        [],
        [],
    ]


class TheToof(MagnitudeMatrix, Max, Matrix3x3):
    """
    TheToof compass operator from SharpAAMCmod.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [
        [5, 10, 5, 0, 0, 0, -5, -10, -5],  # N
        [10, 5, 0, 5, 0, -5, 0, -5, -10],  # NW
        [5, 0, -5, 10, 0, -10, 5, 0, -5],  # W
        [0, -5, -10, 5, 0, -5, 10, 5, 0],  # SW
        [],
        [],
        [],
        [],
    ]
    divisors: ClassVar[Sequence[float] | None] = [4] * 4


class Kirsch(MagnitudeEdgeMasks, Max, Matrix3x3):
    """
    Russell Kirsch compass operator.
    """

    matrices: ClassVar[Sequence[Sequence[float]]] = [
        [5, 5, 5, -3, 0, -3, -3, -3, -3],  # N
        [5, 5, -3, 5, 0, -3, -3, -3, -3],  # NW
        [5, -3, -3, 5, 0, -3, 5, -3, -3],  # W
        [-3, -3, -3, 5, 0, -3, 5, 5, -3],  # SW
        [-3, -3, -3, -3, 0, -3, 5, 5, 5],  # S
        [-3, -3, -3, -3, 0, 5, -3, 5, 5],  # SE
        [-3, -3, 5, -3, 0, 5, -3, -3, 5],  # E
        [-3, 5, 5, -3, 0, 5, -3, -3, -3],  # NE
    ]


@deprecated(
    "KirschTCanny is deprecated and will be removed in a future version. "
    "Please use Kirsch and install the 'edgemasks' plugin instead.",
    category=DeprecationWarning,
)
class KirschTCanny(TCannyEdgeDetect, Matrix3x3):
    """
    Russell Kirsch compass TCanny Vapoursynth plugin operator.
    """

    _op = 5


# Misc
class MinMax(EdgeDetect):
    """
    Min/max mask with separate luma/chroma radii.
    """

    rady: int
    radc: int

    def __init__(self, rady: int = 2, radc: int = 0, **kwargs: Any) -> None:
        self.rady = rady
        self.radc = radc
        super().__init__(**kwargs)

    def _compute_edge_mask(
        self,
        clip: ConstantFormatVideoNode,
        *,
        multi: float | Sequence[float] = 1.0,
        planes: Planes = None,
        **kwargs: Any,
    ) -> ConstantFormatVideoNode:
        return join(
            [
                ExprOp.SUB.combine(
                    Morpho.expand(p, rad, rad, XxpandMode.ELLIPSE, **kwargs),
                    Morpho.inpand(p, rad, rad, XxpandMode.ELLIPSE, **kwargs),
                    expr_suffix=[f"{m} *" if m != 1.0 else "" for m in to_arr(multi)],
                    planes=planes,
                    func=self.__class__,
                )
                if rad > 0
                else p
                for p, rad in zip(split(clip), (self.rady, self.radc, self.radc)[: clip.format.num_planes])
            ],
            clip.format.color_family,
        )
