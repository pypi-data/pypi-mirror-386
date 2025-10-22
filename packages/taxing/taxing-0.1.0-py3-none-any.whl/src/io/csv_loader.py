from dataclasses import fields
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


def load_csv(path: Path, model_class: type[T], fy: int) -> list[T]:
    """Load CSV into list of dataclass instances.

    CSV columns must match dataclass field names.
    Special handling for:
    - date: parsed from YYYY-MM-DD format
    - Decimal: created from a numeric string
    - fy: injected if not in CSV
    """
    if not path.exists():
        return []

    items = []
    try:
        with open(path) as f:
            lines = [
                line.strip() for line in f if line.strip() and not line.strip().startswith("#")
            ]
            if not lines:
                return []

            header = lines[0].split(",")
            header = [h.strip() for h in header]

            for line in lines[1:]:
                values = line.split(",")
                values = [v.strip() for v in values]

                if len(values) != len(header):
                    continue

                row = {header[i]: values[i] for i in range(len(header))}

                try:
                    parsed = _parse_row(row, model_class, fy)
                    items.append(parsed)
                except (ValueError, TypeError, KeyError):
                    pass

    except Exception:
        pass

    return items


def _parse_row(row: dict, model_class: type[T], fy: int) -> T:
    """Parse CSV row into dataclass instance."""
    kwargs = {}

    for field in fields(model_class):
        if field.name == "fy":
            kwargs["fy"] = fy
            continue

        if field.name not in row and field.name != "fy":
            if field.default is not None:
                kwargs[field.name] = field.default
            elif field.default_factory is not None:
                kwargs[field.name] = field.default_factory()
            continue

        value = row.get(field.name, "")

        if field.type is date:
            kwargs[field.name] = date.fromisoformat(value)
        elif field.type is Decimal:
            kwargs[field.name] = Decimal(value)
        elif field.type is int:
            kwargs[field.name] = int(value)
        else:
            kwargs[field.name] = value

    return model_class(**kwargs)
