"""End-to-end tests: run the whole pipeline on a copy of the project (plan 7.3)."""

import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from northwind.config import ROOT
from northwind.load import file_sha256

pytestmark = pytest.mark.integration

WORKBOOK = ROOT / "data" / "Northwind Database.xlsx"
if not WORKBOOK.exists():
    pytest.skip("real workbook not present", allow_module_level=True)

COPY = ["run_analysis.py", "northwind", "templates", "verification", "data"]
TIMESTAMP = re.compile(r"Built \d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC")


def _run_copy(dest):
    """Copy the project into ``dest`` and run the pipeline there.

    Args:
        dest (pathlib.Path): Empty folder.

    Returns:
        subprocess.CompletedProcess: The finished run.
    """
    for name in COPY:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, dest / name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(src, dest / name)
    return subprocess.run([sys.executable, "run_analysis.py"], cwd=dest, capture_output=True,
                          text=True, encoding="utf-8", timeout=600)


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    first, second = tmp_path_factory.mktemp("run1"), tmp_path_factory.mktemp("run2")
    return (first, _run_copy(first)), (second, _run_copy(second))


@pytest.fixture(scope="module")
def page(runs):
    (root, _), _ = runs
    return (root / "docs" / "index.html").read_text(encoding="utf-8")


def test_pipeline_succeeds(runs):
    for root, proc in runs:
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (root / "docs" / "index.html").exists()
        assert (root / "docs" / ".nojekyll").exists()


def test_page_has_every_section(page):
    for anchor in ('id="q1"', 'id="q2"', 'id="q3"', "Technical appendix", "Verification",
                   "What this analysis can't tell us", "Reproduce:", "Input fingerprint"):
        assert anchor in page


def _section(page, qid):
    start = page.index(f'id="{qid}"')
    return page[start:page.index("</section>", start)]


def test_two_titled_charts_per_question(page):
    for qid in ("q1", "q2", "q3"):
        section = _section(page, qid)
        assert section.count("<svg") == 2, qid
        assert section.count('class="chart-title"') == 2, qid


def test_each_question_has_required_parts_in_order(page):
    parts = ["<h2", "Why it matters", "Key finding", "<svg", "Business interpretation",
             "Recommended action", "<details"]
    for qid in ("q1", "q2", "q3"):
        section = _section(page, qid)
        positions = [section.index(p) for p in parts]
        assert positions == sorted(positions), qid
        actions = section[section.index("Recommended action"):section.index("<details")]
        assert actions.count("<li>") >= 2, qid
        full = section[section.index("Full interpretation"):]
        assert full.count("<li>") >= 3, qid


def test_one_primary_chart_visible_per_question(page):
    for qid in ("q1", "q2", "q3"):
        section = _section(page, qid)
        visible = section[:section.index("<details")]
        assert visible.count("<svg") == 1, qid
        # Only Q2 shows a table up front: the top products to order.
        assert visible.count("<table") == (1 if qid == "q2" else 0), qid


def test_shortages_are_not_called_confirmed_backorders(page):
    q2 = _section(page, "q2")
    assert "likely backorders" not in page and "Possible backorder" not in page
    assert "possible shortages" in q2 and "not confirmed backorders" in q2


def test_rescue_does_not_blame_a_growing_key_account(page):
    q1 = _section(page, "q1")
    assert "the key account is the likely issue" not in page
    assert "Ernst Handel" not in q1 or "the main cause" in q1


def test_no_recommendation_to_act_on_unsupported_freight(page):
    q3 = _section(page, "q3")
    assert "Review United Package&#39;s rates" not in q3
    assert "rates, or move comparable shipments" not in q3
    assert "No action: the gap isn't clear" in q3.replace("&#39;", "'")


def test_no_missing_value_text(page):
    visible = re.sub(r"<svg.*?</svg>", "", page, flags=re.S)
    visible = re.sub(r"<[^>]+>", " ", visible)
    for bad in ("NaN", "None", " nan ", " inf "):
        assert bad not in visible, bad


def test_self_contained(page):
    assert not re.search(r'<(script|link|img)[^>]+(src|href)="https?://', page)
    assert "<script" not in page
    assert re.findall(r"#[0-9a-fA-F]{6}", re.sub(r"<style>.*?</style>", "", page, flags=re.S)) == []


def test_charts_have_text_alternatives(page):
    svgs = re.findall(r"<svg[^>]*>", page)
    assert len(svgs) == 8
    assert all('role="img"' in s and "aria-label=" in s for s in svgs)


def test_headline_numbers_match_tables(runs, page):
    (root, _), _ = runs
    tables = root / "outputs" / "tables"
    with open(tables / "q2_shortlist.csv", encoding="utf-8") as handle:
        first = next(csv.DictReader(handle))
    assert first["ProductName"].replace("'", "&#39;") in page
    findings = json.loads((tables / "q3_findings.json").read_text(encoding="utf-8"))
    assert f"{findings['backlog']['Orders']} unshipped orders" in page
    manifest = json.loads((root / "outputs" / "run_manifest.json").read_text(encoding="utf-8"))
    sql = manifest["sql_crosscheck"]
    assert f"{sql['passed']} of {sql['total']} checks match" in page
    assert sql["passed"] == sql["total"]


def test_deterministic_apart_from_timestamp(runs):
    (a, _), (b, _) = runs
    page_a = TIMESTAMP.sub("", (a / "docs" / "index.html").read_text(encoding="utf-8"))
    page_b = TIMESTAMP.sub("", (b / "docs" / "index.html").read_text(encoding="utf-8"))
    assert page_a == page_b
    for csv_file in sorted((a / "outputs" / "tables").glob("*.csv")):
        assert csv_file.read_bytes() == (b / "outputs" / "tables" / csv_file.name).read_bytes(), csv_file.name


def test_input_unchanged(runs):
    (a, _), _ = runs
    assert file_sha256(a / "data" / "Northwind Database.xlsx") == file_sha256(WORKBOOK)


# --- Corrections from the independent review (gate 6) -----------------------

def _text(html_part):
    html_part = re.sub(r"<svg.*?</svg>", "", html_part, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_part)).replace("&#39;", "'")


def test_q3_does_not_overstate(page):
    q3 = _text(_section(page, "q3"))
    assert "median 7 days everywhere" not in q3
    assert "97%" not in q3
    assert "inconclusive" in q3
    assert "likely range" in q3


def test_q1_separates_clear_from_tentative(page):
    q1 = _text(_section(page, "q1"))
    assert "depending on the quarters compared" in q1
    assert "Tentative" in q1 and "Confirmed" in q1
    assert "borderline" in q1


def test_q2_states_assumption_and_range(page):
    q2 = _text(_section(page, "q2"))
    assert "assuming the undated stock count" in q2
    assert re.search(r"roughly \d+–\d+ (more )?units", q2)
    assert "none has an order in progress" not in q2


def test_review_listed_in_appendix(page):
    assert "Independent review" in page
    assert page.count("Resolution:") >= 10


# --- Executive revisions -------------------------------------------------------

def test_summary_cards_have_one_metric_finding_and_action(page):
    glance = page[page.index('class="glance"'):page.index('class="priorities"')]
    cards = glance.split("<article>")[1:]
    assert len(cards) == 3
    for card in cards:
        assert card.count('class="metric"') == 1
        assert card.count('class="card-action"') == 1
        assert "<ul" not in card


def test_three_ranked_priorities_all_confirmed(page):
    prio = page[page.index('class="priorities"'):page.index('class="legend-note"')]
    assert [int(r) for r in re.findall(r'class="rank">(\d)<', prio)] == [1, 2, 3]
    assert prio.count("Next step:") == 3
    assert prio.count('class="badge confirmed"') == 3
    assert len(set(re.findall(r'class="owner">(\w+)', prio))) == 3


def test_q1_chart_guide_explains_axes_and_six_categories(page):
    q1 = _text(_section(page, "q1"))
    assert "How to read this chart" in q1 and "Across:" in q1 and "Up:" in q1
    for category in ("Rescue", "Protect", "Broaden", "Diagnose", "Maintain", "Invest"):
        assert category in q1


def test_q1_actions_name_an_account(page):
    q1 = _section(page, "q1")
    actions = _text(q1[q1.index("Recommended action"):q1.index("<details")])
    assert "call " in actions and "to find out why orders fell" in actions


def test_q2_buy_list_and_selection_rule(page):
    q2 = _section(page, "q2")
    visible = q2[:q2.index("<details")]
    buy = visible[visible.index('class="buy"'):]
    assert buy.count("<tr>") == 1 + 5
    assert "Order now (units)" in buy
    text = _text(buy)
    assert "urgency tier" in text and "ranked by monthly revenue at stake" in text


def test_glossary_explains_terms(page):
    assert "Terms in plain English" in page
    for term in ("Share of company revenue", "Concentration", "Months of stock", "Order-days",
                 "Likely range", "Adjusted comparison", "Resampling check"):
        assert term in page


def test_q1_question_wording(page):
    assert ("How should Northwind prioritize its sales markets based on revenue performance "
            "and customer concentration risk?") in _section(page, "q1")
    assert "grew or declined" not in page


def test_five_assignment_parts_visible_before_details(page):
    parts = ["<h2", "Why it matters", "Analytical approach", "<svg", "Key finding",
             "Business interpretation"]
    for qid in ("q1", "q2", "q3"):
        visible = _section(page, qid)
        visible = visible[:visible.index("<details")]
        for part in parts:
            assert part in visible, (qid, part)
        assert visible.index("Analytical approach") < visible.index("<svg"), qid
        assert visible.index("Why it matters") < visible.index("Analytical approach"), qid
