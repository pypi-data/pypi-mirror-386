from __future__ import annotations

import re
from logging import debug as logging_debug
from math import ceil
from typing import TYPE_CHECKING, Any, Callable, Iterable, Sequence, SupportsIndex, TypeAlias, Union
from warnings import warn

from jetpytools import CustomIndexError, norm_func_name

from vstools import (
    EXPR_VARS,
    ConstantFormatVideoNode,
    CustomRuntimeError,
    FuncExcept,
    HoldsVideoFormat,
    Planes,
    ProcessVariableResClip,
    StrList,
    SupportsString,
    VideoFormatLike,
    VideoNodeIterableT,
    check_variable_format,
    core,
    flatten_vnodes,
    get_video_format,
    normalize_planes,
    normalize_seq,
    to_arr,
    vs,
)

from .error import CustomExprError
from .exprop import ExprList, ExprOp, ExprOpBase, TupleExprList, _TokenDeprecation
from .util import ExprVars

__all__ = ["combine", "combine_expr", "expr_func", "norm_expr"]


def expr_func(
    clips: vs.VideoNode | Sequence[vs.VideoNode],
    expr: str | Sequence[str],
    format: HoldsVideoFormat | VideoFormatLike | None = None,
    opt: bool = False,
    boundary: bool = True,
    func: FuncExcept | None = None,
) -> ConstantFormatVideoNode:
    """
    Calls `akarin.Expr` plugin.

    For a higher-level function, see [norm_expr][vsexprtools.norm_expr]

    Web app to dissect expressions:
        - <https://jaded-encoding-thaumaturgy.github.io/expr101/>

    Args:
        clips: Input clip(s). Supports constant format clips, or one variable resolution clip.
        expr: Expression to be evaluated.
        format: Output format, defaults to the first clip format.
        opt: Forces integer evaluation as much as possible.
        boundary: Specifies the default boundary condition for relative pixel accesses:

               - True (default): Mirrored edges.
               - False: Clamped edges.
        func: Function returned for custom error handling. This should only be set by VS package developers.

    Raises:
        CustomRuntimeError: If `akarin` plugin is not found.
        CustomExprError: If the expression could not be evaluated.

    Returns:
        Evaluated clip.
    """
    func = func or expr_func

    clips = to_arr(clips)

    if TYPE_CHECKING:
        assert check_variable_format(clips, func)

    fmt = get_video_format(format).id if format is not None else None

    logging_debug(f"expr_func ({norm_func_name(func)}): {expr}")

    try:
        return core.akarin.Expr(clips, expr, fmt, opt, boundary)
    except AttributeError as e:
        raise CustomRuntimeError(e)
    except vs.Error as e:
        if len(clips) == 1 and 0 in (clips[0].width, clips[0].height):
            return ProcessVariableResClip[ConstantFormatVideoNode].from_func(
                clips[0], lambda clip: core.akarin.Expr(clip, expr, fmt, opt, boundary)
            )

        raise CustomExprError(e, func, clips, expr, fmt, opt, boundary) from e


def _combine_norm__ix(ffix: SupportsString | Iterable[SupportsString] | None, n_clips: int) -> list[SupportsString]:
    if ffix is None:
        return [""] * n_clips

    ffix = to_arr(ffix)

    return ffix * max(1, ceil(n_clips / len(ffix)))


def combine_expr(
    n: SupportsIndex | Sequence[SupportsString] | HoldsVideoFormat | VideoFormatLike,
    operator: ExprOpBase = ExprOp.MAX,
    suffix: SupportsString | Iterable[SupportsString] | None = None,
    prefix: SupportsString | Iterable[SupportsString] | None = None,
    expr_suffix: SupportsString | Iterable[SupportsString] | None = None,
    expr_prefix: SupportsString | Iterable[SupportsString] | None = None,
) -> ExprList:
    """
    Builds a combine expression using a specified expression operator.

    For combining multiple clips, see [combine][vsexprtools.combine].

    Args:
        n: Object from which to infer the variables.
        operator: An ExprOpBase enum used to join the variables.
        suffix: Optional suffix string(s) to append to each input variable in the expression.
        prefix: Optional prefix string(s) to prepend to each input variable in the expression.
        expr_suffix: Optional expression to append after the combined input expression.
        expr_prefix: Optional expression to prepend before the combined input expression.

    Returns:
        A expression representing the combined result.
    """
    evars = n if isinstance(n, Sequence) else ExprVars(n)
    n = len(evars)

    prefixes, suffixes = (_combine_norm__ix(x, n) for x in (prefix, suffix))

    args = zip(prefixes, evars, suffixes)

    has_op = (n >= operator.n_op) or any(x is not None for x in (suffix, prefix, expr_suffix, expr_prefix))

    operators = operator * max(n - 1, int(has_op))

    return ExprList([to_arr(expr_prefix), args, operators, to_arr(expr_suffix)])


def combine(
    clips: VideoNodeIterableT[vs.VideoNode],
    operator: ExprOpBase = ExprOp.MAX,
    suffix: SupportsString | Iterable[SupportsString] | None = None,
    prefix: SupportsString | Iterable[SupportsString] | None = None,
    expr_suffix: SupportsString | Iterable[SupportsString] | None = None,
    expr_prefix: SupportsString | Iterable[SupportsString] | None = None,
    planes: Planes = None,
    split_planes: bool = False,
    **kwargs: Any,
) -> ConstantFormatVideoNode:
    """
    Combines multiple video clips using a specified expression operator.

    Args:
        clips: Input clip(s).
        operator: An ExprOpBase enum used to join the clips.
        suffix: Optional suffix string(s) to append to each input variable in the expression.
        prefix: Optional prefix string(s) to prepend to each input variable in the expression.
        expr_suffix: Optional expression to append after the combined input expression.
        expr_prefix: Optional expression to prepend before the combined input expression.
        planes: Which planes to process. Defaults to all.
        split_planes: If True, treats each plane of input clips as separate inputs.
        **kwargs: Additional keyword arguments forwarded to [norm_expr][vsexprtools.norm_expr].

    Returns:
        A clip representing the combined result of applying the expression.
    """
    clips = flatten_vnodes(clips, split_planes=split_planes)

    return norm_expr(
        clips, combine_expr(len(clips), operator, suffix, prefix, expr_suffix, expr_prefix), planes, **kwargs
    )


ExprLike: TypeAlias = Union[SupportsString | None, Iterable["ExprLike"]]
"""
A recursive type representing a valid expression input.

Acceptable forms include:
- A single string (or string-like object): Used as the same expression for all planes.
- A list of expressions: Concatenated into a single expression for all planes.
- A tuple of expressions: Interpreted as separate expressions for each plane.
- A TupleExprList: will make a [norm_expr][vsexprtools.norm_expr] call for each expression within this tuple.
"""


def norm_expr(
    clips: VideoNodeIterableT[vs.VideoNode],
    expr: ExprLike,
    planes: Planes = None,
    format: HoldsVideoFormat | VideoFormatLike | None = None,
    opt: bool = False,
    boundary: bool = True,
    func: FuncExcept | None = None,
    split_planes: bool = False,
    debug: bool = False,
    **kwargs: Iterable[SupportsString] | SupportsString,
) -> ConstantFormatVideoNode:
    """
    Evaluate a per-pixel expression on input clip(s), normalize it based on the specified planes,
    and format [tokens][vsexprtools.ExprToken] and placeholders using provided keyword arguments.

    Web app to dissect expressions:
        - <https://jaded-encoding-thaumaturgy.github.io/expr101/>

    Args:
        clips: Input clip(s). Supports constant format clips, or one variable resolution clip.
        expr: Expression to be evaluated.

               - A single str will be processed for all planes.
               - A list will be concatenated to form a single expr for all planes.
               - A tuple of these types will allow specification of different expr for each planes.
               - A TupleExprList will make a `norm_expr` call for each expression within this tuple.
        planes: Plane to process, defaults to all.
        format: Output format, defaults to the first clip format.
        opt: Forces integer evaluation as much as possible.
        boundary: Specifies the default boundary condition for relative pixel accesses:

               - True (default): Mirrored edges.
               - False: Clamped edges.
        func: Function returned for custom error handling. This should only be set by VS package developers.
        split_planes: Splits the VideoNodes into their individual planes.
        debug: Print out the normalized expr.
        **kwargs: Additional keywords arguments to be passed to the expression function. These arguments are key-value
            pairs, where the keys are placeholders that will be replaced in the expression string. Iterable values
            (except str and bytes types) will be associated with the corresponding plane.

    Returns:
        Evaluated clip.
    """
    if isinstance(expr, str):
        nexpr = ([expr],)
    elif isinstance(expr, tuple):
        if isinstance(expr, TupleExprList):
            return expr(
                clips,
                planes=planes,
                format=format,
                opt=opt,
                boundary=boundary,
                func=func,
                split_planes=split_planes,
                **kwargs,
            )
        else:
            nexpr = tuple([to_arr(x) for x in expr])
    else:
        nexpr = (to_arr(expr),)

    clips = flatten_vnodes(clips, split_planes=split_planes)

    normalized_exprs = [StrList(plane_expr).to_str() for plane_expr in nexpr]

    normalized_expr = norm_expr_planes(clips[0], normalized_exprs, planes, **kwargs)

    tokenized_expr = [
        bitdepth_aware_tokenize_expr(clips, e, bool(is_chroma)) for is_chroma, e in enumerate(normalized_expr)
    ]

    if debug:
        print(tokenized_expr)

    return expr_func(clips, tokenized_expr, format, opt, boundary, func)


def extra_op_tokenize_expr(expr: str) -> str:
    # Workaround for the not implemented op
    def _replace_polyval(matched: re.Match[str]) -> str:
        degree = int(matched.group(1))
        return ExprOp.POLYVAL.convert_extra(degree)

    for extra_op in ExprOp._extra_op_names_:
        if extra_op.lower() in expr:
            if extra_op == ExprOp.POLYVAL.name:
                expr = re.sub(rf"\b{extra_op.lower()}(\d+)\b", _replace_polyval, expr)
            else:
                expr = re.sub(rf"\b{extra_op.lower()}\b", getattr(ExprOp, extra_op).convert_extra(), expr)

    return expr


def bitdepth_aware_tokenize_expr(
    clips: Sequence[vs.VideoNode], expr: str, chroma: bool, func: FuncExcept | None = None
) -> str:
    from .exprop import ExprToken

    func = func or bitdepth_aware_tokenize_expr

    expr = extra_op_tokenize_expr(expr)

    if not expr or len(expr) < 4:
        return expr

    replaces = list[tuple[str, Callable[[vs.VideoNode, bool, vs.VideoNode], float]]]()

    for token in sorted(ExprToken, key=lambda x: len(x), reverse=True):
        if token.value in expr:
            replaces.append((token.value, token.get_value))

        if token.name in expr:
            warn(
                f"Using token name '{token.name}' in expressions is deprecated. "
                "Use the token's string representation or its value instead.",
                _TokenDeprecation,
            )
            replaces.append((f"{token.__class__.__name__}.{token.name}", token.get_value))

    if not replaces:
        return expr

    clips = list(clips)
    mapped_clips = list(reversed(list(zip(["", *EXPR_VARS], clips[:1] + clips))))

    for mkey, function in replaces:
        if mkey in expr:
            for key, clip in [(f"{mkey}_{k}" if k else f"{mkey}", clip) for k, clip in mapped_clips]:
                expr = re.sub(rf"\b{key}\b", str(function(clip, chroma, clip)), expr)

        if re.search(rf"\b{mkey}\b", expr):
            raise CustomIndexError("Parsing error or not enough clips passed!", func, reason=expr)

    return expr


def norm_expr_planes(
    clip: vs.VideoNode,
    expr: str | list[str],
    planes: Planes = None,
    **kwargs: Iterable[SupportsString] | SupportsString,
) -> list[str]:
    assert clip.format

    expr_array = normalize_seq(expr, clip.format.num_planes)

    planes = normalize_planes(clip, planes)

    string_args = [(key, normalize_seq(value)) for key, value in kwargs.items()]

    return [
        exp.format(**({"plane_idx": i} | {key: value[i] for key, value in string_args})) if i in planes else ""
        for i, exp in enumerate(expr_array)
    ]
