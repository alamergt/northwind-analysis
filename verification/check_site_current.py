"""Check that the committed page matches a fresh build (used by CI).

Run after ``python run_analysis.py``. Compares the freshly built
``docs/index.html`` with the version committed at HEAD. The build
timestamp is ignored, and each chart is compared by its text description
(which lists every plotted value) rather than by drawing coordinates, so
sub-pixel font differences between operating systems don't cause false
failures while any change in a number or a word still does.

Usage:
    python verification/check_site_current.py

Exits with status 1 if the pages differ.
"""

import difflib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = "docs/index.html"


def normalise(page):
    """Reduce a page to the parts that must match exactly.

    Args:
        page (str): HTML document.

    Returns:
        list[str]: Lines with the timestamp removed and each SVG replaced
        by its aria-label.
    """
    page = re.sub(r"Built \d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC", "Built <time>", page)
    page = re.sub(r'<svg[^>]*aria-label="([^"]*)".*?</svg>', r"<svg \1>", page, flags=re.S)
    return page.splitlines()


def main():
    """Compare the built page with the committed one.

    Args:
        None.

    Returns:
        int: 0 if they match, otherwise 1.
    """
    built = (ROOT / PAGE).read_text(encoding="utf-8")
    committed = subprocess.run(["git", "show", f"HEAD:{PAGE}"], cwd=ROOT, capture_output=True,
                               text=True, encoding="utf-8", check=True).stdout
    diff = list(difflib.unified_diff(normalise(committed), normalise(built), "committed", "built", lineterm=""))
    if diff:
        print("The committed page does not match a fresh build. Run python run_analysis.py and commit docs/.")
        print("\n".join(diff[:40]))
        return 1
    print("Committed page matches a fresh build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
