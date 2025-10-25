"""Matcher for ast Nodes.

see nodes at https://docs.python.org/3/library/ast.html
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from types import EllipsisType
from typing import Any, Literal

from .core import matches
from .matchers import AllOf, AtLeastN, AtMostN, DoNotCare, Matcher, MatchIfTrue, Missing, OneOf
from .types import T as T

type Single[N] = N | DoNotCare | OneOf[N] | AllOf[N] | MatchIfTrue[N]
type Many[N] = (
    list[Single[N] | AtLeastN[Single[N] | None] | AtMostN[Single[N] | None]]
    | AtLeastN[Single[N] | None]
    | AtMostN[Single[N] | None]
)


@dataclass
class NodeMatcher[T](Matcher):
    """
    Base class for matchers that match specific AST node types.

    Supports matching node attributes with specific values or nested matchers.
    """

    def matches(self, node: Any) -> bool:
        """Check if node matches this pattern."""
        return self.matches_type(node) and self.matches_attributes(node)

    def matches_type(self, node: Any) -> bool:
        return isinstance(node, self._node_type)  # type: ignore

    def matches_attributes(self, node: Any) -> bool:
        for attr, pattern in self.attributes:
            value = getattr(node, attr)
            result = matches(value, pattern)
            if result is False:
                return False
        return True

    def __init_subclass__(cls, node: type[T]) -> None:
        cls._node_type = node  # type: ignore
        super().__init_subclass__()

    @property
    def attributes(self) -> Iterator[tuple[str, Any]]:
        for field in self.__dataclass_fields__.keys():
            value = getattr(self, field)
            yield field, value


type RootNode = Module | Expression | Interactive
type ExpressionNode = (
    Expr
    | UnaryOp
    | UAdd
    | USub
    | Not
    | Invert
    | BinOp
    | Add
    | Sub
    | Mult
    | Div
    | FloorDiv
    | Mod
    | Pow
    | LShift
    | RShift
    | BitOr
    | BitXor
    | BitAnd
    | MatMult
    | BoolOp
    | And
    | Or
    | Compare
    | Eq
    | NotEq
    | Lt
    | LtE
    | Gt
    | GtE
    | Is
    | IsNot
    | In
    | NotIn
    | Call
    | IfExp
    | Attribute
    | NamedExpr
    | SubscriptingNode
    | ComprehensionNode
)
type SubscriptingNode = Subscript | Slice
type ComprehensionNode = ListComp | SetComp | GeneratorExp | DictComp

type Statement = Assign | AnnAssign | AugAssign | Raise | Assert | Delete | Pass
type ImportNode = Import | ImportFrom
type ControlFlow = (
    If | For | While | Break | Continue | Try | TryStar | ExceptHandler | With | Await | AsyncFor | AsyncWith
)
type PatternMatching = Match
type Def = FunctionDef | Lambda | ClassDef | Return | Yield | YieldFrom | Global | Nonlocal | AsyncFunctionDef


@dataclass
class Module(NodeMatcher, node=ast.Module):
    """Matcher for module definitions."""

    body: Many[Statement] = Missing
    "a list of the module’s Statements"


@dataclass
class Expression(NodeMatcher, node=ast.Module):
    """Matcher for expression definitions."""

    body: Single[ExpressionNode] = Missing
    """a single node, one of the expression types"""


@dataclass
class Interactive(NodeMatcher, node=ast.Module):
    """Matcher for interactive definitions."""

    body: Many[Statement] = Missing
    "a list of the module’s Statements"


@dataclass
class FunctionDef(NodeMatcher, node=ast.FunctionDef):
    """Matcher for function definitions."""

    name: Single[str] = Missing
    "raw string of the function name"

    args: Single[Arguments] = Missing
    body: Many[Matcher] = Missing
    decorator_list: Many[Matcher] = Missing
    returns: Many[Matcher] = Missing


class Arguments(NodeMatcher, node=ast.arguments):
    posonlyargs: Many[Argument] = Missing
    args: Many[Argument] = Missing
    kwonlyargs: Many[Argument] = Missing
    vararg: Single[Argument] = Missing
    kwarg: Single[Argument] = Missing
    kw_defaults: Many[Matcher] = Missing
    defaults: Many[Matcher] = Missing


@dataclass
class AsyncFunctionDef(NodeMatcher, node=ast.AsyncFunctionDef):
    """Matcher for async function definitions."""

    name: Single[str] = Missing
    "raw string of the function name"

    args: Single[Arguments] = Missing
    body: Many[Matcher] = Missing
    decorator_list: Many[Matcher] = Missing
    returns: Many[Matcher] = Missing


@dataclass
class ClassDef(NodeMatcher, node=ast.ClassDef):
    """Matcher for class definitions."""

    name: Single[str] = Missing
    "raw string for the class name"

    bases: Many[Name] = Missing

    keywords: Many[Keyword] = Missing
    body: Many[Matcher] = Missing

    decorator_list: Many[Name] = Missing
    type_params: Any = Missing


@dataclass
class Return(NodeMatcher, node=ast.Return):
    """Matcher for return statements."""

    value: Single[Matcher] = Missing
    "returned value"


@dataclass
class Delete(NodeMatcher, node=ast.Delete):
    """Matcher for delete statements."""

    targets: Many[Name | Attribute | Subscript] = Missing
    "list of nodes, such as Name, Attribute or Subscript nodes"


@dataclass
class Assign(NodeMatcher, node=ast.Assign):
    """Matcher for assignment statements."""

    targets: Many[Name | Attribute | Subscript] = Missing
    "list of nodes, such as Name, Attribute or Subscript nodes"

    value: Single[Matcher] = Missing
    "value is a single node"


@dataclass
class AugAssign(NodeMatcher, node=ast.AugAssign):
    """Matcher for augmented assignment (+=, -=, etc.)."""

    target: Single[Name | Attribute | Subscript] = Missing
    "list of nodes, such as Name, Attribute or Subscript nodes"

    op: Single[Matcher] = Missing
    value: Single[Matcher] = Missing
    "value is a single node"


@dataclass
class AnnAssign(NodeMatcher, node=ast.AnnAssign):
    """Matcher for annotated assignments."""

    target: Single[Name | Attribute | Subscript] = Missing
    "list of nodes, such as Name, Attribute or Subscript nodes"

    value: Single[Matcher] = Missing
    "value is a single node"


@dataclass
class For(NodeMatcher, node=ast.For):
    """Matcher for for loops."""

    target: Single[Name | Tuple | List | Attribute | Subscript] = Missing
    iter: Single[Matcher] = Missing
    body: Many[Matcher] = Missing
    orelse: Many[Matcher] = Missing


@dataclass
class AsyncFor(NodeMatcher, node=ast.AsyncFor):
    """Matcher for async for loops."""

    target: Single[Name | Tuple | List | Attribute | Subscript] = Missing
    iter: Single[Matcher] = Missing
    body: Many[Matcher] = Missing
    orelse: Many[Matcher] = Missing


@dataclass
class While(NodeMatcher, node=ast.While):
    """Matcher for while loops."""

    test: Single[Matcher] = Missing
    body: Many[Matcher] = Missing
    orelse: Many[Matcher] = Missing


@dataclass
class If(NodeMatcher, node=ast.If):
    """Matcher for if statements."""

    test: Single[Matcher] = Missing
    body: Many[Matcher] = Missing
    orelse: Many[Matcher] = Missing


@dataclass
class With(NodeMatcher, node=ast.With):
    """Matcher for with statements."""

    items: Many[WithItem] = Missing
    body: Many[Matcher] = Missing


@dataclass
class WithItem(NodeMatcher, node=ast.withitem):
    """Matcher for a single context manager in a with block."""

    context_expr: Single[Matcher] = Missing
    optional_vars: Single[Matcher] | None = Missing


@dataclass
class AsyncWith(NodeMatcher, node=ast.AsyncWith):
    """Matcher for async with statements."""

    context_expr: Single[Matcher] = Missing
    optional_vars: Single[Matcher] | None = Missing


class Match(NodeMatcher, node=ast.Match):
    """"""


@dataclass
class Raise(NodeMatcher, node=ast.Raise):
    """Matcher for raise statements."""

    exc: Single[Matcher] = Missing
    cause: Single[Matcher] = Missing


@dataclass
class Try(NodeMatcher, node=ast.Try):
    """Matcher for try/except blocks."""

    body: Many[Matcher] = Missing
    handlers: Many[ExceptHandler] = Missing
    orelse: Many[Matcher] = Missing
    finalbody: Many[Matcher] = Missing


@dataclass
class TryStar(NodeMatcher, node=ast.TryStar):
    """Matcher for try/except* blocks."""

    body: Many[Matcher] = Missing
    handlers: Many[ExceptHandler] = Missing
    orelse: Many[Matcher] = Missing
    finalbody: Many[Matcher] = Missing


class ExceptHandler(NodeMatcher, node=ast.ExceptHandler):
    """Matcher a single except clause."""

    type: Single[Matcher] = Missing
    name: Single[Matcher] | None = Missing
    body: Many[Matcher] = Missing


@dataclass
class Assert(NodeMatcher, node=ast.Assert):
    """Matcher for assert statements."""

    test: Single[Matcher] = Missing
    msg: Single[Matcher] | None = Missing


@dataclass
class Import(NodeMatcher, node=ast.Import):
    """Matcher for import statements."""

    names: Many[Alias] = Missing
    "list of alias nodes"


@dataclass
class Alias(NodeMatcher, node=ast.alias):
    """Matcher for alias in import statements."""

    name: Single[str] = Missing
    asname: Single[str] | None = Missing


@dataclass
class ImportFrom(NodeMatcher, node=ast.ImportFrom):
    """Matcher for `from x import y` statements."""

    module: Single[str] = Missing
    "raw string of the `from` name, without any leading dots, or None for statements such as `from . import foo`"

    names: Many[Alias] = Missing
    "list of alias nodes"

    level: Single[int] = Missing
    "integer holding the level of the relative import (0 means absolute import)"


@dataclass
class Global(NodeMatcher, node=ast.Global):
    """Matcher for global declarations."""

    names: Many[Name] = Missing


@dataclass
class Nonlocal(NodeMatcher, node=ast.Nonlocal):
    """Matcher for nonlocal declarations."""

    names: Many[Name] = Missing


@dataclass
class Expr(NodeMatcher, node=ast.Expr):
    """Matcher for expression statements."""

    value: Single[Matcher] = Missing


@dataclass
class Pass(NodeMatcher, node=ast.Pass):
    """Matcher for raise NotImplementedError statements."""

    value: Single[Matcher] = Missing


@dataclass
class Break(NodeMatcher, node=ast.Break):
    """Matcher for break statements."""


@dataclass
class Continue(NodeMatcher, node=ast.Continue):
    """Matcher for continue statements."""


@dataclass
class BoolOp(NodeMatcher, node=ast.BoolOp):
    """Matcher for boolean operations (and, or)."""

    op: Single[Matcher] = Missing
    values: Many[Matcher] = Missing


@dataclass
class BinOp(NodeMatcher, node=ast.BinOp):
    """Matcher for binary operations (+, -, *, /, etc.)."""

    op: Single[Matcher] = Missing
    values: Many[Matcher] = Missing


@dataclass
class UnaryOp(NodeMatcher, node=ast.UnaryOp):
    """Matcher for unary operations (not, -, +, ~)."""

    op: Single[Matcher] = Missing
    operand: Single[Matcher] = Missing


@dataclass
class Lambda(NodeMatcher, node=ast.Lambda):
    """Matcher for lambda expressions."""

    args: Arguments = Missing
    body: Single[Matcher] = Missing


@dataclass
class IfExp(NodeMatcher, node=ast.IfExp):
    """Matcher for ternary if expressions."""

    test: Single[Matcher] = Missing
    body: Single[Matcher] = Missing
    orelse: Single[Matcher] = Missing


@dataclass
class Dict(NodeMatcher, node=ast.Dict):
    """Matcher for dictionary literals."""

    keys: Many[Matcher] = Missing
    values: Many[Matcher] = Missing


@dataclass
class Set(NodeMatcher, node=ast.Set):
    """Matcher for set literals."""

    elts: Many[Matcher] = Missing


@dataclass
class ListComp(NodeMatcher, node=ast.ListComp):
    """Matcher for list comprehensions."""

    elt: Single[Matcher] = Missing
    generators: Many[Comprehension] = Missing


@dataclass
class Comprehension(NodeMatcher, node=ast.comprehension):
    """Matcher for set literals."""

    target: Name | Tuple = Missing
    iter: Single[Matcher] = Missing
    ifs: Many[Matcher] = Missing
    is_async: Single[bool] = Missing


@dataclass
class SetComp(NodeMatcher, node=ast.SetComp):
    """Matcher for set comprehensions."""

    elt: Single[Matcher] = Missing
    generators: Many[Comprehension] = Missing


@dataclass
class DictComp(NodeMatcher, node=ast.DictComp):
    """Matcher for dictionary comprehensions."""

    key: Single[Matcher] = Missing
    value: Single[Matcher] = Missing
    generators: Many[Comprehension] = Missing


@dataclass
class GeneratorExp(NodeMatcher, node=ast.GeneratorExp):
    """Matcher for generator expressions."""

    elt: Single[Matcher] = Missing
    generators: Many[Comprehension] = Missing


@dataclass
class Await(NodeMatcher, node=ast.Await):
    """Matcher for await expressions."""

    value: Single[Matcher] = Missing


@dataclass
class Yield(NodeMatcher, node=ast.Yield):
    """Matcher for yield expressions."""

    value: Single[Matcher] = Missing


@dataclass
class YieldFrom(NodeMatcher, node=ast.YieldFrom):
    """Matcher for yield from expressions."""

    value: Single[Matcher] = Missing


@dataclass
class Compare(NodeMatcher, node=ast.Compare):
    """Matcher for comparison operations."""

    left: Single[Matcher] = Missing
    ops: Many[Matcher] = Missing
    comparators: Many[Matcher] = Missing


@dataclass
class Call(NodeMatcher, node=ast.Call):
    """Matcher for function/method calls."""

    func: Single[Name | Attribute] = Missing
    "func is the function, which will often be a Name or Attribute object"

    args: Many[Argument] = Missing
    "holds a list of the arguments passed by position."

    keywords: Many[Keyword] = Missing
    "holds a list of keyword objects representing arguments passed by keyword."


type Argument = Name | Starred | Constant | Matcher


@dataclass
class Keyword(NodeMatcher, node=ast.keyword):
    arg: Single[str] = Missing
    "raw string of the parameter name."

    value: Single[Matcher] = Missing
    "node to pass in."


@dataclass
class FormattedValue(NodeMatcher, node=ast.FormattedValue):
    """Matcher for f-string formatted values."""

    value: Single[Matcher] = Missing
    conversion: Single[Literal[-1, 97, 114, 115]] = Missing
    format_spec: Single[JoinedStr] = Missing


@dataclass
class JoinedStr(NodeMatcher, node=ast.JoinedStr):
    """Matcher for f-strings."""

    values: Many[Matcher] = Missing


@dataclass
class Constant(NodeMatcher, node=ast.Constant):
    """Matcher for constant values."""

    value: Single[str | bytes | int | float | complex | bool | EllipsisType | None] = Missing
    """
    value attribute of the Constant literal contains the Python object it represents. The values represented can be instances of str, bytes, int, float, complex, and bool, and the constants None and Ellipsis
    """


@dataclass
class Integer(NodeMatcher, node=ast.Constant):
    """Matcher for integer constant values."""

    def matches(self, node: Any) -> bool:
        return super().matches(node) and isinstance(node.value, int)


@dataclass
class String(NodeMatcher, node=ast.Constant):
    """Matcher for string constant values."""

    def matches(self, node: Any) -> bool:
        return super().matches(node) and isinstance(node.value, str)


@dataclass
class Attribute(NodeMatcher, node=ast.Attribute):
    """Matcher for attribute access."""

    value: Single[Name | Matcher] = Missing
    "a node, typically a Name"

    attr: Single[str] = Missing
    "a bare string giving the name of the attribute"


@dataclass
class NamedExpr(NodeMatcher, node=ast.NamedExpr):
    """Matcher for attribute access."""

    target: Single[Name | Matcher] = Missing
    value: Single[Name | Matcher] = Missing


@dataclass
class Subscript(NodeMatcher, node=ast.Subscript):
    """Matcher for subscript operations (indexing)."""

    value: Single[Matcher] = Missing
    slice: Single[Matcher] = Missing


@dataclass
class Starred(NodeMatcher, node=ast.Starred):
    """Matcher for starred expressions (*args)."""

    value: Single[Matcher] = Missing


@dataclass
class Name(NodeMatcher, node=ast.Name):
    """Matcher for variable names."""

    id: Single[str] = Missing
    """holds the name as a string"""


@dataclass
class List(NodeMatcher, node=ast.List):
    """Matcher for list literals."""

    elts: Many[Matcher] = Missing


@dataclass
class Tuple(NodeMatcher, node=ast.Tuple):
    """Matcher for tuple literals."""

    elts: Many[Matcher] = Missing


@dataclass
class Slice(NodeMatcher, node=ast.Slice):
    """Matcher for slice objects."""

    lower: Single[Matcher] = Missing
    upper: Single[Matcher] = Missing
    step: Single[Matcher] = Missing


@dataclass
class Add(NodeMatcher, node=ast.Add):
    """Matcher for addition operator."""


@dataclass
class Sub(NodeMatcher, node=ast.Sub):
    """Matcher for subtraction operator."""


@dataclass
class Mult(NodeMatcher, node=ast.Mult):
    """Matcher for multiplication operator."""


@dataclass
class Div(NodeMatcher, node=ast.Div):
    """Matcher for division operator."""


@dataclass
class FloorDiv(NodeMatcher, node=ast.FloorDiv):
    """Matcher for floor division operator."""


@dataclass
class Mod(NodeMatcher, node=ast.Mod):
    """Matcher for modulo operator."""


@dataclass
class Pow(NodeMatcher, node=ast.Pow):
    """Matcher for power operator."""


@dataclass
class LShift(NodeMatcher, node=ast.LShift):
    """Matcher for left shift operator."""


@dataclass
class RShift(NodeMatcher, node=ast.RShift):
    """Matcher for right shift operator."""


@dataclass
class BitOr(NodeMatcher, node=ast.BitOr):
    """Matcher for bitwise OR operator."""


@dataclass
class BitXor(NodeMatcher, node=ast.BitXor):
    """Matcher for bitwise XOR operator."""


@dataclass
class BitAnd(NodeMatcher, node=ast.BitAnd):
    """Matcher for bitwise AND operator."""


@dataclass
class MatMult(NodeMatcher, node=ast.MatMult):
    """Matcher for matrix multiplication operator."""


@dataclass
class And(NodeMatcher, node=ast.And):
    """Matcher for logical AND operator."""


@dataclass
class Or(NodeMatcher, node=ast.Or):
    """Matcher for logical OR operator."""


@dataclass
class Not(NodeMatcher, node=ast.Not):
    """Matcher for logical NOT operator."""


@dataclass
class Invert(NodeMatcher, node=ast.Invert):
    """Matcher for bitwise NOT operator."""


@dataclass
class UAdd(NodeMatcher, node=ast.UAdd):
    """Matcher for unary plus operator."""


@dataclass
class USub(NodeMatcher, node=ast.USub):
    """Matcher for unary minus operator."""


@dataclass
class Eq(NodeMatcher, node=ast.Eq):
    """Matcher for equality comparison."""


@dataclass
class NotEq(NodeMatcher, node=ast.NotEq):
    """Matcher for inequality comparison."""


@dataclass
class Lt(NodeMatcher, node=ast.Lt):
    """Matcher for less than comparison."""


@dataclass
class LtE(NodeMatcher, node=ast.LtE):
    """Matcher for less than or equal comparison."""


@dataclass
class Gt(NodeMatcher, node=ast.Gt):
    """Matcher for greater than comparison."""


@dataclass
class GtE(NodeMatcher, node=ast.GtE):
    """Matcher for greater than or equal comparison."""


@dataclass
class Is(NodeMatcher, node=ast.Is):
    """Matcher for identity comparison."""


@dataclass
class IsNot(NodeMatcher, node=ast.IsNot):
    """Matcher for negative identity comparison."""


@dataclass
class In(NodeMatcher, node=ast.In):
    """Matcher for membership test."""


@dataclass
class NotIn(NodeMatcher, node=ast.NotIn):
    """Matcher for negative membership test."""
