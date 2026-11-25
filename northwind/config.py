"""Paths, dates, thresholds and region maps used by every analysis step."""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

FOCUS_MARKETS = ("USA", "Germany", "Brazil", "France")

# Q1 markets: the four focus countries stand alone, the rest are grouped.
MARKET_GROUPS = {
    "USA": "USA",
    "Germany": "Germany",
    "Brazil": "Brazil",
    "France": "France",
    "UK": "UK & Ireland",
    "Ireland": "UK & Ireland",
    "Sweden": "Nordics",
    "Denmark": "Nordics",
    "Finland": "Nordics",
    "Norway": "Nordics",
    "Austria": "Central Europe",
    "Switzerland": "Central Europe",
    "Belgium": "Central Europe",
    "Poland": "Central Europe",
    "Spain": "Southern Europe",
    "Italy": "Southern Europe",
    "Portugal": "Southern Europe",
    "Canada": "Other North America",
    "Mexico": "Other North America",
    "Venezuela": "Other South America",
    "Argentina": "Other South America",
}

# Q3 destination regions: fewer, larger groups for freight comparisons.
DEST_REGIONS = {
    "USA": "North America",
    "Canada": "North America",
    "Mexico": "North America",
    "Brazil": "South America",
    "Venezuela": "South America",
    "Argentina": "South America",
    "Germany": "Western Europe",
    "France": "Western Europe",
    "Belgium": "Western Europe",
    "Switzerland": "Western Europe",
    "Austria": "Western Europe",
    "UK": "UK & Ireland",
    "Ireland": "UK & Ireland",
    "Sweden": "Nordics",
    "Denmark": "Nordics",
    "Finland": "Nordics",
    "Norway": "Nordics",
    "Spain": "Southern & Eastern Europe",
    "Italy": "Southern & Eastern Europe",
    "Portugal": "Southern & Eastern Europe",
    "Poland": "Southern & Eastern Europe",
}

# Known totals for the real workbook; integration tests and the SQL
# cross-check fail if the model does not reproduce them.
CONTROL_TOTALS = {
    "order_lines": 2155,
    "orders": 830,
    "orders_shipped": 809,
    "orders_unshipped": 21,
    "orders_late": 37,
    "customers_with_orders": 89,
    "products": 77,
    "active_products": 69,
    "active_without_reorder_rule": 16,
    "net_revenue": 1_265_793,
    "gross_revenue": 1_354_459,
}


@dataclass(frozen=True)
class Config:
    """Settings for one analysis run.

    Attributes:
        workbook (pathlib.Path): Input Excel workbook.
        output_dir (pathlib.Path): Folder for generated tables and
            manifest.
        docs_dir (pathlib.Path): Folder served by GitHub Pages.
        cutoff (pandas.Timestamp): Last order date; all recent windows
            end here.
        first_full_quarter (str): First complete calendar quarter.
        last_full_quarter (str): Last complete calendar quarter.
        current_window (tuple[str, ...]): Quarters in the Q1 growth
            window.
        prior_window (tuple[str, ...]): Same quarters one year earlier.
        outperform_threshold (float): Relative growth at or above which
            a market is Outperforming.
        underperform_threshold (float): Relative growth at or below
            which a market is Underperforming.
        concentration_threshold (float): Largest-customer share above
            which concentration risk is High.
        concentration_flag_margin (float): Dependence within this
            distance of the threshold is flagged as near the line.
        narrow_growth_share (float): One account supplying more than
            this share of a market's increase is flagged as narrow
            growth.
        min_orders_per_window (int): Fewer orders than this in either
            window gives "Insufficient data".
        near_threshold_margin (float): Relative growth this close to a
            performance threshold triggers the bootstrap check (plan
            4.4).
        bootstrap_resamples (int): Resamples for the bootstrap check.
        bootstrap_interval (float): Width of the bootstrap interval.
        movers_per_side (int): Gaining and losing accounts listed per
            market.
        demand_window_days (int): Length of the recent-demand window.
        days_per_month (float): Days used to convert to monthly rates.
        acceleration_ratio (float): Recent/long-run demand ratio above
            which demand counts as speeding up.
        demand_months (tuple[str, str]): First and last full month used
            for demand variability.
        critical_cover (float): Months of cover (incl. on order) below
            which a product is Critical.
        high_cover (float): Months of on-hand cover below which a
            product can be High.
        watch_cover (float): Months of on-hand cover used by Watch
            rules.
        high_variability (float): Coefficient of variation above which
            demand counts as erratic.
        lead_time_scenarios (tuple[float, ...]): Assumed lead times in
            months for suggested reorder levels.
        shortlist_size (int): Products shown on the main page for Q2.
        buy_list_size (int): Products listed with order quantities.
        slow_quantile (float): Quantile of processing days that defines
            a slow order.
        consolidation_share (float): Freight share of revenue above
            which a small order is a consolidation candidate.
        min_group_orders_per_band (int): Orders a group needs in a size
            band to serve as that band's benchmark.
        min_opportunity_orders (int): Opportunities resting on fewer
            orders get a bootstrap check (plan 4.4).
        region_mix_tolerance (float): Largest acceptable gap between
            carriers' destination shares before the regression check
            runs.
        freight_materiality (float): Carrier freight difference that
            counts as material.
        dispatch_materiality_days (float): Carrier dispatch difference
            that counts as material.
        freight_outlier_quantile (float): Freight above this quantile is
            dropped in the robustness check.
        seed (int): Random seed for any resampling.
        repo_url (str | None): Public repository link shown on the page;
            None until the repository exists (gate 7).
        focus_markets (tuple[str, ...]): Markets analysed individually.
        market_groups (dict[str, str]): Country to Q1 market.
        dest_regions (dict[str, str]): Country to Q3 destination region.
    """

    workbook: Path = ROOT / "data" / "Northwind Database.xlsx"
    output_dir: Path = ROOT / "outputs"
    docs_dir: Path = ROOT / "docs"
    cutoff: pd.Timestamp = pd.Timestamp("1998-05-06")
    first_full_quarter: str = "1996Q3"
    last_full_quarter: str = "1998Q1"
    current_window: tuple[str, ...] = ("1997Q4", "1998Q1")
    prior_window: tuple[str, ...] = ("1996Q4", "1997Q1")
    outperform_threshold: float = 0.15
    underperform_threshold: float = -0.10
    concentration_threshold: float = 0.50
    concentration_flag_margin: float = 0.05
    narrow_growth_share: float = 0.60
    min_orders_per_window: int = 8
    near_threshold_margin: float = 0.05
    bootstrap_resamples: int = 2000
    bootstrap_interval: float = 0.90
    movers_per_side: int = 3
    demand_window_days: int = 90
    days_per_month: float = 30.44
    acceleration_ratio: float = 1.25
    demand_months: tuple[str, str] = ("1996-07", "1998-04")
    critical_cover: float = 0.5
    high_cover: float = 1.0
    watch_cover: float = 1.5
    high_variability: float = 1.5
    lead_time_scenarios: tuple[float, ...] = (0.5, 1.0, 2.0)
    shortlist_size: int = 10
    buy_list_size: int = 5
    slow_quantile: float = 0.90
    consolidation_share: float = 0.15
    min_group_orders_per_band: int = 10
    min_opportunity_orders: int = 30
    region_mix_tolerance: float = 0.10
    freight_materiality: float = 0.10
    dispatch_materiality_days: float = 1.0
    freight_outlier_quantile: float = 0.99
    seed: int = 561
    repo_url: str | None = "https://github.com/alamergt/northwind-analysis"
    focus_markets: tuple[str, ...] = FOCUS_MARKETS
    market_groups: dict = field(default_factory=lambda: dict(MARKET_GROUPS))
    dest_regions: dict = field(default_factory=lambda: dict(DEST_REGIONS))
