"""Check docstrings against the course SKILL.md rules.

Rules checked for every module, class, function and method (including
nested functions):

* a docstring exists; modules get one at the very top;
* function and method docstrings are multi-line, with a one-line summary
  ending in a period, then a blank line;
* an ``Args:`` section lists every parameter except ``self``/``cls``
  exactly once, in signature order (``Args:`` / ``None.`` when there
  are none);
* a ``Returns:`` (or ``Yields:``) section is present;
* no docstring line is longer than 72 characters;
* the summary doesn't start with "This function", "Helper", "Used to".

Usage:
    python verification/check_docstrings.py [paths...]

Exits with status 1 and lists every problem if any rule is broken.
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = ["northwind", "run_analysis.py", "verification"]
MAX_LINE = 72
BANNED_STARTS = ("this function", "helper", "used to")


def _params(node):
    """Return a function's parameter names in signature order.

    Args:
        node (ast.FunctionDef | ast.AsyncFunctionDef): Function node.

    Returns:
        list[str]: Names, excluding ``self`` and ``cls``; ``*args`` and
        ``**kwargs`` keep their bare names.
    """
    a = node.args
    names = [p.arg for p in a.posonlyargs + a.args]
    if a.vararg:
        names.append(a.vararg.arg)
    names += [p.arg for p in a.kwonlyargs]
    if a.kwarg:
        names.append(a.kwarg.arg)
    return [n for n in names if n not in ("self", "cls")]


def _documented_args(doc):
    """Return parameter names listed in a Google-style Args section.

    Args:
        doc (str): Docstring text.

    Returns:
        list[str] | None: Names in order; an empty list for
        ``Args: None.``; None if there is no Args section.
    """
    lines = doc.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "Args:")
    except StopIteration:
        return None
    names = []
    indent = None
    for line in lines[start + 1:]:
        if not line.strip():
            break
        stripped = line.lstrip()
        level = len(line) - len(stripped)
        if indent is None:
            indent = level
        if level < indent or stripped.endswith(":") and stripped[:-1] in ("Returns", "Yields", "Raises"):
            break
        if level == indent:
            if stripped == "None.":
                return []
            names.append(stripped.split(" ", 1)[0].split("(", 1)[0].rstrip(":").lstrip("*"))
    return names


def check_node(node, path, problems):
    """Check one module, class or function docstring.

    Args:
        node (ast.AST): Module, ClassDef or FunctionDef node.
        path (pathlib.Path): File the node is in.
        problems (list[str]): Collected problems; appended to.

    Returns:
        None.
    """
    name = getattr(node, "name", "<module>")
    where = f"{path.relative_to(ROOT)}:{getattr(node, 'lineno', 1)} {name}"
    doc = ast.get_docstring(node, clean=False)
    if not doc:
        problems.append(f"{where}: missing docstring")
        return
    clean = ast.get_docstring(node)
    for line in doc.splitlines():
        if len(line.rstrip()) > MAX_LINE:
            problems.append(f"{where}: line over {MAX_LINE} chars")
            break
    summary = clean.splitlines()[0].strip()
    if not summary.endswith("."):
        problems.append(f"{where}: summary line doesn't end with a period")
    if summary.lower().startswith(BANNED_STARTS):
        problems.append(f"{where}: summary starts with a banned phrase")
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return
    lines = clean.splitlines()
    if len(lines) < 3 or lines[1].strip():
        problems.append(f"{where}: not multi-line with a blank line after the summary")
    documented = _documented_args(clean)
    expected = _params(node)
    if documented is None:
        problems.append(f"{where}: no Args section")
    elif documented != expected:
        problems.append(f"{where}: Args {documented} don't match signature {expected}")
    if "Returns:" not in clean and "Yields:" not in clean:
        problems.append(f"{where}: no Returns/Yields section")


def main(paths=None):
    """Check every Python file under the given paths.

    Args:
        paths (list[str] | None): Files or folders relative to the
            project root; None uses the default set.

    Returns:
        int: 0 if every docstring follows the rules, otherwise 1.
    """
    files = []
    for p in paths or DEFAULT_PATHS:
        target = ROOT / p
        files += sorted(target.rglob("*.py")) if target.is_dir() else [target]
    problems, count = [], 0
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if path.name == "__init__.py" and not tree.body:
            continue
        check_node(tree, path, problems)
        count += 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                check_node(node, path, problems)
                count += 1
    for p in problems:
        print(p)
    print(f"\n{count - len({p.split(': ')[0] for p in problems})}/{count} docstrings follow every rule "
          f"({len(problems)} problems).")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or None))
