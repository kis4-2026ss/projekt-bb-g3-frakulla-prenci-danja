"""
arkulcis/translator/skills/number_skill.py

Skill 1 — Number conversion pipeline:
  1. Parse English written numbers ("twenty-two", "one hundred and forty-four")
  2. Convert decimal integers (99, 144)
  3. Convert to Arkulcis base-12 notation
     Digits 0-9 use: zan ban dan fan gan han jan kan lan man
     Digit 10 = δ (delta)  — nan in spoken Arkulcis
     Digit 11 = λ (lambda) — pan in spoken Arkulcis

Written symbols:
  0-9  → zan ban dan fan gan han jan kan lan man
  10   → δ   (spoken: nan)
  11   → λ   (spoken: pan)
  12   → banbil
  99   → lanbil-man (8×12 + 3... wait: lanbil-fan)

Multipliers (spoken + written same):
  -bil = ×12  |  -dil = ×144  |  -fil = ×1728  |  -gil = ×20736
"""

import re
from typing import Optional

# ── Digit system ──────────────────────────────────────────────────────────
DIGIT_WORDS   = ['zan','ban','dan','fan','gan','han','jan','kan','lan','man','nan','pan']
DIGIT_SYMBOLS = ['0','1','2','3','4','5','6','7','8','9','δ','λ']

# Special spoken names for 10 and 11
DIGIT_SPOKEN  = {
    10: 'nan',   # δ spoken as "nan"
    11: 'pan',   # λ spoken as "pan"
}

MULTIPLIER_SUFFIXES = ['bil','dil','fil','gil','hil','jil','kil','lil','mil','nil']

# ── English word → integer ────────────────────────────────────────────────
ONES = {
    'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,
    'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,
    'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,
    'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,
    'thirty':30,'forty':40,'fifty':50,'sixty':60,'seventy':70,
    'eighty':80,'ninety':90,
    # common shorthand
    'a dozen':12,'dozen':12,'a score':20,'score':20,
    'a gross':144,'gross':144,
    'a hundred':100,'a thousand':1000,'a million':1000000,
}
MAGNITUDES = {
    'hundred':100,'thousand':1000,'million':1000000,
    'billion':1000000000,'trillion':1000000000000,
}


def words_to_int(text: str) -> Optional[int]:
    """
    Convert an English number phrase to an integer.
    Returns None if the text is not a recognisable number.
    Examples:
        "twenty-two"              → 22
        "one hundred and forty-four" → 144
        "a dozen"                 → 12
        "three thousand"          → 3000
    """
    text = text.lower().strip()
    text = re.sub(r'\band\b', ' ', text)
    text = re.sub(r'[-\u2013]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Direct lookup first
    if text in ONES:
        return ONES[text]

    words = text.split()
    current = 0
    result  = 0
    i = 0
    while i < len(words):
        w = words[i]
        if w in ONES:
            current += ONES[w]
        elif w in MAGNITUDES:
            mag = MAGNITUDES[w]
            if mag == 100:
                current *= 100
            else:
                if current == 0:
                    current = 1
                result  += current * mag
                current  = 0
        else:
            return None
        i += 1

    total = result + current
    return total if total > 0 or text in ('zero','0') else None


# ── Integer → base-12 digits list ────────────────────────────────────────
def to_base12_digits(n: int) -> list[int]:
    if n == 0:
        return [0]
    digits = []
    while n > 0:
        digits.insert(0, n % 12)
        n //= 12
    return digits


# ── Integer → Arkulcis spoken word ───────────────────────────────────────
def to_arkulcis_spoken(n: int, hyphen: bool = True) -> str:
    """
    Convert integer to Arkulcis spoken number word.
    Uses digit words (zan, ban, ... nan, pan) + multiplier suffixes.
    Examples:
        0  → zan
        10 → nan
        11 → pan
        12 → banbil
        99 → lanbil-fan
    """
    if n < 0:
        raise ValueError('Arkulcis numbers must be non-negative.')
    if n == 0:
        return 'zan'

    digits = to_base12_digits(n)
    length = len(digits)
    parts  = []

    for i, digit in enumerate(digits):
        if digit == 0:
            continue
        power      = length - 1 - i
        digit_word = DIGIT_WORDS[digit]
        if power == 0:
            parts.append(digit_word)
        else:
            suffix = MULTIPLIER_SUFFIXES[power - 1]
            parts.append(digit_word + suffix)

    sep = '-' if hyphen else ''
    return sep.join(parts)


# ── Integer → Arkulcis written symbol string ─────────────────────────────
def to_arkulcis_written(n: int) -> str:
    """
    Convert integer to Arkulcis written symbol notation.
    Uses 0-9 for digits 0-9, δ for 10, λ for 11.
    Examples:
        10  → δ
        11  → λ
        12  → 10  (1×12 + 0)
        22  → 1δ  (1×12 + 10)
        144 → 100 (1×144)
        155 → 10λ (1×144 + 0×12 + 11)
    """
    if n < 0:
        raise ValueError('Arkulcis numbers must be non-negative.')
    digits = to_base12_digits(n)
    return ''.join(DIGIT_SYMBOLS[d] for d in digits)


# ── Reverse: written symbol → integer ────────────────────────────────────
def from_arkulcis_written(sym: str) -> int:
    """Convert Arkulcis written notation back to decimal integer."""
    sym_to_val = {s: i for i, s in enumerate(DIGIT_SYMBOLS)}
    total = 0
    for ch in sym:
        if ch not in sym_to_val:
            raise ValueError(f'Unknown Arkulcis digit symbol: {ch!r}')
        total = total * 12 + sym_to_val[ch]
    return total


# ── Reverse: spoken word → integer ───────────────────────────────────────
def from_arkulcis_spoken(word: str) -> int:
    """Parse Arkulcis spoken number word back to decimal integer."""
    word  = word.strip().lower().replace('-', '')
    d_map = {d: i for i, d in enumerate(DIGIT_WORDS)}
    m_map = {s: 12**(i+1) for i, s in enumerate(MULTIPLIER_SUFFIXES)}

    if word in d_map:
        return d_map[word]

    total = 0
    i     = 0
    while i < len(word):
        matched = False
        for dig in sorted(DIGIT_WORDS[1:], key=len, reverse=True):
            for suf in sorted(m_map.keys(), key=len, reverse=True):
                chunk = dig + suf
                if word[i:].startswith(chunk):
                    total   += DIGIT_WORDS.index(dig) * m_map[suf]
                    i       += len(chunk)
                    matched  = True
                    break
            if matched:
                break
        if not matched:
            for dig in sorted(DIGIT_WORDS, key=len, reverse=True):
                if word[i:].startswith(dig):
                    total   += DIGIT_WORDS.index(dig)
                    i       += len(dig)
                    matched  = True
                    break
        if not matched:
            raise ValueError(f'Cannot parse Arkulcis number: {word!r} at pos {i}')
    return total


# ── Main skill: apply to text ─────────────────────────────────────────────
# Ordered from longest to shortest to avoid partial matches
# Patterns ordered longest/most-specific first to avoid partial matches
_ONES_PAT  = r'(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)'
_TENS_PAT  = r'(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)'
_COMP_PAT  = rf'(?:{_TENS_PAT}(?:[\s-]{_ONES_PAT})?|{_ONES_PAT})'
_MAG_PAT   = r'(?:hundred|thousand|million|billion)'

_WRITTEN_NUMBER_PATTERNS = [
    # Full complex: "one hundred and forty-four", "three thousand and twelve"
    rf'\b{_COMP_PAT}(?:\s+{_MAG_PAT}(?:\s+and\s+{_COMP_PAT})?)*\b',
    # "a dozen / a gross / a score"
    r'\b(?:a\s+(?:dozen|gross|hundred|thousand|million|score))\b',
    # standalone shorthands
    r'\b(?:dozen|gross|score)\b',
]


def apply(text: str) -> str:
    """
    Convert all numbers in text to Arkulcis notation.
    Numbers are wrapped in [NUM:...] tags so the AI knows to copy them verbatim.
    Call strip_num_tags() on the AI output to remove the tags.

    Two modes:
      Digit form   (3232)                   → written symbols  (1δ54)
      Written form ("three thousand...")    → spoken words     (banfil-nandil...)
    """
    # 0. Protect time patterns (H:MM, HH:MM) with placeholders
    _times = {}
    def _protect_time(m: re.Match) -> str:
        k = f'__T{len(_times)}__'
        _times[k] = m.group(0)
        return k
    text = re.sub(r'\b\d{1,2}:\d{2}\b', _protect_time, text)

    # 1. Strip commas from digit groups: 4,782,391 → 4782391
    text = re.sub(r'(\d{1,3}(?:,\d{3})+)', lambda m: m.group(0).replace(',', ''), text)

    # 2. Digit sequences → written symbol notation, tagged as [NUM]
    def replace_digits(m: re.Match) -> str:
        n = int(m.group(0))
        return f'[NUM:{to_arkulcis_written(n)}]'

    result = re.sub(r'\b\d+\b', replace_digits, text)

    # Restore protected time strings
    for k, v in _times.items():
        result = result.replace(k, v)

    # 3. Written English number words → spoken word form
    # Use greedy word-by-word scanner instead of regex to handle
    # multi-word numbers like "three thousand three hundred and thirty two"
    result = _convert_written_numbers(result)
    return result


def _convert_written_numbers(text: str) -> str:
    """
    Greedy left-to-right scan: find the longest sequence of words that
    forms a valid English number, convert it, then continue.
    """
    # Number-related words (includes connectors)
    NUM_WORDS = {
        'zero','one','two','three','four','five','six','seven','eight','nine',
        'ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen',
        'seventeen','eighteen','nineteen','twenty','thirty','forty','fifty',
        'sixty','seventy','eighty','ninety','hundred','thousand','million',
        'billion','dozen','gross','score',
    }
    CONNECTORS = {'and', 'a'}

    # Tokenise preserving spaces and punctuation
    tokens = re.split(r'(\s+|[^\w\s-]|(?<=[a-z])-(?=[a-z]))', text)
    # Flatten to word tokens with their positions
    # Simpler: work on words split by whitespace, rebuild after
    words   = text.split()
    result  = []
    i       = 0

    while i < len(words):
        # Try to build the longest number phrase starting at i
        best_end   = None
        best_n     = None
        phrase     = []

        for j in range(i, min(i + 12, len(words))):  # max ~12 words for a number
            w = words[j]
            # Strip punctuation for lookup
            w_clean = re.sub(r'[^a-z-]', '', w.lower())
            # Hyphens: "thirty-two" counts as one token, split for lookup
            parts = w_clean.split('-')

            # "and" only allowed after at least one number word (not at start)
            # "a" is allowed at start only if followed by a shorthand (a dozen, a gross)
            SHORTHANDS = {'dozen', 'gross', 'score', 'hundred', 'thousand', 'million'}
            if j == i and w_clean == 'and':
                break
            if j == i and w_clean == 'a':
                # only continue if next word is a shorthand
                if j + 1 < len(words):
                    nxt = re.sub(r'[^a-z]', '', words[j+1].lower())
                    if nxt not in SHORTHANDS:
                        break
                else:
                    break

            # Allow number words and connectors
            if all(p in NUM_WORDS or p in CONNECTORS for p in parts if p):
                phrase.append(w)
                candidate = ' '.join(re.sub(r'[^a-z0-9 -]', '', x.lower()) for x in phrase)
                n = words_to_int(candidate)
                if n is not None and n > 0:
                    best_end = j + 1
                    best_n   = n
            else:
                break

        if best_n is not None and best_end is not None:
            result.append(f'[NUM:TEXT:{to_arkulcis_spoken(best_n)}]')
            # Preserve trailing punctuation of last word
            last = words[best_end - 1]
            trail = re.sub(r'[a-zA-Z0-9δλ-]', '', last)
            if trail:
                result.append(trail)
            i = best_end
        else:
            result.append(words[i])
            i += 1

    return ' '.join(result)


def strip_num_tags(text: str) -> str:
    """
    Remove [NUM:x] and [NUM:TEXT:x] protection tags, keeping the number value.
    Also strips any stray << >> wrappers the AI may echo back.
      [NUM:1δ54]        → 1δ54
      [NUM:TEXT:banbil] → banbil
      <<banjil-nan>>    → banjil-nan
    """
    text = re.sub(r'\[NUM:TEXT:([^\]]+)\]', r'\1', text)
    text = re.sub(r'\[NUM:([^\]]+)\]', r'\1', text)
    text = re.sub(r'<<([^>]+)>>', r'\1', text)
    return text


if __name__ == '__main__':
    print('=== Written symbol notation ===')
    for n in [0,1,10,11,12,22,99,144,155,1728]:
        print(f'{n:>8}  spoken={to_arkulcis_spoken(n):<25} written={to_arkulcis_written(n)}')

    print('\n=== English words → Arkulcis spoken ===')
    tests = [
        'I have twenty-two books.',
        'She found one hundred and forty-four insects.',
        'A dozen eggs.',
        'Ten cats and eleven dogs.',
        'Three thousand students.',
        'The year two thousand and twenty-four.',
    ]
    for t in tests:
        print(f'  IN:  {t}')
        print(f'  OUT: {apply(t)}')
        print()
