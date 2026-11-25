"""Serialize configuration values into XML 1.0."""

from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, indent, tostring

from .evaluator import Value


def to_xml(value: Value | None) -> str:
    """Wrap the document value in a config element and format the XML."""
    root = Element("config")
    if value is not None:
        root.append(_value_element(value))
    indent(root, space="  ")
    return _serialize(root, declaration=True) + "\n"


def format_printed(value: Value) -> str:
    """Display scalars as text and dictionaries as XML fragments."""
    if isinstance(value, dict):
        return _serialize(_value_element(value))
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


def _value_element(value: Value) -> Element:
    """Build a typed element for one value, retaining dictionary order."""
    if isinstance(value, dict):
        element = Element("dict")
        for name, child in value.items():
            entry = SubElement(element, "entry", name=name)
            entry.append(_value_element(child))
        return element
    if isinstance(value, Decimal):
        element = Element("number")
        element.text = format(value, "f")
        return element
    element = Element("string")
    element.text = value
    return element


def _serialize(element: Element, *, declaration: bool = False) -> str:
    """Escape carriage returns so XML parsers preserve string contents."""
    xml = tostring(element, encoding="utf-8", xml_declaration=declaration)
    return xml.decode("utf-8").replace("\r", "&#13;")
