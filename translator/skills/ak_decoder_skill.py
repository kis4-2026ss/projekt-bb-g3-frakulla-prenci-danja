"""
translator/skills/ak_decoder_skill.py

Post-processor for Arkulcis → English direction.
Runs AFTER AI decodes Arkulcis to raw English.

Handles:
  - Arkulcis number symbols back to decimal (1727707 → 4,782,391)
  - Spoken Arkulcis numbers back to decimal (banbil-nan → 22)
  - Pronoun reverse map (mi→I, pi→she/he/it, pios→they...)
  - Tense marker cleanup ([PAST] etc. if any survive)
  - Suffix stripping hints for the englishifier
"""

import re
from translator.skills.number_skill import (
    from_arkulcis_written,
    from_arkulcis_spoken,
    DIGIT_SYMBOLS,
    DIGIT_WORDS,
)

# ── Pronoun reverse map ─────────────────────────────────────────────
AK_TO_EN_PRONOUN = {
    'mi':   'I',
    'ni':   'you',
    'pi':   'they',   # gender-neutral singular → use they/them in modern English
    'mios': 'we',
    'nios': 'you all',
    'pios': 'they',
}

# ── Arkulcis spoken digit names ──────────────────────────────────────
# Used to detect and convert spoken numbers in decoded text
SPOKEN_MULTIPLIERS = ['gil', 'fil', 'dil', 'bil']


def _is_arkulcis_written_number(token: str) -> bool:
    """Check if a token is a base-12 written symbol (digits + δ + λ)."""
    return bool(re.fullmatch(r'[0-9δλ]+', token)) and len(token) > 0


def _is_arkulcis_spoken_number(token: str) -> bool:
    """Check if a token looks like a spoken Arkulcis number (zan/ban/banbil-nan etc)."""
    digit_names = set(DIGIT_WORDS)
    parts = token.lower().split('-')
    for part in parts:
        # Strip multiplier suffix
        for mult in SPOKEN_MULTIPLIERS:
            if part.endswith(mult):
                part = part[:-len(mult)]
                break
        if part not in digit_names:
            return False
    return len(parts) > 0 and token.lower() not in {'be', 'ban', 'dan'}  # avoid false positives


def convert_written_numbers(text: str) -> str:
    """Convert Arkulcis written symbols back to decimal. Protects time patterns."""
    # Protect time patterns first (H:MM, HH:MM) — same as number_skill
    _times = {}
    def protect_time(m: re.Match) -> str:
        k = f'__T{len(_times)}__'
        _times[k] = m.group(0)
        return k
    text = re.sub(r'\b\d{1,2}:\d{2}\b', protect_time, text)

    def replace(m: re.Match) -> str:
        token = m.group(0)
        if _is_arkulcis_written_number(token):
            try:
                decimal = from_arkulcis_written(token)
                return f'{decimal:,}'
            except Exception:
                return token
        return token
    result = re.sub(r'\b[0-9δλ]+\b', replace, text)

    # Restore times
    for k, v in _times.items():
        result = result.replace(k, v)
    return result


def convert_spoken_numbers(text: str) -> str:
    """Convert Arkulcis spoken number words back to decimal.
    Handles consecutive spoken tokens (split large numbers) by summing adjacent results."""
    # All multiplier suffixes: bil(x12) dil(x144) fil(x1728) gil(x20736) hil jil kil lil mil nil
    MULTS = r'(?:nil|mil|lil|kil|jil|hil|gil|fil|dil|bil)'
    DIGIT = r'(?:zan|ban|dan|fan|gan|han|jan|kan|lan|man|nan|pan)'
    spoken_pattern = (
        r'\b' + DIGIT +
        r'(?:' + MULTS + r'(?:-' + DIGIT + r'(?:' + MULTS + r')?)*)*\b'
    )
    def replace(m: re.Match) -> str:
        token = m.group(0)
        try:
            decimal = from_arkulcis_spoken(token)
            return f'__NUM{decimal}__'
        except Exception:
            return token
    result = re.sub(spoken_pattern, replace, text, flags=re.IGNORECASE)

    # Merge adjacent __NUMx__ __NUMy__ tokens that represent one split number
    # e.g. __NUM987654300__ __NUM21__ → 987,654,321
    def merge(m: re.Match) -> str:
        a, b = int(m.group(1)), int(m.group(2))
        # Only merge if b is much smaller than a (it's a remainder, not a new number)
        if b < a and b < 10_000_000:
            return f'{a + b:,}'
        return f'{a:,} {b:,}'
    result = re.sub(r'__NUM(\d+)__\s+__NUM(\d+)__', merge, result)

    # Format any remaining single markers
    result = re.sub(r'__NUM(\d+)__', lambda m: f'{int(m.group(1)):,}', result)
    return result


def restore_pronouns(text: str) -> str:
    """Replace Arkulcis pronouns with English equivalents."""
    def replace(m: re.Match) -> str:
        word = m.group(0).lower()
        if word in AK_TO_EN_PRONOUN:
            en = AK_TO_EN_PRONOUN[word]
            # Preserve capitalisation if at start of sentence
            if m.start() == 0 or text[m.start()-2:m.start()] in ('. ', '? ', '! '):
                return en.capitalize()
            return en
        return m.group(0)
    return re.sub(r'\b(mi|ni|pi|mios|nios|pios)\b', replace, text, flags=re.IGNORECASE)


def apply(text: str) -> str:
    """
    Full AK→EN post-processor pipeline:
      1. Convert written Arkulcis numbers back to decimal
      2. Convert spoken Arkulcis numbers back to decimal  
      3. Restore Arkulcis pronouns to English
    """
    text = convert_written_numbers(text)
    text = convert_spoken_numbers(text)
    text = restore_pronouns(text)
    return text


if __name__ == '__main__':
    tests = [
        'goed pi to librari',
        'wondered mi whether ni maked decision',
        'losed kompani 1727707 dolars',
        'drived mi thru kountrisaid at 71 km/h',
        'beas pi leading teim sins 1205',
    ]
    for t in tests:
        print(f'IN:  {t}')
        print(f'OUT: {apply(t)}')
        print()
