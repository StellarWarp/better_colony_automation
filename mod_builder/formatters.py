"""Lightweight formatters for generated PDX/Jinja-PDX text.

These functions deliberately operate on text instead of AST nodes. Generated
templates often emit valid script with poor whitespace, and a brace formatter is
enough to make generated files stable without making templates harder to read.
"""

from __future__ import annotations

import re
from collections.abc import Iterable


INDENT = "    "
JINJA_TAG_RE = re.compile(r"^\s*{%-?\s*([a-zA-Z_][a-zA-Z0-9_]*)\b")
JINJA_END_TAGS = {"endfor", "endif", "endmacro", "endblock", "endfilter", "endwith", "endraw"}
JINJA_MID_TAGS = {"else", "elif"}
JINJA_START_TAGS = {"for", "if", "macro", "block", "filter", "with", "raw"}


def _strip_comment(line: str) -> str:
    """Return the part of a PDX line before an unquoted # comment."""
    in_quote = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_quote = not in_quote
            continue
        if char == "#" and not in_quote:
            return line[:index]
    return line


def _brace_delta(line: str) -> tuple[int, int]:
    """Count opening and closing block brackets outside quotes and comments."""
    code = _strip_comment(line)
    in_quote: str | None = None
    escaped = False
    opens = 0
    closes = 0
    index = 0
    while index < len(code):
        char = code[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if char == "\\":
            escaped = True
            index += 1
            continue
        if char in {"'", '"'}:
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
            index += 1
            continue
        if in_quote is not None:
            index += 1
            continue
        two = code[index : index + 2]
        if two == "{#":
            comment_end = code.find("#}", index + 2)
            if comment_end == -1:
                break
            index = comment_end + 2
            continue
        if two in {"{{", "{%"}:
            opens += 1
            index += 2
            continue
        if two in {"}}", "%}"}:
            closes += 1
            index += 2
            continue
        if char in {"{", "("}:
            opens += 1
        elif char in {"}", ")"}:
            closes += 1
        index += 1
    return opens, closes


def _leading_closes(line: str) -> int:
    """Count closing braces at the beginning of the code part of a line."""
    stripped = _strip_comment(line).lstrip()
    if stripped.startswith("#}"):
        return 0
    if stripped.startswith(("}}", "%}")):
        return 1
    if len(stripped) >= 3 and stripped[0] in {"-", "+"} and stripped[1:3] in {"}}", "%}"}:
        return 1
    count = 0
    for char in stripped:
        if char in {"}", ")"}:
            count += 1
        elif char.isspace():
            continue
        else:
            break
    return count


def _indent_lines(lines: Iterable[str], *, keep_blank_lines: bool, include_jinja: bool) -> list[str]:
    formatted: list[str] = []
    bracket_depth = 0
    jinja_depth = 0
    source_lines = list(lines)
    index = 0

    while index < len(source_lines):
        raw_line = source_lines[index]
        stripped = raw_line.strip()
        if not stripped:
            if keep_blank_lines:
                formatted.append("")
            index += 1
            continue

        if include_jinja and stripped.startswith("{#"):
            formatted.append(f"{INDENT * jinja_depth}{stripped}")
            index += 1
            continue

        jinja_tag = JINJA_TAG_RE.match(stripped)
        jinja_keyword = jinja_tag.group(1) if jinja_tag else None
        jinja_dedent = include_jinja and jinja_keyword in (JINJA_END_TAGS | JINJA_MID_TAGS)
        jinja_indent = max(jinja_depth - (1 if jinja_dedent else 0), 0)

        opens, closes = _brace_delta(stripped)
        line_depth = max(bracket_depth - _leading_closes(stripped), 0)
        formatted.append(f"{INDENT * (jinja_indent + line_depth)}{stripped}")

        bracket_depth = max(bracket_depth + opens - closes, 0)

        if include_jinja and jinja_keyword:
            if jinja_keyword in JINJA_END_TAGS:
                jinja_depth = max(jinja_depth - 1, 0)
            elif jinja_keyword in JINJA_MID_TAGS:
                # else/elif stay at the same nesting depth as the matching if.
                pass
            elif jinja_keyword in JINJA_START_TAGS:
                jinja_depth += 1

        index += 1

    return formatted


def _separate_top_level_blocks(lines: Iterable[str]) -> list[str]:
    separated: list[str] = []
    previous_depth = 0

    for line in lines:
        opens, closes = _brace_delta(line)
        starts_top_level = previous_depth == 0 and bool(line.strip()) and not line.lstrip().startswith("#")

        if separated and starts_top_level:
            while separated and separated[-1] == "":
                separated.pop()
            separated.extend(["", ""])

        separated.append(line)
        previous_depth = max(previous_depth + opens - closes, 0)

    return separated


def format_pdx_code(content: str) -> str:
    """Format generated PDX/GUI script.

    Empty lines are removed first, then top-level blocks are separated by two
    blank lines. Inline brace pairs such as `{ x = 0 y = 0 }` have zero net
    indentation impact.
    """
    lines = _indent_lines(content.splitlines(), keep_blank_lines=False, include_jinja=False)
    return "\n".join(_separate_top_level_blocks(lines)).rstrip() + "\n"


def format_jinja_pdx_template(content: str) -> str:
    """Format a Jinja template containing PDX-like script.

    This preserves blank lines and also indents Jinja control structures. It is
    intentionally not wired into the normal build to avoid rewriting templates
    unless we explicitly choose to run a template cleanup pass.
    """
    return "\n".join(_indent_lines(content.splitlines(), keep_blank_lines=True, include_jinja=True)).rstrip() + "\n"
