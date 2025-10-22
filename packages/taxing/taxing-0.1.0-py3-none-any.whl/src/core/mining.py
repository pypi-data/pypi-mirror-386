from dataclasses import dataclass
from pathlib import Path

from src.core.models import Transaction
from src.lib.search import extract_search_categories, load_cache, search_merchant


@dataclass(frozen=True)
class RuleSuggestion:
    """Suggested rule with evidence."""

    keyword: str
    category: str
    evidence: int
    source: str
    unlabeled_desc: str
    total_category_evidence: int = 0


@dataclass(frozen=True)
class MiningConfig:
    """Configuration for rule mining and scoring."""

    dominance: float = 0.6
    threshold: int = 10
    min_unlabeled_coverage: int = 1
    min_keyword_len: int = 3
    keyword_length_bonus: int = 5


GENERIC_WORDS = {
    "fast",
    "transfer",
    "from",
    "credit",
    "account",
    "card",
    "value",
    "date",
    "aus",
    "payment",
    "bank",
    "wise",
    "direct",
    "dispatch",
    "app",
    "reverse",
    "jpy",
    "eur",
    "cny",
    "sgd",
    "usd",
    "gbp",
    "in",
    "to",
    "at",
    "ltd",
    "pty",
    "aust",
    "inc",
    "co",
}


def extract_keywords(desc: str, min_len: int = 3) -> list[str]:
    """Extract candidate keywords from description (alphanumeric, min length)."""
    words = desc.lower().split()
    cleaned = [w.strip(".,!?;:") for w in words if len(w.strip(".,!?;:")) >= min_len]
    return [w for w in cleaned if not w.isdigit()]


def find_similar_labeled(txns: list[Transaction], unlabeled_desc: str) -> list[Transaction]:
    """Find categorized txns with keyword overlap to unlabeled desc."""
    keywords = extract_keywords(unlabeled_desc)
    if not keywords:
        return []

    similar = []
    for txn in txns:
        if txn.category is None or not txn.category:
            continue

        desc_upper = txn.description.upper()
        for kw in keywords:
            if kw.upper() in desc_upper:
                similar.append(txn)
                break

    return similar


def mine_suggestions(
    txns: list[Transaction],
    use_search: bool = False,
    cache_path: Path | None = None,
) -> list[RuleSuggestion]:
    """Mine keyword-category suggestions from similar labeled transactions.

    For each unlabeled txn, find similar labeled txns and extract keywords
    that map to categories. Optionally enhance with merchant search via DDGS.

    Args:
        txns: All transactions (labeled + unlabeled)
        use_search: Enable DDGS merchant search for orphan txns
        cache_path: Path to search cache file
    """
    unlabeled = [t for t in txns if t.category is None or not t.category]
    labeled = [t for t in txns if t.category is not None and t.category]

    if not unlabeled or not labeled:
        return []

    suggestions = []
    cache = load_cache(cache_path) if use_search and cache_path else {}

    for unlabeled_txn in unlabeled:
        desc = unlabeled_txn.description
        similar = find_similar_labeled(labeled, desc)

        if similar:
            keywords = extract_keywords(desc)
            for kw in keywords:
                for labeled_txn in similar:
                    desc_upper = labeled_txn.description.upper()
                    if kw.upper() in desc_upper:
                        for cat in labeled_txn.category:
                            suggestions.append(
                                RuleSuggestion(
                                    keyword=kw,
                                    category=cat,
                                    evidence=1,
                                    source="keyword",
                                    unlabeled_desc=desc[:60],
                                )
                            )
        elif use_search and cache_path:
            merchant = desc.split()[0] if desc else ""
            if merchant:
                snippets = search_merchant(merchant, cache, cache_path)
                hints = extract_search_categories(snippets)
                for hint in hints:
                    suggestions.append(
                        RuleSuggestion(
                            keyword=merchant,
                            category=hint,
                            evidence=1,
                            source="search",
                            unlabeled_desc=desc[:60],
                        )
                    )

    return suggestions


def score_suggestions(
    suggestions: list[RuleSuggestion],
    config: MiningConfig | None = None,
) -> list[RuleSuggestion]:
    """Score and filter suggestions by dominance and threshold.

    Args:
        suggestions: Raw suggestions from mine_suggestions()
        config: MiningConfig with thresholds (uses defaults if None)

    Returns:
        Filtered, scored suggestions ranked by evidence
    """
    if not suggestions:
        return []

    cfg = config or MiningConfig()

    filtered_suggestions = [s for s in suggestions if s.keyword.lower() not in GENERIC_WORDS]
    if not filtered_suggestions:
        return []

    keyword_cat_evidence = {}
    for s in filtered_suggestions:
        key = (s.keyword, s.category)
        if key not in keyword_cat_evidence:
            keyword_cat_evidence[key] = 0
        keyword_cat_evidence[key] += s.evidence

    scored = []
    for (kw, cat), total_ev in keyword_cat_evidence.items():
        scored.append(
            RuleSuggestion(
                keyword=kw,
                category=cat,
                evidence=total_ev,
                source="keyword",
                unlabeled_desc="",
                total_category_evidence=total_ev,
            )
        )

    filtered = []
    for kw in {s.keyword for s in scored}:
        kw_rules = [s for s in scored if s.keyword == kw]
        total_ev = sum(s.evidence for s in kw_rules)

        dominant = max(kw_rules, key=lambda s: s.evidence)

        if dominant.evidence >= cfg.threshold and dominant.evidence / total_ev >= cfg.dominance:
            filtered.append(dominant)

    return sorted(filtered, key=lambda s: s.evidence, reverse=True)
