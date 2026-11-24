"""Apply the cleaning rules from plan.md section 2.3."""

import pandas as pd

# Leftover spreadsheet-exercise columns and empty columns (plan 2.3, rule 3).
JUNK_COLUMNS = {
    "Product": ["Cheap", "Cheap.1", "IsCheap", "NewPrice", "NewPrice.1", "Unnamed: 14"],
    "Categories": ["Picture"],
}

DATE_COLUMNS = {"Orders": ["OrderDate", "RequiredDate", "ShippedDate"]}

DISCOUNT_DECIMALS = 2


def clean_tables(raw):
    """Return cleaned copies of the workbook sheets.

    Drops leftover columns, rounds discounts, parses order dates (missing
    ShippedDate stays missing) and makes Discontinued a boolean. The
    input is not modified.

    Args:
        raw (dict[str, pandas.DataFrame]): Sheets as read from the workbook.

    Returns:
        dict[str, pandas.DataFrame]: Cleaned sheets, keyed by sheet name.
    """
    tables = {name: frame.copy() for name, frame in raw.items()}

    for sheet, columns in JUNK_COLUMNS.items():
        if sheet in tables:
            present = [col for col in columns if col in tables[sheet].columns]
            tables[sheet] = tables[sheet].drop(columns=present)

    details = tables["Orders Details"]
    details["Discount"] = details["Discount"].astype(float).round(DISCOUNT_DECIMALS)

    for sheet, columns in DATE_COLUMNS.items():
        for col in columns:
            tables[sheet][col] = pd.to_datetime(tables[sheet][col])

    tables["Product"]["Discontinued"] = tables["Product"]["Discontinued"].astype(bool)
    return tables
