from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, Literal, Sequence

from jetpytools import FuncExcept

from vsexprtools import norm_expr
from vskernels import Bilinear

if TYPE_CHECKING:
    from vsmasktools import MaskLike

from vstools import (
    ChromaLocation,
    ConstantFormatVideoNode,
    ConvMode,
    FunctionUtil,
    Planes,
    VSFunctionNoArgs,
    VSFunctionPlanesArgs,
    check_ref_clip,
    core,
    get_y,
    join,
    pick_func_stype,
    scale_delta,
    scale_mask,
    vs,
)

from .blur import box_blur, gauss_blur, median_blur
from .enum import BlurMatrix
from .rgtools import repair

__all__ = ["awarpsharp", "fine_sharp", "soothe", "unsharpen"]


def unsharpen(
    clip: vs.VideoNode,
    strength: float = 1.0,
    blur: vs.VideoNode | VSFunctionNoArgs[vs.VideoNode, ConstantFormatVideoNode] = partial(gauss_blur, sigma=1.5),
    planes: Planes = None,
    func: FuncExcept | None = None,
) -> ConstantFormatVideoNode:
    """
    Apply an unsharp mask to a clip.

    This filter sharpens the input by subtracting a blurred version of the clip
    from the original, scaling the difference by the given `strength`, and
    adding it back to the original image. Conceptually:

        result = clip + (clip - blur(clip)) * strength

    Args:
        clip: Input clip.
        strength: Sharpening strength. Defaults to 1.0.
        blur: Either a blurred reference clip or a callable that takes the source clip
            and returns a blurred version (e.g., a Gaussian blur).
        planes: Which planest to process. Default to all.
        func: func: Function returned for custom error handling. This should only be set by VS package developers.

    Returns:
        A sharpened clip.
    """
    func = func or unsharpen

    if callable(blur):
        blur = blur(clip)

    check_ref_clip(clip, blur, func)

    return norm_expr([clip, blur], f"x y - {strength} * x +", planes, func=func)


def awarpsharp(
    clip: vs.VideoNode,
    mask: MaskLike | None = None,
    thresh: int | float = 128,
    blur: int | VSFunctionPlanesArgs[vs.VideoNode, vs.VideoNode] | Literal[False] = 3,
    depth: int | Sequence[int] | None = None,
    chroma: bool = False,
    planes: Planes = None,
    **kwargs: Any,
) -> ConstantFormatVideoNode:
    """
    Sharpens edges by warping them.

    Args:
        clip: Clip to process. Must be either the same size as mask, or four times the size of mask in each dimension.
            The latter can be useful if better subpixel interpolation is desired. If clip is upscaled to four times the
            original size, it must be top-left aligned.
        mask: Edge mask.
        thresh: No pixel in the edge mask will have a value greater than thresh. Decrease for weaker sharpening.
        blur: Specifies the blur applied to the edge mask.
               - If an `int`, it sets the number of passes for the default `box_blur` filter.
               - If a callable, a custom blur function will be used instead.
               - If `False`, no blur will be applied.
        depth: Controls how far to warp. Negative values warp in the other direction, i.e. will blur the image instead
            of sharpening.
        chroma: Controls the chroma handling method. False will use the edge mask from the luma to warp the chroma.
            True will create an edge mask from each chroma channel and use those to warp each chroma channel
            individually.
        planes: Planes to process. Defaults to all.
        **kwargs: Additional arguments forwarded to the [normalize_mask][vsmasktools.normalize_mask] function.

    Returns:
        Warp-sharpened clip.
    """
    from vsmasktools import Sobel, normalize_mask

    func = FunctionUtil(clip, awarpsharp, planes)

    thresh = scale_mask(thresh, 8, func.work_clip)
    chroma = True if func.work_clip.format.color_family is vs.RGB else chroma
    mask_planes = planes if chroma else 0

    if mask is None:
        mask = Sobel

    kwargs = {"clamp": (0, thresh)} | kwargs

    mask = normalize_mask(mask, func.work_clip, func.work_clip, func=func.func, planes=mask_planes, **kwargs)

    if blur is not False:
        blur_fn = partial(box_blur, radius=2, passes=blur, planes=planes) if isinstance(blur, int) else blur
        mask = blur_fn(mask, planes=mask_planes)

    if not chroma:
        loc = ChromaLocation.from_video(func.work_clip)

        mask = get_y(mask)
        mask = join(mask, mask, mask)
        mask = Bilinear().resample(mask, func.work_clip.format.id, chromaloc=loc)

    warp = pick_func_stype(func.work_clip, core.lazy.warp.AWarp, core.lazy.warpsf.AWarp)(
        func.work_clip, mask, depth, 1, planes
    )

    return func.return_clip(warp)


def fine_sharp(
    clip: vs.VideoNode,
    mode: int = 0,
    sstr: float = 2.0,
    cstr: float | None = None,
    xstr: float = 0.19,
    lstr: float = 1.49,
    pstr: float = 1.272,
    ldmp: float | None = None,
    hdmp: float = 0.01,
    planes: Planes = 0,
) -> ConstantFormatVideoNode:
    func = FunctionUtil(clip, fine_sharp, planes)

    if cstr is None:
        from numpy import asarray
        from scipy import interpolate

        cs = interpolate.CubicSpline(
            (0, 0.5, 1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 8.0, 255.0), (0, 0.1, 0.6, 0.9, 1.0, 1.09, 1.15, 1.19, 1.249, 1.5)
        )
        cstr = float(cs(asarray(sstr)))

    if ldmp is None:
        ldmp = sstr + 0.1

    if mode == 0:
        blurred = median_blur(BlurMatrix.BINOMIAL()(func.work_clip, planes), planes=planes)
    elif mode == 1:
        blurred = BlurMatrix.BINOMIAL()(median_blur(func.work_clip, planes=planes), planes)
    else:
        raise NotImplementedError

    sharp = func.work_clip

    if sstr:
        sharp = norm_expr(
            [func.work_clip, blurred],
            "x y = x dup x y - range_size 256 / / dup dup dup abs {lstr} / {pstr} pow "
            "swap3 abs {hdmp} + / swap dup * dup {ldmp} + / * * {sstr} * + ?",
            planes,
            lstr=lstr,
            pstr=1 / pstr,
            sstr=scale_delta(sstr, 8, clip),
            ldmp=ldmp,
            hdmp=hdmp,
            func=func.func,
        )

    if cstr:
        diff = norm_expr([func.work_clip, sharp], "x y - {cstr} * neutral +", planes, cstr=cstr, func=func.func)
        sharp = sharp.std.MergeDiff(BlurMatrix.BINOMIAL()(diff, planes))

    if xstr:
        xysharp = norm_expr([sharp, box_blur(sharp, planes=planes)], "x x y - 9.9 * +", planes, func=func.func)
        rpsharp = repair(xysharp, sharp, 12, planes)
        sharp = sharp.std.Merge(rpsharp, func.norm_seq(xstr, 0))

    return func.return_clip(sharp)


def soothe(
    flt: vs.VideoNode,
    src: vs.VideoNode,
    spatial_strength: float = 0.0,
    temporal_strength: float = 0.75,
    spatial_radius: int = 1,
    temporal_radius: int = 1,
    scenechange: bool = False,
    planes: Planes = None,
) -> ConstantFormatVideoNode:
    sharp_diff = src.std.MakeDiff(flt, planes)

    expr = (
        "x neutral - X! y neutral - Y! X@ Y@ xor X@ {strength} * neutral + X@ abs Y@ abs > x y - {strength} * y + x ? ?"
    )

    if spatial_strength:
        blurred = box_blur(sharp_diff, spatial_radius, planes=planes)
        sharp_diff = norm_expr([sharp_diff, blurred], expr, strength=1.0 - spatial_strength, planes=planes, func=soothe)

    if temporal_strength:
        blurred = box_blur(sharp_diff, temporal_radius, 1, ConvMode.TEMPORAL, planes, scenechange=scenechange)
        sharp_diff = norm_expr(
            [sharp_diff, blurred], expr, strength=1.0 - temporal_strength, planes=planes, func=soothe
        )

    return src.std.MakeDiff(sharp_diff, planes)
