import pytest
import xml.etree.ElementTree as ET

from xmllens.core import _is_number_str, _is_number, _format_xpath, _match_xpath_pattern, _get_tolerances_for_path, \
    _path_matches_any_xpath, _deep_compare_xml


# -----------------------------------------------------------------------------
# Tests for _is_number_str
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("s,expected", [
    ("123", True),
    ("123.45", True),
    ("-0.001", True),
    ("1e-6", True),
    ("NaN", True),  # float("NaN") is valid
    ("Infinity", True),
    ("abc", False),
    ("", False),
    ("12a", False),
])
def test_is_number_str(s, expected):
    assert _is_number_str(s) == expected


# -----------------------------------------------------------------------------
# Tests for _is_number
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("v,expected", [
    (123, True),
    (123.45, True),
    (-5, True),
    (True, False),  # bool is subclass of int
    ("123", False),
    (None, False),
])
def test_is_number(v, expected):
    assert _is_number(v) == expected


# -----------------------------------------------------------------------------
# Tests for _format_xpath
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("path,expected", [
    ((), "/"),
    (("root",), "/root"),
    (("a", "b", "c"), "/a/b/c"),
])
def test_format_xpath(path, expected):
    assert _format_xpath(path) == expected


# -----------------------------------------------------------------------------
# Tests for _match_xpath_pattern
# -----------------------------------------------------------------------------
@pytest.mark.parametrize("pattern,path,expected", [
    ("/a/b/c", "/a/b/c", True),
    ("/a/b/c", "/a/b/d", False),
    ("//b", "/a/b", True),
    ("//b", "/x/y/z", False),
    ("/a/*/c", "/a/b/c", True),
    ("/a/*/c", "/a/x/y", False),
    ("/a/b[1]/c", "/a/b[1]/c", True),
    ("/a/b[2]/c", "/a/b[1]/c", False),
    ("//b[2]", "/x/y/b[2]", True),
])
def test_match_xpath_pattern(pattern, path, expected):
    assert _match_xpath_pattern(pattern, path) == expected


# -----------------------------------------------------------------------------
# Tests for _get_tolerances_for_path
# -----------------------------------------------------------------------------
def test_get_tolerances_exact_match():
    abs_tol_paths = {"/a/b": 0.01}
    rel_tol_paths = {"/a/b": 0.1}
    abs_tol, rel_tol = _get_tolerances_for_path("/a/b", 1e-5, 1e-5, abs_tol_paths, rel_tol_paths)
    assert abs_tol == 0.01
    assert rel_tol == 0.1


def test_get_tolerances_pattern_match():
    abs_tol_paths = {"//b": 0.1}
    rel_tol_paths = {"//b": 0.2}
    abs_tol, rel_tol = _get_tolerances_for_path("/a/b", 1e-5, 1e-5, abs_tol_paths, rel_tol_paths)
    assert abs_tol == 0.1
    assert rel_tol == 0.2


def test_get_tolerances_default():
    abs_tol, rel_tol = _get_tolerances_for_path("/x", 0.001, 0.002, {}, {})
    assert abs_tol == 0.001
    assert rel_tol == 0.002


# -----------------------------------------------------------------------------
# Tests for _path_matches_any_xpath
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("path,patterns,expected", [
    ("/a/b", ["/a/b"], True),
    ("/a/b", ["/a/*"], True),
    ("/a/b", ["//b"], True),
    ("/x/y", ["/a/b"], False),
])
def test_path_matches_any_xpath(path, patterns, expected):
    assert _path_matches_any_xpath(path, patterns) == expected


# -----------------------------------------------------------------------------
# Tests for _deep_compare_xml
# -----------------------------------------------------------------------------
def make_elem(xml: str) -> ET.Element:
    return ET.fromstring(xml)


def test_deep_compare_xml_basic_match():
    a = make_elem("<root><x>1</x></root>")
    b = make_elem("<root><x>1</x></root>")
    assert _deep_compare_xml(a, b, (), 0, 0, {}, {}, [], 1e-12, False)


def test_deep_compare_xml_tag_mismatch():
    a = make_elem("<root><x>1</x></root>")
    b = make_elem("<root><y>1</y></root>")
    assert not _deep_compare_xml(a, b, (), 0, 0, {}, {}, [], 1e-12, False)


def test_deep_compare_xml_attr_mismatch():
    a = make_elem('<root><x id="1"/></root>')
    b = make_elem('<root><x id="2"/></root>')
    assert not _deep_compare_xml(a, b, (), 0, 0, {}, {}, [], 1e-12, False)


def test_deep_compare_xml_text_mismatch():
    a = make_elem("<root><x>1</x></root>")
    b = make_elem("<root><x>2</x></root>")
    assert not _deep_compare_xml(a, b, (), 0, 0, {}, {}, [], 1e-12, False)


def test_deep_compare_xml_numeric_with_tolerance():
    a = make_elem("<root><x>1.00</x></root>")
    b = make_elem("<root><x>1.001</x></root>")
    assert _deep_compare_xml(a, b, (), 0.01, 0.0, {}, {}, [], 1e-12, False)


def test_deep_compare_xml_ignore_field():
    a = make_elem("<root><x>1</x><y>2</y></root>")
    b = make_elem("<root><x>1</x><y>999</y></root>")
    assert _deep_compare_xml(a, b, (), 0, 0, {}, {}, ["/root/y"], 1e-12, False)


def test_deep_compare_xml_child_count_mismatch():
    a = make_elem("<root><x>1</x></root>")
    b = make_elem("<root><x>1</x><y>2</y></root>")
    assert not _deep_compare_xml(a, b, (), 0, 0, {}, {}, [], 1e-12, False)


def test_deep_compare_xml_nested_numeric_with_path_tolerance():
    a = make_elem("<root><group><val>100</val></group></root>")
    b = make_elem("<root><group><val>102</val></group></root>")
    abs_tol_paths = {"//val": 5.0}
    rel_tol_paths = {}
    assert _deep_compare_xml(a, b, (), 0, 0, abs_tol_paths, rel_tol_paths, [], 1e-12, False)
