from __future__ import annotations

import ast

from typing_extensions import TypeVar

T = TypeVar("T", bound=ast.AST)
