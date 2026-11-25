"""Verify the converter through its standard input and output streams."""

import subprocess
import sys
import unittest
from pathlib import Path
from xml.etree.ElementTree import fromstring

ROOT = Path(__file__).resolve().parents[1]


def run_cli(source: str | bytes, *args: str) -> subprocess.CompletedProcess:
    """Run the module and capture the raw UTF-8 streams."""
    data = source.encode("utf-8") if isinstance(source, str) else source
    return subprocess.run(
        [sys.executable, "-m", "src", *args],
        input=data,
        capture_output=True,
        cwd=ROOT,
        timeout=10,
        check=False,
    )


class CliTests(unittest.TestCase):
    """Check XML output, diagnostics and representative inputs."""

    def test_xml_structure(self):
        """Represent every value type and preserve dictionary order."""
        result = run_cli("var a := 0.5; ([value: |+ a 1|, nested: ([]),])")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b"")
        self.assertTrue(result.stdout.startswith(b"<?xml version='1.0'"))
        root = fromstring(result.stdout)
        self.assertEqual(root.tag, "config")
        self.assertEqual(root[0].tag, "dict")
        first, second = root[0]
        self.assertEqual(first.attrib, {"name": "value"})
        self.assertEqual((first[0].tag, first[0].text), ("number", "1.5"))
        self.assertEqual(second.attrib, {"name": "nested"})
        self.assertEqual((second[0].tag, list(second[0])), ("dict", []))

    def test_xml_escaping_and_utf8(self):
        """Read a UTF-8 BOM and preserve all XML-safe characters."""
        text = "Привет <a> & 😀\r\n \t"
        result = run_cli(f"\ufeffq({text})")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"&lt;a&gt; &amp;", result.stdout)
        node = fromstring(result.stdout)[0]
        self.assertEqual((node.tag, node.text), ("string", text))

    def test_document_without_value(self):
        """Write an empty root element when the input has only declarations."""
        result = run_cli("var num := 4.;")
        self.assertEqual(result.returncode, 0, result.stderr)
        root = fromstring(result.stdout)
        self.assertEqual(root.tag, "config")
        self.assertEqual(list(root), [])

    def test_print_stream(self):
        """Keep print messages ordered on stderr and XML on stdout."""
        result = run_cli("|print ([a: |print 2|, b: |print q(строка)|])|")
        self.assertEqual(result.returncode, 0, result.stderr)
        number, string, dictionary = result.stderr.decode().splitlines()
        self.assertEqual((number, string), ("2", "строка"))
        self.assertEqual(fromstring(dictionary).tag, "dict")
        self.assertEqual(fromstring(result.stdout)[0].tag, "dict")

    def test_invalid_source(self):
        """Print a position and exit unsuccessfully without emitting XML."""
        result = run_cli("([\n  value: @\n])")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn("строка 2, столбец 10", result.stderr.decode())

    def test_no_output_after_evaluation_error(self):
        """Suppress buffered print output if the document is invalid."""
        result = run_cli("([a: |print q(пролог)|, b: |+ unknown 1|])")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn("'unknown' не объявлена", result.stderr.decode())
        self.assertNotIn("пролог", result.stderr.decode())

    def test_invalid_utf8(self):
        """Report unsupported input bytes as a CLI error."""
        result = run_cli(b"\xff")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"UTF-8", result.stderr)

    def test_deeply_nested_input(self):
        """Report excessive recursion without an interpreter traceback."""
        depth = sys.getrecursionlimit() * 2
        result = run_cli("([x:" * depth + "0." + "])" * depth)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn("глубина вложенности", result.stderr.decode())

    def test_help(self):
        """Allow help to be requested independently of stdin."""
        result = run_cli(b"", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"--help", result.stdout)

    def test_examples(self):
        """Run each submitted example and check a computed setting."""
        cases = (
            ("web_service", ("network", "read_timeout"), "3.5"),
            ("greenhouse", ("temperature", "minimum"), "22.5"),
            ("library", ("loans", "standard", "reminder_day"), "11"),
        )
        for filename, keys, expected in cases:
            with self.subTest(example=filename):
                data = (ROOT / "examples" / f"{filename}.cfg").read_bytes()
                result = run_cli(data)
                self.assertEqual(result.returncode, 0, result.stderr)
                root = fromstring(result.stdout)
                entries = "/dict/".join(f"entry[@name='{key}']" for key in keys)
                actual = root.findtext(f"dict/{entries}/number")
                self.assertEqual(actual, expected)
