"""Property expense aggregation."""

from decimal import Decimal

from src.core.models import PropertyExpense, PropertyExpensesSummary


def aggregate_expenses(expenses: list[PropertyExpense]) -> PropertyExpensesSummary:
    """Aggregate property expenses by type.

    Args:
        expenses: List of PropertyExpense records

    Returns:
        PropertyExpensesSummary with totals per category
    """
    totals = {
        "rent": Decimal("0"),
        "water": Decimal("0"),
        "council": Decimal("0"),
        "strata": Decimal("0"),
    }

    for exp in expenses:
        if exp.expense_type in totals:
            totals[exp.expense_type] += exp.amount

    return PropertyExpensesSummary(
        rent=totals["rent"],
        water=totals["water"],
        council=totals["council"],
        strata=totals["strata"],
    )
