import ast
import re
from pathlib import Path

MODEL_DIR = Path("src/local_newsifier/models")
SKIP_FILES = {"__init__.py", "base.py", "base_state.py", "state.py"}


def parse_bases(node):
    bases = []
    for b in node.bases:
        if isinstance(b, ast.Name):
            bases.append(b.id)
        elif isinstance(b, ast.Attribute):
            bases.append(b.attr)
        else:
            try:
                bases.append(ast.unparse(b))
            except Exception:
                pass
    return bases


def find_table_models(tree):
    result = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            table_kw = any(
                kw.arg == "table" and isinstance(kw.value, ast.Constant) and kw.value.value
                for kw in getattr(node, "keywords", [])
            )
            if table_kw:
                result.append((node.name, parse_bases(node)))
    return result


for path in sorted(MODEL_DIR.glob("*.py")):
    if path.name in SKIP_FILES:
        continue
    text = path.read_text()
    tree = ast.parse(text)
    models = find_table_models(tree)
    if not models:
        continue

    lines = text.splitlines()
    # find insertion index (before first class)
    insert_index = next((i for i, l in enumerate(lines) if l.startswith("class ")), len(lines))

    insert_lines = []
    for cls_name, bases in models:
        if "TableBase" in bases:
            base_parent = "TableBase"
        else:
            base_parent = "SQLModel"
        insert_lines.append(f"class {cls_name}Base({base_parent}):")
        insert_lines.append(f"    \"\"\"Base model for {cls_name}.\"\"\"")
        insert_lines.append(f"    # TODO: move field definitions from {cls_name} here")
        insert_lines.append("")
        insert_lines.append(f"class {cls_name}Read({cls_name}Base):")
        insert_lines.append(f"    \"\"\"Read model for {cls_name}.\"\"\"")
        insert_lines.append("    pass")
        insert_lines.append("")

        # modify class definition line
        pattern = rf"^class {cls_name}\(([^)]*)\)"
        for i, line in enumerate(lines):
            m = re.match(pattern, line)
            if m:
                inside = m.group(1)
                parts = [p.strip() for p in inside.split(',')]
                parts = [p for p in parts if p not in {"SQLModel", "TableBase"}]
                base_parts = [p for p in parts if '=' not in p]
                kw_parts = [p for p in parts if '=' in p]
                base_parts.append(f"{cls_name}Base")
                new_inside = ', '.join(base_parts + kw_parts)
                lines[i] = re.sub(pattern, f"class {cls_name}({new_inside})", line)
                break

    # insert new classes
    lines = lines[:insert_index] + insert_lines + lines[insert_index:]
    path.write_text("\n".join(lines) + "\n")

print("Model files updated.")
