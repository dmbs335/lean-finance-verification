from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .errors import ValidationError


@dataclass(frozen=True)
class EvalContext:
    state: Mapping[str, bool]


def validate_expr(expr: Any, variables: set[str], path: str = "$expr") -> None:
    if isinstance(expr, bool):
        return
    if not isinstance(expr, dict) or len(expr) != 1:
        raise ValidationError(f"{path}: expected a boolean or one-operation object")
    op, argument = next(iter(expr.items()))
    if op == "var":
        if not isinstance(argument, str) or argument not in variables:
            raise ValidationError(f"{path}.var: unknown boolean variable {argument!r}")
        return
    if op == "not":
        validate_expr(argument, variables, f"{path}.not")
        return
    if op in {"all", "any"}:
        if not isinstance(argument, list) or not argument:
            raise ValidationError(f"{path}.{op}: expected a non-empty array")
        for index, item in enumerate(argument):
            validate_expr(item, variables, f"{path}.{op}[{index}]")
        return
    if op in {"eq", "ne"}:
        if not isinstance(argument, list) or len(argument) != 2:
            raise ValidationError(f"{path}.{op}: expected exactly two operands")
        validate_expr(argument[0], variables, f"{path}.{op}[0]")
        validate_expr(argument[1], variables, f"{path}.{op}[1]")
        return
    if op == "if":
        if not isinstance(argument, dict):
            raise ValidationError(f"{path}.if: expected an object")
        expected = {"condition", "then", "else"}
        if set(argument) != expected:
            raise ValidationError(
                f"{path}.if: fields must be exactly {sorted(expected)}"
            )
        validate_expr(argument["condition"], variables, f"{path}.if.condition")
        validate_expr(argument["then"], variables, f"{path}.if.then")
        validate_expr(argument["else"], variables, f"{path}.if.else")
        return
    raise ValidationError(f"{path}: unsupported expression operator {op!r}")


def eval_expr(expr: Any, context: EvalContext) -> bool:
    if isinstance(expr, bool):
        return expr
    op, argument = next(iter(expr.items()))
    if op == "var":
        return bool(context.state[argument])
    if op == "not":
        return not eval_expr(argument, context)
    if op == "all":
        return all(eval_expr(item, context) for item in argument)
    if op == "any":
        return any(eval_expr(item, context) for item in argument)
    if op == "eq":
        return eval_expr(argument[0], context) == eval_expr(argument[1], context)
    if op == "ne":
        return eval_expr(argument[0], context) != eval_expr(argument[1], context)
    if op == "if":
        branch = "then" if eval_expr(argument["condition"], context) else "else"
        return eval_expr(argument[branch], context)
    raise AssertionError(f"validated expression contains unknown operator {op!r}")


def lean_expr(expr: Any, state_name: str = "state") -> str:
    if isinstance(expr, bool):
        return "true" if expr else "false"
    op, argument = next(iter(expr.items()))
    if op == "var":
        return f"{state_name}.{argument}"
    if op == "not":
        return f"!({lean_expr(argument, state_name)})"
    if op == "all":
        return "(" + " && ".join(lean_expr(item, state_name) for item in argument) + ")"
    if op == "any":
        return "(" + " || ".join(lean_expr(item, state_name) for item in argument) + ")"
    if op == "eq":
        return (
            f"(({lean_expr(argument[0], state_name)}) == "
            f"({lean_expr(argument[1], state_name)}))"
        )
    if op == "ne":
        return (
            f"!((({lean_expr(argument[0], state_name)}) == "
            f"({lean_expr(argument[1], state_name)})))"
        )
    if op == "if":
        return (
            f"(if {lean_expr(argument['condition'], state_name)} then "
            f"{lean_expr(argument['then'], state_name)} else "
            f"{lean_expr(argument['else'], state_name)})"
        )
    raise AssertionError(f"validated expression contains unknown operator {op!r}")
