"""
LABBAIK AI - Name Normalization Service
=======================================
Arabic/Latin transliteration and hotel name matching.
"""

import re
import unicodedata
from typing import List, Set, Optional, Tuple
from difflib import SequenceMatcher


# Arabic diacritics (tashkil) - to be removed
ARABIC_DIACRITICS = re.compile(r'[\u064B-\u065F\u0670]')

# Non-alphanumeric (keep spaces)
NON_ALNUM = re.compile(r'[^a-z0-9\s]')

# Arabic to Latin transliteration map
ARABIC_TO_LATIN = {
    # Letters
    'ا': 'a', 'أ': 'a', 'إ': 'i', 'آ': 'aa',
    'ب': 'b', 'ت': 't', 'ث': 'th',
    'ج': 'j', 'ح': 'h', 'خ': 'kh',
    'د': 'd', 'ذ': 'dh',
    'ر': 'r', 'ز': 'z',
    'س': 's', 'ش': 'sh',
    'ص': 's', 'ض': 'd',
    'ط': 't', 'ظ': 'z',
    'ع': 'a', 'غ': 'gh',
    'ف': 'f', 'ق': 'q',
    'ك': 'k', 'ل': 'l',
    'م': 'm', 'ن': 'n',
    'ه': 'h', 'و': 'w',
    'ي': 'y', 'ى': 'a',
    'ة': 'h', 'ء': 'a',
    'ؤ': 'w', 'ئ': 'y',
    # Numbers
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
}

# Common replacements for normalization
COMMON_REPLACEMENTS = [
    # Articles
    ("al ", ""), ("el ", ""), ("the ", ""),
    ("al-", ""), ("el-", ""),
    # City names
    ("makkah", "mecca"), ("mekkah", "mecca"), ("mekah", "mecca"),
    ("madinah", "medina"), ("medinah", "medina"), ("madinah al munawwarah", "medina"),
    ("jeddah", "jeddah"), ("jedda", "jeddah"),
    # Common terms to remove
    ("masjid", ""), ("haram", ""), ("nabawi", ""),
    ("hotel", ""), ("resort", ""), ("suites", "suite"),
    ("tower", ""), ("towers", ""),
    # Connectors
    ("and", ""), ("&", " "), ("'s", ""),
]

# Pre-compiled single-pass replacement (avoids 13+ sequential .replace() calls)
_REPLACEMENT_DICT = dict(COMMON_REPLACEMENTS)
_REPLACEMENT_RE = re.compile(
    "|".join(re.escape(old) for old, _ in COMMON_REPLACEMENTS)
)

# Hotel chain aliases
HOTEL_CHAINS = {
    "hilton": ["hilton", "doubletree", "embassy suites", "hampton", "waldorf"],
    "marriott": ["marriott", "sheraton", "westin", "ritz carlton", "courtyard", "jw"],
    "accor": ["accor", "sofitel", "pullman", "novotel", "ibis", "mercure", "swissotel"],
    "ihg": ["ihg", "intercontinental", "crowne plaza", "holiday inn", "indigo"],
    "hyatt": ["hyatt", "grand hyatt", "park hyatt", "andaz"],
    "rotana": ["rotana", "rayhaan", "arjaan"],
    "raffles": ["raffles", "fairmont"],
}


def transliterate_arabic(text: str) -> str:
    """Convert Arabic text to Latin characters."""
    if not text:
        return ""

    result = []
    for char in text:
        if char in ARABIC_TO_LATIN:
            result.append(ARABIC_TO_LATIN[char])
        else:
            result.append(char)

    return ''.join(result)


def normalize_name(name: str) -> str:
    """
    Normalize hotel/location name for matching.

    Steps:
    1. Lowercase
    2. Remove Arabic diacritics
    3. Transliterate Arabic to Latin
    4. Apply common replacements
    5. Remove non-alphanumeric (keep spaces)
    6. Collapse whitespace

    Args:
        name: Original name (Arabic or Latin)

    Returns:
        Normalized name for matching
    """
    if not name:
        return ""

    # Lowercase and strip
    s = name.strip().lower()

    # Remove Arabic diacritics
    s = ARABIC_DIACRITICS.sub("", s)

    # Transliterate Arabic
    s = transliterate_arabic(s)

    # Normalize unicode
    s = unicodedata.normalize('NFKD', s)
    s = s.encode('ascii', 'ignore').decode('ascii')

    # Clean up quotes
    s = s.replace("'", "'").replace("`", "'").replace("'", "")
    s = s.replace('"', '')

    # Apply common replacements (single-pass regex)
    s = _REPLACEMENT_RE.sub(lambda m: _REPLACEMENT_DICT[m.group()], s)

    # Remove non-alphanumeric
    s = NON_ALNUM.sub(" ", s)

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s


def alt_forms(name: str) -> List[str]:
    """
    Generate alternative forms of a name for matching.

    Args:
        name: Original name

    Returns:
        List of alternative normalized forms
    """
    base = normalize_name(name)
    if not base:
        return []

    variants: Set[str] = set()

    # Base form
    variants.add(base)

    # No spaces
    variants.add(base.replace(" ", ""))

    # Hyphenated
    variants.add(base.replace(" ", "-"))

    # First word only (brand)
    words = base.split()
    if words:
        variants.add(words[0])

    # First two words
    if len(words) >= 2:
        variants.add(" ".join(words[:2]))

    # Without numbers
    no_nums = re.sub(r'\d+', '', base).strip()
    if no_nums:
        variants.add(no_nums)

    return [v for v in variants if v and len(v) > 2]


def similarity_score(name1: str, name2: str) -> float:
    """
    Calculate similarity score between two names.

    Args:
        name1: First name
        name2: Second name

    Returns:
        Similarity score 0.0 to 1.0
    """
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)

    if not n1 or not n2:
        return 0.0

    # Exact match
    if n1 == n2:
        return 1.0

    # One contains the other
    if n1 in n2 or n2 in n1:
        return 0.9

    # Sequence matcher
    return SequenceMatcher(None, n1, n2).ratio()


def match_hotel_name(
    query: str,
    candidates: List[str],
    threshold: float = 0.7
) -> List[Tuple[str, float]]:
    """
    Find matching hotel names from candidates.

    Args:
        query: Search query
        candidates: List of hotel names to search
        threshold: Minimum similarity score (0.0-1.0)

    Returns:
        List of (name, score) tuples, sorted by score desc
    """
    query_norm = normalize_name(query)
    query_alts = set(alt_forms(query))

    results = []

    for candidate in candidates:
        cand_norm = normalize_name(candidate)
        cand_alts = set(alt_forms(candidate))

        # Check for alt form matches
        if query_alts & cand_alts:
            results.append((candidate, 0.95))
            continue

        # Calculate similarity
        score = similarity_score(query, candidate)

        if score >= threshold:
            results.append((candidate, score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)

    return results


def identify_hotel_chain(name: str) -> Optional[str]:
    """
    Identify hotel chain from name.

    Args:
        name: Hotel name

    Returns:
        Chain name or None
    """
    name_lower = name.lower()

    for chain, aliases in HOTEL_CHAINS.items():
        for alias in aliases:
            if alias in name_lower:
                return chain

    return None


def extract_star_rating(name: str) -> Optional[int]:
    """
    Extract star rating from hotel name if present.

    Args:
        name: Hotel name

    Returns:
        Star rating (1-5) or None
    """
    # Pattern: "5 star", "5-star", "5*"
    patterns = [
        r'(\d)\s*star',
        r'(\d)-star',
        r'(\d)\*',
        r'bintang\s*(\d)',
    ]

    for pattern in patterns:
        match = re.search(pattern, name.lower())
        if match:
            rating = int(match.group(1))
            if 1 <= rating <= 5:
                return rating

    return None


# Convenience functions for common use cases
def normalize_city(city: str) -> str:
    """Normalize city name."""
    city_map = {
        "makkah": "MAKKAH",
        "mecca": "MAKKAH",
        "mekkah": "MAKKAH",
        "mekah": "MAKKAH",
        "madinah": "MADINAH",
        "medina": "MADINAH",
        "medinah": "MADINAH",
        "jeddah": "JEDDAH",
        "jedda": "JEDDAH",
        "jidda": "JEDDAH",
    }

    normalized = city.lower().strip()
    return city_map.get(normalized, city.upper())


def format_hotel_display_name(name: str, city: str = None) -> str:
    """
    Format hotel name for display.

    Args:
        name: Raw hotel name
        city: Optional city to append

    Returns:
        Formatted display name
    """
    # Title case
    display = name.strip().title()

    # Fix common title case issues
    replacements = [
        ("'S", "'s"),
        (" And ", " and "),
        (" Of ", " of "),
        (" The ", " the "),
        ("Al ", "Al-"),
    ]

    for old, new in replacements:
        display = display.replace(old, new)

    # Add city if provided
    if city:
        city_norm = normalize_city(city)
        if city_norm not in display.upper():
            display = f"{display}, {city_norm.title()}"

    return display
