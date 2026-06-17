"""
arkulcis/translator/phonetic.py
Converts English text to Arkulcis phonetic spelling.
Rule: one letter = one sound. Remove C, Q, X. Respell silents.
"""

import re

# Rules applied in order. Longer/more-specific patterns first.
# We use a two-pass approach for 'igh' to avoid the ai->ei rule firing on it.
REPLACEMENTS = [
    (r'ough',        'uf'),
    (r'augh',        'af'),
    (r'igh',         'AI'),      # placeholder uppercase — protected from later rules
    (r'sch',         'sk'),
    (r'ph',          'f'),
    (r'ck',          'k'),
    (r'qu',          'kw'),
    (r'wh',          'w'),
    (r'kn',          'n'),
    (r'wr',          'r'),
    (r'gh',          ''),
    (r'a(?=tion)',   'ei'),      # nation -> neishen
    (r'tion',        'shen'),
    (r'sion',        'shen'),
    (r'ture',        'chur'),
    (r'dge',         'j'),
    (r'tch',         'ch'),
    (r'oo',          'u'),
    (r'ee',          'i'),
    (r'ea',          'i'),
    (r'oe',          'o'),
    (r'oa',          'o'),
    (r'ou',          'ou'),
    (r'ow',          'ou'),
    (r'aw',          'ao'),
    (r'au',          'ao'),
    (r'ai',          'ei'),      # rain, wait -> rei, weit
    (r'ay',          'ei'),
    (r'ey',          'ei'),
    (r'ie',          'i'),
    (r'a(?=[^aeiou ]*e\b)',  'ei'),
    (r'i(?=[^aeiou ]*e\b)',  'ai'),
    (r'o(?=[^aeiou ]*e\b)',  'o'),
    (r'c(?=[eiy])',  's'),
    (r'c',           'k'),
    (r'x',           'ks'),
    (r'y\b',         'i'),
    (r'e\b',         ''),
    (r'AI',          'ai'),      # restore placeholder -> lowercase ai
]


def to_arkulcis_phonetic(word: str) -> str:
    """Convert a single English word to Arkulcis phonetic spelling."""
    result = word.lower()
    for pattern, replacement in REPLACEMENTS:
        result = re.sub(pattern, replacement, result)
    return result


def respell_text(text: str, preserve_case: bool = True) -> str:
    """
    Respell every word in a text to Arkulcis phonetics.
    Preserves punctuation and whitespace.
    Capitalises first letter if original started with a capital (proper nouns).
    """
    def respell_word(match):
        original = match.group(0)
        converted = to_arkulcis_phonetic(original)
        if preserve_case and original[0].isupper() and converted:
            converted = converted[0].upper() + converted[1:]
        return converted

    return re.sub(r"[A-Za-z']+", respell_word, text)


if __name__ == '__main__':
    tests = [
        ('phone',    'fon'),
        ('queen',    'kwin'),
        ('fox',      'foks'),
        ('city',     'siti'),
        ('cat',      'kat'),
        ('school',   'skul'),
        ('night',    'nait'),
        ('knife',    'naif'),
        ('clock',    'klok'),
        ('rain',     'rein'),
        ('day',      'dei'),
        ('beautiful','biutiful'),
    ]
    print(f'{"English":<16} {"Expected":<16} {"Got":<16} {"OK?"}')
    print('-' * 56)
    for word, expected in tests:
        got = to_arkulcis_phonetic(word)
        ok = '✓' if got == expected else '✗'
        print(f'{word:<16} {expected:<16} {got:<16} {ok}')
