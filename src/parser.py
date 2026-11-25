
from pathlib import Path

from lark import Lark, Tree, UnexpectedCharacters, UnexpectedToken

GRAMMAR_FILE = Path(__file__).with_name("config.lark")
PARSER = Lark(
    GRAMMAR_FILE.read_text(encoding="utf-8"),
    parser="lalr",
    maybe_placeholders=False,
    propagate_positions=True,
)


class ConfigError(ValueError):

    def __init__(self, line: int, column: int, message: str):
        super().__init__(f"строка {line}, столбец {column}: {message}")


def parse(source: str) -> Tree:
    try:
        return PARSER.parse(source)
    except UnexpectedCharacters as error:
        message = f"неожиданный символ {error.char!r}"
        raise ConfigError(error.line, error.column, message) from error
    except UnexpectedToken as error:
        if error.token.type == "$END":
            line = source.count("\n") + 1
            column = len(source.rsplit("\n", 1)[-1]) + 1
            message = "неожиданный конец ввода"
            raise ConfigError(line, column, message) from error
        message = f"неожиданный элемент {str(error.token)!r}"
        raise ConfigError(error.line, error.column, message) from error
