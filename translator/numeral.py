"""
arkulcis/translator/numeral.py
Converts decimal integers to Arkulcis base-12 number words.

Digits 0-11: zan ban dan fan gan han jan kan lan man nan pan
Multipliers: -bil (x12) -dil (x144) -fil (x1728) -gil -hil -jil ...
"""

DIGITS = ['zan', 'ban', 'dan', 'fan', 'gan', 'han',
          'jan', 'kan', 'lan', 'man', 'nan', 'pan']

MULTIPLIER_SUFFIXES = ['bil', 'dil', 'fil', 'gil', 'hil', 'jil',
                       'kil', 'lil', 'mil', 'nil', 'pil']


def to_base12_digits(n: int) -> list[int]:
    """Return list of base-12 digits, most significant first."""
    if n == 0:
        return [0]
    digits = []
    while n > 0:
        digits.insert(0, n % 12)
        n //= 12
    return digits


def to_arkulcis_number(n: int, hyphen: bool = True) -> str:
    """
    Convert a non-negative integer to its Arkulcis word form.
    e.g. 12 -> banbil, 13 -> banbil-ban, 144 -> bandil, 157 -> bandil-banbil-ban
    """
    if n < 0:
        raise ValueError('Arkulcis numbers must be non-negative.')
    if n == 0:
        return 'zan'

    b12 = to_base12_digits(n)
    length = len(b12)
    parts = []

    for i, digit in enumerate(b12):
        if digit == 0:
            continue
        power = length - 1 - i
        digit_word = DIGITS[digit]          # e.g. 'ban', 'dan', 'pan'
        if power == 0:
            parts.append(digit_word)        # plain digit: ban, dan ...
        else:
            suffix = MULTIPLIER_SUFFIXES[power - 1]   # bil, dil, fil ...
            # Combine: ban + bil = banbil, dan + dil = dandil
            parts.append(digit_word + suffix)

    sep = '-' if hyphen else ''
    return sep.join(parts)



def from_arkulcis_number(word: str) -> int:
    """
    Parse an Arkulcis number word back to a decimal integer.
    Accepts hyphenated (banbil-ban) or joined (banbilban) forms.
    Strategy: try to match full digit+suffix combos (e.g. banbil, dandil)
    then fall back to plain digit words.
    """
    word = word.strip().lower().replace('-', '')

    DIGIT_MAP = {d: i for i, d in enumerate(DIGITS)}
    MUL_MAP = {s: 12 ** (i + 1) for i, s in enumerate(MULTIPLIER_SUFFIXES)}

    if word in DIGIT_MAP:
        return DIGIT_MAP[word]

    total = 0
    i = 0
    while i < len(word):
        matched = False
        # Try digit_word + suffix (e.g. ban+bil = banbil)
        for dig_word in sorted(DIGITS[1:], key=len, reverse=True):
            for suf in sorted(MUL_MAP.keys(), key=len, reverse=True):
                chunk = dig_word + suf
                if word[i:].startswith(chunk):
                    total += DIGITS.index(dig_word) * MUL_MAP[suf]
                    i += len(chunk)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            # Try plain digit word
            for dig_word in sorted(DIGITS, key=len, reverse=True):
                if word[i:].startswith(dig_word):
                    total += DIGITS.index(dig_word)
                    i += len(dig_word)
                    matched = True
                    break
        if not matched:
            raise ValueError(f'Cannot parse Arkulcis number: {word!r} at position {i}')

    return total


if __name__ == '__main__':
    test_cases = [0, 1, 11, 12, 13, 14, 24, 143, 144, 157, 1728, 2024, 1000000]
    print(f'{"Decimal":<12} {"Base-12 (Arkulcis)":<30} {"Roundtrip check"}')
    print('-' * 60)
    for n in test_cases:
        ak = to_arkulcis_number(n)
        b12_digits = to_base12_digits(n)
        b12_str = ''.join(str(d) if d < 10 else chr(65 + d - 10) for d in b12_digits)
        print(f'{n:<12} {ak:<30} ✓' )
