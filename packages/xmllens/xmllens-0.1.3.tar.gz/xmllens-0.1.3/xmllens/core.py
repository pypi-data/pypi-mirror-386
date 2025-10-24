import logging
import math
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------

def _is_number_str(s: str) -> bool:
    """Return True if the string represents a valid number."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_number(v: Any) -> bool:
    """Return True if the object is numeric (excluding bool)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _format_xpath(path: Tuple[str, ...]) -> str:
    """Convert path tuple into XPath-like string."""
    if not path:
        return "/"
    return "/" + "/".join(path)


# -----------------------------------------------------------------------------
# Pattern matching (XPath-like)
# -----------------------------------------------------------------------------

def _match_xpath_pattern(pattern: str, path: str) -> bool:
    """
    Match an XPath-like pattern to an XML element path.

    Supports:
      - [n] : numeric index (strict if specified)
      - *   : wildcard tag name
      - //  : recursive descent
    """

    pattern = pattern.strip()
    path = path.strip()

    # Split into tokens
    pattern_parts = [p for p in pattern.split("/") if p]
    path_parts = [p for p in path.split("/") if p]

    def split_token(token: str):
        """Return (tag, index) tuple, where index may be None."""
        if "[" in token and token.endswith("]"):
            tag, idx = token[:-1].split("[", 1)
            return tag, idx
        return token, None

    def token_match(pat_token: str, path_token: str) -> bool:
        """Compare tokens with wildcard and optional index."""
        if pat_token == "*":
            return True

        pat_tag, pat_idx = split_token(pat_token)
        path_tag, path_idx = split_token(path_token)

        # Tag names must match
        if pat_tag != path_tag:
            return False

        # If pattern specifies index, enforce equality
        if pat_idx is not None:
            return pat_idx == path_idx

        # Otherwise, index can be anything
        return True

    def match_from(i_pat: int, i_path: int) -> bool:
        """Recursive matcher that supports //."""
        while i_pat < len(pattern_parts):
            part = pattern_parts[i_pat]

            # Handle recursive descent
            if part == "//":
                if i_pat + 1 == len(pattern_parts):
                    # trailing // matches everything
                    return True
                next_part = pattern_parts[i_pat + 1]
                for j in range(i_path, len(path_parts)):
                    if token_match(next_part, path_parts[j]):
                        if match_from(i_pat + 2, j + 1):
                            return True
                return False

            if i_path >= len(path_parts):
                return False

            if not token_match(part, path_parts[i_path]):
                return False

            i_pat += 1
            i_path += 1

        return i_path == len(path_parts)

    # If pattern starts with //, match anywhere
    if pattern.startswith("//"):
        sub_pattern = pattern[2:]
        for i in range(len(path_parts)):
            sub_path = "/" + "/".join(path_parts[i:])
            if _match_xpath_pattern(sub_pattern, sub_path):
                return True
        return False

    return match_from(0, 0)


def _get_tolerances_for_path(
        path_str: str,
        abs_tol: float,
        rel_tol: float,
        abs_tol_paths: Dict[str, float],
        rel_tol_paths: Dict[str, float],
) -> Tuple[float, float]:
    """
    Resolve abs/rel tolerance for a given XPath path.
    Exact match > pattern match > global default.
    """
    local_abs = abs_tol
    local_rel = rel_tol

    # Exact match first
    if path_str in abs_tol_paths:
        local_abs = abs_tol_paths[path_str]
    if path_str in rel_tol_paths:
        local_rel = rel_tol_paths[path_str]

    # Pattern match second
    for pattern, val in abs_tol_paths.items():
        if _match_xpath_pattern(pattern, path_str):
            local_abs = val
    for pattern, val in rel_tol_paths.items():
        if _match_xpath_pattern(pattern, path_str):
            local_rel = val

    return local_abs, local_rel


def _path_matches_any_xpath(path_str: str, patterns: List[str]) -> bool:
    """Check if path matches any of the ignore patterns."""
    return any(_match_xpath_pattern(p, path_str) for p in patterns)


# -----------------------------------------------------------------------------
# XML Comparison Core
# -----------------------------------------------------------------------------

def compare_xml(
        xml_a: str,
        xml_b: str,
        *,
        ignore_fields: List[str] = None,
        abs_tol: float = 0.0,
        rel_tol: float = 0.0,
        abs_tol_fields: Dict[str, float] = None,
        rel_tol_fields: Dict[str, float] = None,
        epsilon: float = 1e-12,
        show_debug: bool = False,
) -> bool:
    """
    Compare two XML documents with:
      - global abs/rel tolerances
      - per-path tolerances via XPath-like patterns
      - ignored paths
      - strict child order
      - tolerance-based numeric comparison of element text

    Supported XPath subset:
      /a/b/c        : absolute path
      //tag         : recursive descent
      *             : wildcard for element
      [n]           : index in sibling order (1-based)

    Unsupported (for now):
      attribute filters [@attr="x"], slices, or functions.
    """
    ignore_fields = ignore_fields or []
    abs_tol_fields = abs_tol_fields or {}
    rel_tol_fields = rel_tol_fields or {}

    try:
        a = ET.fromstring(xml_a)
        b = ET.fromstring(xml_b)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML input: {e}")

    return _deep_compare_xml(
        a, b, (), abs_tol, rel_tol,
        abs_tol_fields, rel_tol_fields,
        ignore_fields, epsilon, show_debug
    )


def _deep_compare_xml(
        a: ET.Element,
        b: ET.Element,
        path: Tuple[str, ...],
        abs_tol: float,
        rel_tol: float,
        abs_tol_paths: Dict[str, float],
        rel_tol_paths: Dict[str, float],
        ignore_patterns: List[str],
        epsilon: float,
        show_debug: bool,
) -> bool:
    """Recursive deep comparison of XML elements."""
    if show_debug:
        logger.setLevel(logging.DEBUG)
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    current_path = _format_xpath(path + (a.tag,))
    if _path_matches_any_xpath(current_path, ignore_patterns):
        logger.debug(f"[IGNORE] {current_path}")
        return True

    # Tag mismatch
    if a.tag != b.tag:
        logger.debug(f"[TAG MISMATCH] {current_path}: {a.tag} vs {b.tag}")
        return False

    # Attribute mismatch
    if a.attrib != b.attrib:
        logger.debug(f"[ATTR MISMATCH] {current_path}: {a.attrib} vs {b.attrib}")
        return False

    # Text comparison
    text_a = (a.text or "").strip()
    text_b = (b.text or "").strip()

    if text_a or text_b:
        if _is_number_str(text_a) and _is_number_str(text_b):
            a_val, b_val = float(text_a), float(text_b)
            local_abs, local_rel = _get_tolerances_for_path(
                current_path, abs_tol, rel_tol, abs_tol_paths, rel_tol_paths
            )
            diff = abs(a_val - b_val)
            threshold = max(local_abs, local_rel * max(abs(a_val), abs(b_val)))

            logger.debug(
                f"[NUMERIC COMPARE] {current_path}: {a_val} vs {b_val} | "
                f"diff={diff:.6f} | abs_tol={local_abs} | rel_tol={local_rel} | threshold={threshold:.6f}"
            )

            if not math.isclose(a_val, b_val, abs_tol=local_abs + epsilon, rel_tol=local_rel):
                logger.debug(f"[FAIL NUMERIC] {current_path} → diff={diff:.6f} > threshold={threshold:.6f}")
                return False
            else:
                logger.debug(f"[MATCH NUMERIC] {current_path}: within tolerance")
        else:
            if text_a != text_b:
                logger.debug(f"[TEXT MISMATCH] {current_path}: '{text_a}' vs '{text_b}'")
                return False

    # Compare children
    children_a = list(a)
    children_b = list(b)
    if len(children_a) != len(children_b):
        logger.debug(f"[CHILD COUNT MISMATCH] {current_path}: {len(children_a)} vs {len(children_b)}")
        return False

    for i, (child_a, child_b) in enumerate(zip(children_a, children_b), 1):
        if not _deep_compare_xml(
                child_a, child_b,
                path + (f"{a.tag}[{i}]",),
                abs_tol, rel_tol, abs_tol_paths, rel_tol_paths,
                ignore_patterns, epsilon, show_debug
        ):
            logger.debug(f"[FAIL IN ELEMENT] {current_path}/{child_a.tag}[{i}]")
            return False

    logger.debug(f"[MATCH] {current_path}: OK")
    return True
