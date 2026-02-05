import re

BLOCKLIST_PATTERNS = [
    r"tweet|#\s*tweets",  # Tweet counts
    r"(bitcoin|solana|ethereum).*\$.*on\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",  # Daily crypto
    r"what price will.*(bitcoin|solana|ethereum).*hit",  # Monthly crypto price
    r"\bbo[35]\b|\blpl\b|\blcs\b|\blec\b|\bvalorant\b|\blol:",  # Esports
]

MIN_VOLUME_24H = 250000
RESOLVED_UPPER = 0.95
RESOLVED_LOWER = 0.05


def is_blocklisted(question: str) -> bool:
    """Check if a market question matches any blocklist pattern."""
    question_lower = question.lower()
    for pattern in BLOCKLIST_PATTERNS:
        if re.search(pattern, question_lower):
            return True
    return False


def passes_thresholds(probability: float, volume_24h: float) -> bool:
    """Check if market passes volume and resolution thresholds."""
    if volume_24h < MIN_VOLUME_24H:
        return False
    if probability > RESOLVED_UPPER or probability < RESOLVED_LOWER:
        return False
    return True
