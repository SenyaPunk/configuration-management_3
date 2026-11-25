
import argparse
import sys

from .evaluator import evaluate
from .parser import ConfigError
from .xml_output import format_printed, to_xml


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    cli = argparse.ArgumentParser(
        description="Преобразует конфигурацию варианта №13 из stdin в XML."
    )
    cli.parse_args()

    try:
        source = sys.stdin.buffer.read().decode("utf-8-sig")
        value, printed = evaluate(source)
        output = to_xml(value)
        messages = [format_printed(item) for item in printed]
    except UnicodeDecodeError:
        print("Ошибка: входной текст должен быть в UTF-8", file=sys.stderr)
        return 1
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    except RecursionError:
        print("Ошибка: слишком большая глубина вложенности", file=sys.stderr)
        return 1

    for message in messages:
        print(message, file=sys.stderr)
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
