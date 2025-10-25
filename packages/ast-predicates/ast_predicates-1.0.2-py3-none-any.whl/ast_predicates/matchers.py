from __future__ import annotations

import ast
import enum
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast

from .types import T as T


class Matcher(ABC):
    @abstractmethod
    def matches(self, node: Any) -> bool:
        """
        Check if the given AST node matches this pattern.

        Args:
            node: The AST node to check

        Returns:
            True if the node matches, False otherwise
        """

    def __or__(self, other: Matcher) -> OneOf:
        return OneOf(self, other)

    def __and__(self, other: Matcher) -> AllOf:
        return AllOf(self, other)


type SpecialMatcher[M] = DoNotCare | MatchIfTrue[M] | OneOf[M] | AllOf[M] | AtLeastN[M] | AtMostN[M]


class MissingSentinel(enum.Enum):
    DEFAULT = enum.auto()


Missing: Any = MissingSentinel.DEFAULT


class Predicate(Protocol):
    def __call__(self, obj: Any) -> bool: ...


@dataclass
class DoNotCare(Matcher):
    """
    Matcher that matches any value (wildcard).

    Example:

        Call(func=Name(id=DoNotCare()))  # Matches calls to any function name
    """

    def matches(self, node: ast.AST) -> bool:
        return True


@dataclass
class MatchIfTrue[M](Matcher):
    """
    Matcher that accepts a callable predicate function.

    Example:

        Name(id=MatchIfTrue(lambda x: x.startswith('test_')))
    """

    predicate: Predicate
    """
    Callable that takes a value and returns bool
    """

    def matches(self, node: ast.AST) -> bool:
        return self.predicate(node)


@dataclass
class OneOf[M](Matcher):
    """
    Matcher that matches any one of its options.
    Useful when you want to match against one of several options for a single node.
    You can also construct a OneOf matcher by using Python's bitwise or operator with concrete matcher classes.

    Example:

        BinOp(op=OneOf(Add(), Sub(), Mult()))
    """

    matchers: Sequence[Matcher]

    def __init__(self, *matchers: Matcher) -> None:
        """
        Initialize with multiple matcher options.

        Args:
            *matchers: Variable number of matchers to try
        """
        self.matchers = matchers

    def matches(self, node: ast.AST) -> bool:
        return any(matcher.matches(node) for matcher in self.matchers)


@dataclass
class AllOf[M](Matcher):
    """
    Matcher that succeeds only if all provided matchers match.

    Useful when you want to match against a concrete matcher and
    a MatchIfTrue at the same time.

    Example:

        AllOf(Call(func=Name(id="bar")), Call(args=[]))
    """

    matchers: Sequence[Matcher]

    def __init__(self, *matchers: Matcher) -> None:
        """
        Initialize with multiple matchers that must all succeed.

        Args:
            *matchers: Variable number of matchers that must all match
        """
        self.matchers = matchers

    def matches(self, node: ast.AST) -> bool:
        return all(matcher.matches(node) for matcher in self.matchers)


@dataclass
class AtLeastN[M](Matcher):
    """
    Matcher for sequences requiring at least N matching elements.

    Example:

        Call(args=AtLeastN(n=2))

    """

    n: int
    """Minimum number of elements required"""

    matcher: Matcher | None = None
    """Optional matcher for individual elements"""

    def matches(self, node: list[Any]) -> bool:
        res, _ = self.sequence(node)
        return res

    def sequence(self, seq: list[Any]) -> tuple[bool, list[Any]]:
        matcher = self.matcher or DoNotCare()
        matches = 0
        for item in seq:
            if matcher.matches(item):
                matches += 1
            else:
                break

        return matches >= self.n, seq[matches:]


@dataclass
class AtMostN[M](Matcher):
    """
    Matcher for sequences requiring at most N matching elements.

    Example:

        Call(args=AtMostN(n=2))
    """

    n: int
    """Maximum number of elements required"""

    matcher: Matcher | None = None
    """Optional matcher for individual elements"""

    def matches(self, node: list[Any]) -> bool:
        res, _ = self.sequence(node)
        return res

    def sequence(self, seq: list[Any]) -> tuple[bool, list[Any]]:
        matcher = self.matcher or DoNotCare()
        matches = 0
        for item in seq:
            if matcher.matches(item):
                matches += 1
            else:
                break
        return matches <= self.n, seq[matches:]


class SequenceMatcher(Matcher):
    def __init__(self, *patterns: Any) -> None:
        self.patterns = patterns

    def matches(self, node: list[Matcher]) -> bool:
        if not isinstance(node, list | tuple):
            return False
        patterns: list[Matcher] = list(self.patterns)
        seq = list(node)
        while patterns:
            if not isinstance(patterns[0], AtLeastN | AtMostN):
                if not seq:
                    return False
                pattern = patterns.pop(0)
                item = seq.pop(0)
                if pattern.matches(item) is False:
                    return False
                continue
            elif not isinstance(patterns[-1], AtLeastN | AtMostN):
                if not seq:
                    return False
                pattern = patterns.pop(-1)
                item = seq.pop(-1)
                if pattern.matches(item) is False:
                    return False
                continue
            elif isinstance(patterns[0], AtLeastN | AtMostN):
                pattern = cast(AtLeastN | AtMostN, patterns.pop(0))
                res, seq = pattern.sequence(seq)
                if res is False:
                    return False
            else:
                raise TypeError("Not implemented yet")
        return not seq
