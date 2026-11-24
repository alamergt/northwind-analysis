"""Build every output from the workbook: python run_analysis.py

Builds the model, runs Q1-Q3, cross-checks the results in SQL, renders the
charts and writes the page to docs/index.html. Exits with status 1 if any
cross-check fails.
"""

import json
import sys
from datetime import datetime, timezone

from northwind import Config, load_model
from northwind import charts, q1_markets, q2_inventory, q3_logistics, report
from northwind.load import file_sha256
from verification.sql_crosscheck import run_checks


def write_table(frame, path):
    """Write a table as UTF-8 CSV, creating the folder if needed.

    Args:
        frame (pandas.DataFrame): Table to write.
        path (pathlib.Path): Destination file.

    Returns:
        None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8", float_format="%.6g")


def main():
    """Run the pipeline and write tables and the run manifest.

    Args:
        None.

    Returns:
        int: Process exit status, 0 on success.
    """
    sys.stdout.reconfigure(encoding="utf-8")
    config = Config()
    model = load_model(config)
    tables = config.output_dir / "tables"

    q1 = q1_markets.run(model, config)
    write_table(q1.scorecard, tables / "q1_scorecard.csv")
    write_table(q1.quarterly.assign(Quarter=q1.quarterly["Quarter"].astype(str)),
                tables / "q1_quarterly.csv")
    write_table(q1.movers, tables / "q1_movers.csv")
    write_table(q1.robustness, tables / "q1_robustness.csv")
    write_table(q1.bootstrap, tables / "q1_bootstrap.csv")
    write_table(q1.uncertainty, tables / "q1_uncertainty.csv")

    q2 = q2_inventory.run(model, config)
    write_table(q2.watch_list, tables / "q2_watch_list.csv")
    write_table(q2.shortlist, tables / "q2_shortlist.csv")
    write_table(q2.no_reorder_rule, tables / "q2_no_reorder_rule.csv")
    write_table(q2.discontinued_stock, tables / "q2_discontinued_stock.csv")
    write_table(q2.robustness, tables / "q2_robustness.csv")

    q3 = q3_logistics.run(model, config)
    for name, table in q3.breakdowns.items():
        write_table(table.astype({c: str for c in table.columns if c == "Quarter"}),
                    tables / f"q3_by_{name.lower()}.csv")
    for name, table in q3.within_bands.items():
        write_table(table, tables / f"q3_{name.lower()}_within_bands.csv")
    write_table(q3.opportunities, tables / "q3_opportunities.csv")
    write_table(q3.late_by_window, tables / "q3_late_by_window.csv")
    write_table(q3.regression, tables / "q3_regression.csv")
    write_table(q3.robustness, tables / "q3_robustness.csv")
    findings = {"overview": q3.overview, "backlog": q3.backlog, "consolidation": q3.consolidation,
                "deadlines": q3.deadlines, "regression_reason": q3.regression_reason}
    (tables / "q3_findings.json").write_text(json.dumps(findings, indent=2, default=float),
                                             encoding="utf-8")

    checks = run_checks(config, model)
    failed = [c["check"] for c in checks if not c["pass"]]
    figures = charts.all_charts(q1, q2, q3, q3_logistics.shipped_orders(model, config), config)
    input_sha256 = file_sha256(config.workbook)
    context = report.build_context(q1, q2, q3, figures, checks, config, input_sha256)
    page = report.write_site(report.render(context), config.docs_dir)

    manifest = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_sha256": input_sha256,
        "python": sys.version.split()[0],
        "libraries": context["versions"],
        "steps": ["model", "q1", "q2", "q3", "verification", "charts", "report"],
        "sql_crosscheck": {"passed": len(checks) - len(failed), "total": len(checks), "failed": failed},
        "page": str(page.relative_to(config.docs_dir.parent)),
    }
    (config.output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Page written to {page}")
    print(f"SQL cross-check: {len(checks) - len(failed)}/{len(checks)} passed")
    for name in failed:
        print("  FAILED:", name)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
