"""Format PDX-like Jinja templates in mod_builder/templates.

This is an explicit maintenance step, not part of normal generation. It keeps
template blank lines and avoids localisation/YAML templates where indentation
and quoted strings carry different semantics.
"""

from __future__ import annotations

from pathlib import Path

try:
    from .formatters import format_jinja_pdx_template
except ImportError:
    from formatters import format_jinja_pdx_template


ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"
PDX_TEMPLATE_SUFFIXES = (".txt.j2", ".gui.j2", ".gfx.j2")


def should_format_template(path: Path) -> bool:
    rel = path.relative_to(TEMPLATE_DIR)
    rel_parts = set(rel.parts)
    if "localisation" in rel_parts or "generated_configs" in rel_parts:
        return False
    if str(path).endswith(PDX_TEMPLATE_SUFFIXES):
        return True
    return len(rel.parts) >= 2 and rel.parts[0] == "component" and path.suffix == ".j2"


def main() -> None:
    changed = 0
    scanned = 0
    for path in sorted(TEMPLATE_DIR.rglob("*.j2")):
        if not should_format_template(path):
            continue
        scanned += 1
        original = path.read_text(encoding="utf-8")
        formatted = format_jinja_pdx_template(original)
        if formatted != original:
            path.write_text(formatted, encoding="utf-8")
            changed += 1
    print(f"模板格式化完成: 扫描 {scanned} 个, 修改 {changed} 个")


if __name__ == "__main__":
    main()
