"""Evaluate constants and values in source order."""

import re
from collections.abc import Callable
from decimal import Context, Decimal, DecimalException
from typing import TypeAlias

from lark import Tree
from lark.visitors import Interpreter

from .parser import ConfigError, parse

Value: TypeAlias = Decimal | str | dict[str, "Value"]
PRECISION = 28
STRING_PREFIX_LENGTH = len("q(")
INVALID_XML_CHAR = re.compile(
    r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]"
)


class Evaluator(Interpreter):
    """Keep the constant table and print output local to one translation."""

    def __init__(self):
        """Start with no constants or pending output."""
        self.constants: dict[str, Value] = {}
        self.printed: list[Value] = []
        self.arithmetic = Context(prec=PRECISION)

    def start(self, tree: Tree) -> Value | None:
        """Evaluate declarations first and return the document value."""
        value = None
        for child in tree.children:
            value = self.visit(child)
        return value

    def declaration(self, tree: Tree) -> None:
        """Bind a new constant after evaluating its initializer."""
        token, initializer = tree.children
        name = str(token)
        if name in self.constants:
            message = f"константа {name!r} уже объявлена"
            raise ConfigError(token.line, token.column, message)
        self.constants[name] = self.visit(initializer)

    def reference(self, tree: Tree) -> Value:
        """Look up a previously declared constant."""
        (token,) = tree.children
        name = str(token)
        try:
            return self.constants[name]
        except KeyError as error:
            message = f"константа {name!r} не объявлена"
            raise ConfigError(token.line, token.column, message) from error

    def dictionary(self, tree: Tree) -> dict[str, Value]:
        """Evaluate dictionary entries and reject repeated keys."""
        values: dict[str, Value] = {}
        for entry in tree.children:
            token, expression = entry.children
            name = str(token)
            if name in values:
                message = f"ключ {name!r} уже есть в словаре"
                raise ConfigError(token.line, token.column, message)
            values[name] = self.visit(expression)
        return values

    def number(self, tree: Tree) -> Decimal:
        """Read a decimal number exactly as written."""
        (token,) = tree.children
        return Decimal(token)

    def string(self, tree: Tree) -> str:
        """Unwrap a string and check that it can be written as XML 1.0."""
        (token,) = tree.children
        value = token[STRING_PREFIX_LENGTH:-1]
        if INVALID_XML_CHAR.search(value):
            message = "строка содержит недопустимый для XML 1.0 символ"
            raise ConfigError(token.line, token.column, message)
        return value

    def add(self, tree: Tree) -> Decimal:
        """Add the two operands."""
        return self._calculate(tree, self.arithmetic.add)

    def subtract(self, tree: Tree) -> Decimal:
        """Subtract the second operand from the first."""
        return self._calculate(tree, self.arithmetic.subtract)

    def power(self, tree: Tree) -> Decimal:
        """Raise the first operand to the power of the second."""
        return self._calculate(tree, self.arithmetic.power)

    def print_value(self, tree: Tree) -> Value:
        """Queue the operand for printing and return it unchanged."""
        (value,) = self.visit_children(tree)
        self.printed.append(value)
        return value

    def _calculate(
        self, tree: Tree, operation: Callable[[Decimal, Decimal], Decimal]
    ) -> Decimal:
        """Check operand types and report decimal arithmetic errors."""
        left, right = self.visit_children(tree)
        if not isinstance(left, Decimal) or not isinstance(right, Decimal):
            message = "операция требует два числа"
            raise ConfigError(tree.meta.line, tree.meta.column, message)
        try:
            return operation(left, right)
        except DecimalException as error:
            message = "недопустимый результат арифметической операции"
            raise ConfigError(
                tree.meta.line, tree.meta.column, message
            ) from error


def evaluate(source: str) -> tuple[Value | None, list[Value]]:
    """Return the document value and values requested by print."""
    evaluator = Evaluator()
    value = evaluator.visit(parse(source))
    return value, evaluator.printed
