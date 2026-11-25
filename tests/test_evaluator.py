"""Exercise the grammar and compile-time evaluation."""

import unittest
from decimal import Decimal

from src.evaluator import evaluate
from src.parser import ConfigError


class EvaluatorTests(unittest.TestCase):
    """Cover valid configurations and values."""

    def test_comment_only_document(self):
        """Treat whitespace and comments as an empty document."""
        self.assertEqual(evaluate("#= описания\nнет =#\n"), (None, []))

    def test_comments_between_tokens(self):
        """Ignore multiple comments in declarations and nested values."""
        source = """var #= комментарий =# base := 1.5;
        ([a: #= многострочный
        комментарий =# ([b: |+ base #= аргумент =# 1|]),])"""
        self.assertEqual(evaluate(source), ({"a": {"b": Decimal("2.5")}}, []))

    def test_number_forms(self):
        """Accept fractional and trailing-dot forms with decimal precision."""
        for text in ("12.", "0.001", "12345678901234567890123456789.123"):
            with self.subTest(text=text):
                self.assertEqual(evaluate(text), (Decimal(text), []))

    def test_strings(self):
        """Preserve whitespace, Unicode and comment markers inside strings."""
        text = "  текст\n([ #= строка =# | + < &  "
        self.assertEqual(evaluate(f"q({text})"), (text, []))
        self.assertEqual(evaluate("q()"), ("", []))

    def test_dictionaries(self):
        """Read empty dictionaries, nested dictionaries and ordered keys."""
        source = "([_empty: ([]), inner: ([_empty: q(да), count: 2.]),])"
        value, printed = evaluate(source)
        self.assertEqual(list(value), ["_empty", "inner"])
        self.assertEqual(value["_empty"], {})
        self.assertEqual(value["inner"], {"_empty": "да", "count": Decimal(2)})
        self.assertEqual(printed, [])

    def test_constant_declarations(self):
        """Resolve constants in source order and keep them out of the result."""
        source = "var base := 0.1; var total := |+ base 0.2|; |+ total 1|"
        self.assertEqual(evaluate(source), (Decimal("1.3"), []))
        self.assertEqual(evaluate("var base := 0.1;"), (None, []))

    def test_constant_scope(self):
        """Keep separate translations independent of each other."""
        evaluate("var local := 1.;")
        with self.assertRaisesRegex(ConfigError, "'local' не объявлена"):
            evaluate("|+ local 1|")

    def test_subtraction(self):
        """Subtract the second argument and allow negative results."""
        self.assertEqual(evaluate("|- 2 5|"), (Decimal(-3), []))

    def test_power_with_nested_arguments(self):
        """Evaluate nested operations and permit negative exponents."""
        source = "|pow |+ 1 1| |- 1 3||"
        self.assertEqual(evaluate(source), (Decimal("0.25"), []))

    def test_print_nested_values(self):
        """Return printed numbers, strings and dictionaries in order."""
        source = """
        var title := q(архив);
        var options := ([label: |print title|, count: |+ |print 2| 1|]);
        |print options|
        """
        options = {"label": "архив", "count": Decimal(3)}
        printed = ["архив", Decimal(2), options]
        self.assertEqual(evaluate(source), (options, printed))

    def test_names_matching_keywords(self):
        """Allow keyword spellings in positions reserved for names."""
        source = "var var := 1.; ([print: |+ var 1|, pow: 3.])"
        expected = {"print": Decimal(2), "pow": Decimal(3)}
        self.assertEqual(evaluate(source)[0], expected)


class InvalidSourceTests(unittest.TestCase):
    """Cover syntax errors and invalid constant evaluation."""

    def test_malformed_constructs(self):
        """Reject invalid literals, names, delimiters and arities."""
        cases = (
            "#= незакрытый комментарий",
            "q(нет скобки",
            "42",
            ".75",
            "-1.0",
            "1.0e2",
            "([Upper: 1.])",
            "([key1: 1.])",
            "([key 1.])",
            "([a: 1. b: 2.])",
            "([a: 1.]",
            "var a := 1.",
            "1. var a := 2.;",
            "1. 2.",
            "|+ one1|",
            "|+ 1|",
            "|pow 2 3 4|",
            "|print |",
            "|print 1 2|",
            "|other 1|",
        )
        for source in cases:
            with self.subTest(source=source), self.assertRaises(ConfigError):
                evaluate(source)

    def test_syntax_error_positions(self):
        """Locate unexpected characters, valid tokens and end of input."""
        cases = (
            ("([\n  key: @\n])", "строка 2, столбец 8: неожиданный символ"),
            ("([\n  key: ,\n])", "строка 2, столбец 8: неожиданный элемент"),
            ("([\n  key: 1.\n", "строка 3, столбец 1: неожиданный конец"),
        )
        for source, diagnostic in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ConfigError, diagnostic):
                    evaluate(source)

    def test_invalid_evaluation(self):
        """Reject invalid references, duplicate names and arithmetic."""
        cases = (
            ("var a := |+ a 1|;", "'a' не объявлена"),
            ("var a := 1.; var a := 2.;", "'a' уже объявлена"),
            ("([key: 1., key: 2.])", "'key' уже есть"),
            ("|+ q(текст) 1|", "требует два числа"),
            ("|pow 2 ([])|", "требует два числа"),
            ("|pow |- 0 1| 0.5|", "недопустимый результат"),
            ("q(\x00)", "недопустимый для XML 1.0 символ"),
        )
        for source, diagnostic in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ConfigError, diagnostic):
                    evaluate(source)
