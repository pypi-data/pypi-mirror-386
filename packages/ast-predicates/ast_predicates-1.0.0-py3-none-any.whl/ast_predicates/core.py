# Core matching functions
from __future__ import annotations

import ast
from typing import Any

from .matchers import Matcher, MatchIfTrue, MissingSentinel, SequenceMatcher


def matches(node: ast.AST, pattern: Matcher | type[ast.AST] | list[Matcher | type[ast.AST]] | str | int) -> bool:
    """
    Check if an AST node matches the given pattern.

    Args:
        node: The AST node to check
        pattern: A Matcher instance, AST node type, or literal value

    Returns:
        True if the node matches the pattern, False otherwise

    Example:
        tree = ast.parse("foo.bar()")
        if matches(tree.body[0].value, Call(func=Attribute(attr="bar"))):
            print("Found method call!")
    """
    return _matches(node, pattern)


def _matches(node: Any, pattern: Matcher | type[ast.AST] | list[Matcher | type[ast.AST]] | str | int) -> bool:
    if pattern is MissingSentinel.DEFAULT:
        return True

    if pattern is None:
        return node is None

    if isinstance(pattern, Matcher):
        return pattern.matches(node)

    if isinstance(pattern, type) and issubclass(pattern, ast.AST):
        return isinstance(node, pattern)

    if isinstance(pattern, str | int):
        return node == pattern

    if isinstance(pattern, list):
        if not isinstance(node, list | tuple):
            return False
        # TODO: implement expandable matcher
        matcher = SequenceMatcher(*pattern)
        return matcher.matches(node)

    raise NotImplementedError("AST does not handle the case", node, pattern)


class VisitAll(ast.NodeVisitor):
    def __init__(self, matcher: Matcher) -> None:
        self.nodes: list[ast.AST] = []
        self.matcher = matcher

    def visit(self, node: ast.AST) -> None:
        if self.matcher.matches(node):
            self.nodes.append(node)
        super().visit(node)


def find_all(tree: ast.AST, pattern: Matcher | type[ast.AST]) -> list[ast.AST]:
    """
    Find all nodes in the AST that match the given pattern.

    Args:
        tree: The root AST node to search
        pattern: A Matcher instance or AST node type

    Returns:
        List of all matching AST nodes

    Example:
        tree = ast.parse(source_code)
        calls = find_all(tree, Call(func=Name(id="print")))
    """
    if isinstance(pattern, Matcher):
        matcher = pattern
    elif isinstance(pattern, type) and issubclass(pattern, ast.AST):
        matcher = MatchIfTrue(lambda x: isinstance(x, ast.AST))
    else:
        raise TypeError("Expected matcher or type")
    visitor = VisitAll(matcher)
    visitor.visit(tree)
    return visitor.nodes


def find_first(tree: ast.AST, pattern: Matcher | type[ast.AST]) -> ast.AST | None:
    """
    Find the first node in the AST that matches the given pattern.

    Args:
        tree: The root AST node to search
        pattern: A Matcher instance or AST node type

    Returns:
        The first matching AST node, or None if no match found

    Example:
        tree = ast.parse(source_code)
        first_func = find_first(tree, FunctionDef(name="main"))
    """
    if nodes := find_all(tree, pattern):
        return nodes[0]
    else:
        return None


def extract(node: ast.AST, pattern: Matcher | type[ast.AST], key: str) -> Any | None:
    """
    Match a pattern and extract a specific attribute value.

    Args:
        node: The AST node to match against
        pattern: A Matcher instance or AST node type
        key: The attribute name to extract

    Returns:
        The extracted attribute value, or None if no match

    Example:
        call_node = ast.parse("foo.bar()").body[0].value
        attr = extract(call_node, Call(func=Attribute()), 'func.attr')
        # Returns: 'bar'
    """
    if obj := find_first(node, pattern):
        for part in key.split("."):
            obj = getattr(obj, part, None)
    return obj
