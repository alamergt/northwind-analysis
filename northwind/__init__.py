"""Northwind business analysis: data loading, metrics and reporting."""

from northwind.clean import clean_tables
from northwind.config import Config
from northwind.load import load_workbook
from northwind.model import Model, build_model


def load_model(config=None):
    """Load, clean and join the workbook in one call.

    Args:
        config (northwind.config.Config | None): Settings; None uses the
            defaults.

    Returns:
        northwind.model.Model: Analysis-ready tables.
    """
    config = config or Config()
    return build_model(clean_tables(load_workbook(config.workbook)), config)


__all__ = ["Config", "Model", "build_model", "clean_tables", "load_model", "load_workbook"]
