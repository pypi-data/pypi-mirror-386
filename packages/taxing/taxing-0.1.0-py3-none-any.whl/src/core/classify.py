def classify(description: str, rules: dict[str, list[str]]) -> set[str]:
    """
    Classify a transaction description against rules.

    Args:
        description: Transaction description string
        rules: Dict mapping category -> list of keywords

    Returns:
        Set of matching categories (empty if no matches)
    """
    desc_upper = description.strip().upper()
    matches = set()

    for category, keywords in rules.items():
        for keyword in keywords:
            if keyword.upper() in desc_upper:
                matches.add(category)
                break

    return matches
