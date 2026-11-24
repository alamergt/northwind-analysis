"""Check the published page and repository as an anonymous visitor (plan.md §8.5).

Uses only the Python standard library: no cookies, no tokens, no sign-in.

Checks:
1. The page URL returns HTTP 200 over HTTPS.
2. The page served is byte-for-byte the same as docs/index.html here.
3. The page contains the three questions and the appendix.
4. The repository page and raw README return HTTP 200, and the public
   GitHub API reports the repository as public.

Usage:
    python verification/check_public_site.py

Exits with status 1 if any check fails, and writes the results to
outputs/verification/public_site.json.
"""

import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER, REPO = "alamergt", "northwind-analysis"
PAGE_URL = f"https://{OWNER}.github.io/{REPO}/"
HEADERS = {"User-Agent": "public-site-check/1.0", "Cache-Control": "no-cache"}


def fetch(url):
    """Fetch a URL anonymously.

    Args:
        url (str): Address to fetch.

    Returns:
        tuple[int, bytes, str]: Status code, body and final URL (after
        redirects); status 0 and an empty body on network errors.
    """
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read(), response.geturl()
    except urllib.error.HTTPError as err:
        return err.code, b"", url
    except urllib.error.URLError:
        return 0, b"", url


def main():
    """Run every check, print a report and save it.

    Args:
        None.

    Returns:
        int: 0 if every check passes, otherwise 1.
    """
    results = []

    def record(name, ok, detail):
        results.append({"check": name, "pass": bool(ok), "detail": detail})

    status, body, final = fetch(PAGE_URL)
    record("page returns 200 over HTTPS", status == 200 and final.startswith("https://"),
           f"{status} {final}")
    local = (ROOT / "docs" / "index.html").read_bytes()
    record("served page identical to docs/index.html",
           hashlib.sha256(body).hexdigest() == hashlib.sha256(local).hexdigest(),
           f"served {hashlib.sha256(body).hexdigest()[:16]}… local {hashlib.sha256(local).hexdigest()[:16]}…")
    text = body.decode("utf-8", errors="replace")
    expected = ['id="q1"', 'id="q2"', 'id="q3"', "Technical appendix", "Input fingerprint"]
    missing = [e for e in expected if e not in text]
    record("page has the three questions and the appendix", not missing, f"missing: {missing}" if missing else "all present")

    status, _, _ = fetch(f"https://github.com/{OWNER}/{REPO}")
    record("repository page returns 200 without sign-in", status == 200, str(status))
    status, _, _ = fetch(f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main/README.md")
    record("raw README returns 200 without sign-in", status == 200, str(status))
    status, api, _ = fetch(f"https://api.github.com/repos/{OWNER}/{REPO}")
    private = json.loads(api).get("private") if status == 200 else None
    record("GitHub API reports the repository as public", private is False, f"{status}, private={private}")

    out = ROOT / "outputs" / "verification" / "public_site.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                               "page": PAGE_URL, "results": results}, indent=2), encoding="utf-8")
    for r in results:
        print(f"{'PASS' if r['pass'] else 'FAIL'}  {r['check']}  ({r['detail']})")
    failed = [r for r in results if not r["pass"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} public checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
