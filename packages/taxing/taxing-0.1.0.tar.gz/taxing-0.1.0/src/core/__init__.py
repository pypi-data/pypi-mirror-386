from src.core.classify import classify
from src.core.deduce import deduce
from src.core.models import Gain, Trade, Transaction
from src.core.rules import dedupe_keywords, load_rules
from src.core.trades import process_trades

__all__ = [
    "classify",
    "deduce",
    "dedupe_keywords",
    "load_rules",
    "process_trades",
    "Trade",
    "Gain",
    "Transaction",
]
