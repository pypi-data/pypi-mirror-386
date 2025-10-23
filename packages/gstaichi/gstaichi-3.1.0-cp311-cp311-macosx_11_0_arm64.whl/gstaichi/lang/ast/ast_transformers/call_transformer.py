# type: ignore

import ast
import dataclasses
import inspect
import math
import operator
import re
import warnings
from ast import unparse
from collections import ChainMap
from typing import Any

import numpy as np

from gstaichi.lang import (
    expr,
    impl,
    matrix,
)
from gstaichi.lang import ops as ti_ops
from gstaichi.lang._dataclass_util import create_flat_name
from gstaichi.lang.ast.ast_transformer_utils import (
    ASTTransformerContext,
    get_decorator,
)
from gstaichi.lang.exception import (
    GsTaichiSyntaxError,
    GsTaichiTypeError,
)
from gstaichi.lang.expr import Expr
from gstaichi.lang.matrix import Matrix, Vector
from gstaichi.lang.util import is_gstaichi_class
from gstaichi.types import primitive_types


class CallTransformer:
    @staticmethod
    def _build_call_if_is_builtin(ctx: ASTTransformerContext, node, args, keywords):
        from gstaichi.lang import matrix_ops  # pylint: disable=C0415

        func = node.func.ptr
        replace_func = {
            id(print): impl.ti_print,
            id(min): ti_ops.min,
            id(max): ti_ops.max,
            id(int): impl.ti_int,
            id(bool): impl.ti_bool,
            id(float): impl.ti_float,
            id(any): matrix_ops.any,
            id(all): matrix_ops.all,
            id(abs): abs,
            id(pow): pow,
            id(operator.matmul): matrix_ops.matmul,
        }

        # Builtin 'len' function on Matrix Expr
        if id(func) == id(len) and len(args) == 1:
            if isinstance(args[0], Expr) and args[0].ptr.is_tensor():
                node.ptr = args[0].get_shape()[0]
                return True

        if id(func) in replace_func:
            node.ptr = replace_func[id(func)](*args, **keywords)
            return True
        return False

    @staticmethod
    def _build_call_if_is_type(ctx: ASTTransformerContext, node, args, keywords):
        func = node.func.ptr
        if id(func) in primitive_types.type_ids:
            if len(args) != 1 or keywords:
                raise GsTaichiSyntaxError("A primitive type can only decorate a single expression.")
            if is_gstaichi_class(args[0]):
                raise GsTaichiSyntaxError("A primitive type cannot decorate an expression with a compound type.")

            if isinstance(args[0], expr.Expr):
                if args[0].ptr.is_tensor():
                    raise GsTaichiSyntaxError("A primitive type cannot decorate an expression with a compound type.")
                node.ptr = ti_ops.cast(args[0], func)
            else:
                node.ptr = expr.Expr(args[0], dtype=func)
            return True
        return False

    @staticmethod
    def _is_external_func(ctx: ASTTransformerContext, func) -> bool:
        if ctx.is_in_static_scope():  # allow external function in static scope
            return False
        if hasattr(func, "_is_gstaichi_function") or hasattr(func, "_is_wrapped_kernel"):  # gstaichi func/kernel
            return False
        if hasattr(func, "__module__") and func.__module__ and func.__module__.startswith("gstaichi."):
            return False
        return True

    @staticmethod
    def _warn_if_is_external_func(ctx: ASTTransformerContext, node):
        func = node.func.ptr
        if not CallTransformer._is_external_func(ctx, func):
            return
        name = unparse(node.func).strip()
        warnings.warn_explicit(
            f"\x1b[38;5;226m"  # Yellow
            f'Calling non-gstaichi function "{name}". '
            f"Scope inside the function is not processed by the GsTaichi AST transformer. "
            f"The function may not work as expected. Proceed with caution! "
            f"Maybe you can consider turning it into a @ti.func?"
            f"\x1b[0m",  # Reset
            SyntaxWarning,
            ctx.file,
            node.lineno + ctx.lineno_offset,
            module="gstaichi",
        )

    @staticmethod
    # Parses a formatted string and extracts format specifiers from it, along with positional and keyword arguments.
    # This function produces a canonicalized formatted string that includes solely empty replacement fields, e.g. 'qwerty {} {} {} {} {}'.
    # Note that the arguments can be used multiple times in the string.
    # e.g.:
    # origin input: 'qwerty {1} {} {1:.3f} {k:.4f} {k:}'.format(1.0, 2.0, k=k)
    # raw_string: 'qwerty {1} {} {1:.3f} {k:.4f} {k:}'
    # raw_args: [1.0, 2.0]
    # raw_keywords: {'k': <ti.Expr>}
    # return value: ['qwerty {} {} {} {} {}', 2.0, 1.0, ['__ti_fmt_value__', 2.0, '.3f'], ['__ti_fmt_value__', <ti.Expr>, '.4f'], <ti.Expr>]
    def _canonicalize_formatted_string(raw_string: str, *raw_args: list, **raw_keywords: dict):
        raw_brackets = re.findall(r"{(.*?)}", raw_string)
        brackets = []
        unnamed = 0
        for bracket in raw_brackets:
            item, spec = bracket.split(":") if ":" in bracket else (bracket, None)
            if item.isdigit():
                item = int(item)
            # handle unnamed positional args
            if item == "":
                item = unnamed
                unnamed += 1
            # handle empty spec
            if spec == "":
                spec = None
            brackets.append((item, spec))

        # check for errors in the arguments
        max_args_index = max([t[0] for t in brackets if isinstance(t[0], int)], default=-1)
        if max_args_index + 1 != len(raw_args):
            raise GsTaichiSyntaxError(
                f"Expected {max_args_index + 1} positional argument(s), but received {len(raw_args)} instead."
            )
        brackets_keywords = [t[0] for t in brackets if isinstance(t[0], str)]
        for item in brackets_keywords:
            if item not in raw_keywords:
                raise GsTaichiSyntaxError(f"Keyword '{item}' not found.")
        for item in raw_keywords:
            if item not in brackets_keywords:
                raise GsTaichiSyntaxError(f"Keyword '{item}' not used.")

        # reorganize the arguments based on their positions, keywords, and format specifiers
        args = []
        for item, spec in brackets:
            new_arg = raw_args[item] if isinstance(item, int) else raw_keywords[item]
            if spec is not None:
                args.append(["__ti_fmt_value__", new_arg, spec])
            else:
                args.append(new_arg)
        # put the formatted string as the first argument to make ti.format() happy
        args.insert(0, re.sub(r"{.*?}", "{}", raw_string))
        return args

    @staticmethod
    def _expand_Call_dataclass_args(args: tuple[ast.stmt, ...]) -> tuple[tuple[ast.stmt, ...], tuple[ast.stmt, ...]]:
        """
        We require that each node has a .ptr attribute added to it, that contains
        the associated Python object
        """
        args_new = []
        added_args = []
        for arg in args:
            val = arg.ptr
            if dataclasses.is_dataclass(val):
                dataclass_type = val
                for field in dataclasses.fields(dataclass_type):
                    try:
                        child_name = create_flat_name(arg.id, field.name)
                    except Exception as e:
                        raise RuntimeError(f"Exception whilst processing {field.name} in {type(dataclass_type)}") from e
                    load_ctx = ast.Load()
                    arg_node = ast.Name(
                        id=child_name,
                        ctx=load_ctx,
                        lineno=arg.lineno,
                        end_lineno=arg.end_lineno,
                        col_offset=arg.col_offset,
                        end_col_offset=arg.end_col_offset,
                    )
                    if dataclasses.is_dataclass(field.type):
                        arg_node.ptr = field.type
                        _added_args, _args_new = CallTransformer._expand_Call_dataclass_args((arg_node,))
                        args_new.extend(_args_new)
                        added_args.extend(_added_args)
                    else:
                        args_new.append(arg_node)
                        added_args.append(arg_node)
            else:
                args_new.append(arg)
        return tuple(added_args), tuple(args_new)

    @staticmethod
    def _expand_Call_dataclass_kwargs(kwargs: list[ast.keyword]) -> tuple[list[ast.keyword], list[ast.keyword]]:
        """
        We require that each node has a .ptr attribute added to it, that contains
        the associated Python object
        """
        kwargs_new = []
        added_kwargs = []
        for i, kwarg in enumerate(kwargs):
            val = kwarg.ptr[kwarg.arg]
            if dataclasses.is_dataclass(val):
                dataclass_type = val
                for field in dataclasses.fields(dataclass_type):
                    src_name = create_flat_name(kwarg.value.id, field.name)
                    child_name = create_flat_name(kwarg.arg, field.name)
                    load_ctx = ast.Load()
                    src_node = ast.Name(
                        id=src_name,
                        ctx=load_ctx,
                        lineno=kwarg.lineno,
                        end_lineno=kwarg.end_lineno,
                        col_offset=kwarg.col_offset,
                        end_col_offset=kwarg.end_col_offset,
                    )
                    kwarg_node = ast.keyword(
                        arg=child_name,
                        value=src_node,
                        ctx=load_ctx,
                        lineno=kwarg.lineno,
                        end_lineno=kwarg.end_lineno,
                        col_offset=kwarg.col_offset,
                        end_col_offset=kwarg.end_col_offset,
                    )
                    if dataclasses.is_dataclass(field.type):
                        kwarg_node.ptr = {child_name: field.type}
                        _added_kwargs, _kwargs_new = CallTransformer._expand_Call_dataclass_kwargs([kwarg_node])
                        kwargs_new.extend(_kwargs_new)
                        added_kwargs.extend(_added_kwargs)
                    else:
                        kwargs_new.append(kwarg_node)
                        added_kwargs.append(kwarg_node)
            else:
                kwargs_new.append(kwarg)
        return added_kwargs, kwargs_new

    @staticmethod
    def build_Call(ctx: ASTTransformerContext, node: ast.Call, build_stmt, build_stmts) -> Any | None:
        """
        example ast:
        Call(func=Name(id='f2', ctx=Load()), args=[Name(id='my_struct_ab', ctx=Load())], keywords=[])
        """
        if get_decorator(ctx, node) in ["static", "static_assert"]:
            with ctx.static_scope_guard():
                build_stmt(ctx, node.func)
                build_stmts(ctx, node.args)
                build_stmts(ctx, node.keywords)
        else:
            build_stmt(ctx, node.func)
            # creates variable for the dataclass itself (as well as other variables,
            # not related to dataclasses). Necessary for calling further child functions
            build_stmts(ctx, node.args)
            build_stmts(ctx, node.keywords)

            added_args, node.args = CallTransformer._expand_Call_dataclass_args(node.args)
            added_keywords, node.keywords = CallTransformer._expand_Call_dataclass_kwargs(node.keywords)

            # create variables for the now-expanded dataclass members
            for arg in added_args:
                assert not hasattr(arg, "ptr")
                build_stmt(ctx, arg)
            for arg in added_keywords:
                assert not hasattr(arg, "ptr")
                build_stmt(ctx, arg)

        # if any arg violates pure, then node also violates pure
        for arg in node.args:
            if arg.violates_pure:
                node.violates_pure_reason = arg.violates_pure_reason
                node.violates_pure = True

        for kw in node.keywords:
            if kw.value.violates_pure:
                node.violates_pure = True
                node.violates_pure_reason = kw.value.violates_pure_reason

        args = []
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                arg_list = arg.ptr
                if isinstance(arg_list, Expr) and arg_list.is_tensor():
                    # Expand Expr with Matrix-type return into list of Exprs
                    arg_list = [Expr(x) for x in ctx.ast_builder.expand_exprs([arg_list.ptr])]

                for i in arg_list:
                    args.append(i)
            else:
                args.append(arg.ptr)
        keywords = dict(ChainMap(*[keyword.ptr for keyword in node.keywords]))
        func = node.func.ptr

        if id(func) in [id(print), id(impl.ti_print)]:
            ctx.func.has_print = True

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value.ptr, str) and node.func.attr == "format":
            raw_string = node.func.value.ptr
            args = CallTransformer._canonicalize_formatted_string(raw_string, *args, **keywords)
            node.ptr = impl.ti_format(*args)
            return node.ptr

        if id(func) == id(Matrix) or id(func) == id(Vector):
            node.ptr = matrix.make_matrix(*args, **keywords)
            return node.ptr

        if CallTransformer._build_call_if_is_builtin(ctx, node, args, keywords):
            return node.ptr

        if CallTransformer._build_call_if_is_type(ctx, node, args, keywords):
            return node.ptr

        if hasattr(node.func, "caller"):
            node.ptr = func(node.func.caller, *args, **keywords)
            return node.ptr

        CallTransformer._warn_if_is_external_func(ctx, node)
        try:
            node.ptr = func(*args, **keywords)
        except TypeError as e:
            module = inspect.getmodule(func)
            error_msg = re.sub(r"\bExpr\b", "GsTaichi Expression", str(e))
            func_name = getattr(func, "__name__", func.__class__.__name__)
            msg = f"TypeError when calling `{func_name}`: {error_msg}."
            if CallTransformer._is_external_func(ctx, node.func.ptr):
                args_has_expr = any([isinstance(arg, Expr) for arg in args])
                if args_has_expr and (module == math or module == np):
                    exec_str = f"from gstaichi import {func.__name__}"
                    try:
                        exec(exec_str, {})
                    except:
                        pass
                    else:
                        msg += f"\nDid you mean to use `ti.{func.__name__}` instead of `{module.__name__}.{func.__name__}`?"
            raise GsTaichiTypeError(msg)

        if getattr(func, "_is_gstaichi_function", False):
            ctx.func.has_print |= func.wrapper.has_print

        return node.ptr
