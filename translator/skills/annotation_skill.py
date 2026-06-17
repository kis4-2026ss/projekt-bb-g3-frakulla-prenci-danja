"""
arkulcis/translator/skills/annotation_skill.py

Skill 3 — Semantic annotation:
Wraps tokens in tags so AI-2 applies exactly one rule per token.

Tags added:
  [NAME:x]           proper noun → phonetic respell + capitalise
  [ADJ:x]            adjective base → x + -ro
  [ADJ(COMP):x]      comparative adjective → x + -rot
  [ADJ(SUP):x]       superlative adjective → x + -rots
  [ADV:x]            adverb base → x + -ly
  [ADV(COMP):x]      comparative adverb → x + -lyt
  [ADV(SUP):x]       superlative adverb → x + -lyts
  [PRON:mi]          pronoun → replace with Arkulcis equivalent
"""

import re

# ── Pronoun map ───────────────────────────────────────────────
PRONOUN_MAP = {
    'i':       'mi',
    'me':      'mi',
    'my':      'mi',
    'myself':  'mi',
    'you':     'ni',
    'your':    'ni',
    'yourself':'ni',
    'he':      'pi',
    'him':     'pi',
    'his':     'pi',
    'himself': 'pi',
    'she':     'pi',
    'her':     'pi',
    'hers':    'pi',
    'herself': 'pi',
    'it':      'pi',
    'its':     'pi',
    'itself':  'pi',
    'we':      'mios',
    'us':      'mios',
    'our':     'mios',
    'ours':    'mios',
    'ourselves':'mios',
    'they':    'pios',
    'them':    'pios',
    'their':   'pios',
    'theirs':  'pios',
    'themselves':'pios',
    'you all': 'nios',
    'yourselves':'nios',
}

# ── Comparative / superlative patterns ───────────────────────
# Superlative (check before comparative)
SUPERLATIVE_PATTERNS = [
    r'\bmost\s+(\w+)\b',         # most beautiful
    r'\b(\w+est)\b',              # fastest, biggest
]
COMPARATIVE_PATTERNS = [
    r'\bmore\s+(\w+)\b',          # more beautiful
    r'\b(\w+er)\b',               # faster, bigger
]

# Words that end in -er/-est but are NOT comparatives
NOT_COMPARATIVE = {
    'after', 'better', 'bitter', 'butter', 'center', 'chapter',
    'chester', 'cluster', 'computer', 'consider', 'corner', 'cover',
    'daughter', 'deliver', 'discover', 'easter', 'enter', 'ever',
    'fever', 'filter', 'finger', 'flower', 'foster', 'gender',
    'hamster', 'hunger', 'hunter', 'letter', 'litter', 'master',
    'matter', 'member', 'minister', 'monster', 'mother', 'murder',
    'never', 'number', 'offer', 'order', 'other', 'otter', 'outer',
    'over', 'oyster', 'paper', 'peter', 'plaster', 'plunder', 'poder',
    'poster', 'power', 'proper', 'quarter', 'rather', 'render',
    'river', 'roster', 'rubber', 'rudder', 'scatter', 'server',
    'silver', 'sister', 'slaughter', 'smaller', 'spider', 'summer',
    'super', 'supper', 'sweater', 'theater', 'thunder', 'timber',
    'together', 'tower', 'transfer', 'trigger', 'twitter', 'under',
    'upper', 'utter', 'vector', 'water', 'whether', 'winter', 'wonder',
    # superlative false positives
    'forest', 'harvest', 'honest', 'interest', 'invest', 'modest',
    'protest', 'request', 'suggest', 'test', 'west', 'zest',
}
NOT_SUPERLATIVE = NOT_COMPARATIVE | {
    'chest', 'crest', 'fest', 'jest', 'nest', 'pest', 'quest',
    'rest', 'vest', 'yest',
}

# Common English words that should never be NAME-tagged even if capitalised at sentence start
COMMON_WORDS = {
    'the','a','an','this','that','these','those','my','your','his','her',
    'its','our','their','i','we','you','he','she','it','they','who','which',
    'what','where','when','why','how','and','or','but','if','because','so',
    'as','at','by','for','from','in','into','of','on','onto','out','over',
    'to','up','with','about','after','before','between','during','through',
    'under','until','while','although','though','even','also','just','only',
    'not','no','nor','yet','both','either','neither','than','then','there',
    'here','now','still','already','ever','never','often','always','usually',
    'last','next','first','second','every','each','some','any','all','most',
    'more','less','few','many','much','several','such','same','other','another',
    'have','has','had','will','would','could','should','may','might','must',
    'shall','do','does','did','be','been','being','am','is','are','was','were',
    'NUM','TEXT',  # prevent tagging of tag keywords
    'get','got','go','went','come','came','take','took','make','made','know',
    'think','see','look','use','find','give','tell','ask','seem','feel','try',
    'leave','call','keep','let','begin','show','hear','play','run','move',
    'live','believe','hold','bring','happen','write','provide','sit','stand',
    'lose','pay','meet','include','continue','set','learn','change','lead',
    'understand','watch','follow','stop','create','speak','read','spend',
    'grow','open','walk','win','offer','remember','consider','appear','buy',
    'wait','serve','die','send','expect','build','stay','fall','cut','reach',
    'kill','remain','suggest','raise','pass','sell','require','report','decide',
    'pull','last','by','have','been','has',
}

# Known adjectives from vocabulary (base forms)
KNOWN_ADJECTIVES = {
    'big', 'small', 'fast', 'slow', 'good', 'bad', 'hot', 'cold',
    'new', 'old', 'long', 'short', 'hard', 'soft', 'strong', 'weak',
    'happy', 'sad', 'beautiful', 'ugly', 'smart', 'funny', 'serious',
    'quiet', 'loud', 'rich', 'poor', 'free', 'cheerful', 'rapid',
    'digital', 'simple', 'warm', 'wooden', 'forgotten', 'important',
    'relevant', 'broad', 'general', 'bright', 'dark', 'clean', 'dirty',
    'heavy', 'light', 'deep', 'shallow', 'thick', 'thin', 'wide',
    'narrow', 'tall', 'short', 'young', 'old', 'early', 'late',
    'high', 'low', 'near', 'far', 'right', 'wrong', 'true', 'false',
    'open', 'closed', 'full', 'empty', 'safe', 'dangerous', 'easy',
    'difficult', 'possible', 'impossible', 'necessary', 'different',
    'same', 'similar', 'special', 'common', 'natural', 'normal',
    'wonderful', 'terrible', 'excellent', 'perfect', 'interesting',
    'boring', 'exciting', 'amazing', 'awful', 'great', 'little',
    'tired', 'hungry', 'ready', 'busy', 'alive', 'dead', 'certain',
    'clear', 'complete', 'entire', 'final', 'main', 'major', 'minor',
    'official', 'original', 'personal', 'physical', 'political',
    'popular', 'positive', 'present', 'previous', 'public', 'real',
    'recent', 'significant', 'social', 'successful', 'traditional',
    'various', 'whole',
}

# Known adverbs (base forms, without -ly)
KNOWN_ADVERB_ROOTS = {
    'quick', 'slow', 'fast', 'hard', 'soft', 'loud', 'quiet',
    'bright', 'dark', 'clear', 'clean', 'close', 'deep', 'easy',
    'fair', 'free', 'gentle', 'glad', 'good', 'great', 'hard',
    'high', 'kind', 'large', 'late', 'light', 'likely', 'live',
    'long', 'low', 'near', 'nice', 'open', 'plain', 'poor', 'proud',
    'pure', 'quick', 'rare', 'real', 'right', 'rough', 'safe',
    'sharp', 'short', 'simple', 'slow', 'small', 'smart', 'smooth',
    'soft', 'soon', 'sure', 'sweet', 'tight', 'true', 'warm', 'wide',
    'wild', 'wise', 'wrong', 'beautiful', 'careful', 'cheerful',
    'complete', 'correct', 'direct', 'equal', 'exact', 'final',
    'formal', 'general', 'honest', 'hopeful', 'legal', 'local',
    'logical', 'natural', 'normal', 'official', 'perfect', 'personal',
    'physical', 'political', 'possible', 'probable', 'proper',
    'public', 'quiet', 'rapid', 'real', 'regular', 'relative',
    'safe', 'serious', 'special', 'strong', 'sudden', 'usual',
    'violent', 'visual', 'wonderful',
}


def _is_proper_noun(word: str) -> bool:
    """Heuristic: capitalised word that isn't sentence-start."""
    return word[0].isupper() if word else False


def tag_pronouns(text: str) -> str:
    """Replace English pronouns with [PRON:x] tags. Skips content inside existing tags."""
    # Split on existing tags, only process non-tag parts
    parts = re.split(r'(\[[^\]]+\])', text)
    result = []
    for part in parts:
        if part.startswith('['):
            result.append(part)  # keep existing tags unchanged
        else:
            def replace(m: re.Match) -> str:
                w = m.group(0)
                key = w.lower()
                if key in PRONOUN_MAP:
                    return f'[PRON:{PRONOUN_MAP[key]}]'
                return w
            result.append(re.sub(r"\b\w+\b", replace, part))
    return ''.join(result)


def tag_names(text: str) -> str:
    """
    Wrap likely proper nouns in [NAME:x] tags.
    Skips sentence-start words and common English words.
    """
    # Split on sentence boundaries to track sentence starts
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result_parts = []

    for sent in sentences:
        tokens = sent.split()
        result = []
        for i, tok in enumerate(tokens):
            # Skip tokens that are or contain existing tags
            if '[' in tok or ']' in tok:
                result.append(tok)
                continue

            # Strip punctuation for check
            clean = re.sub(r'[^a-zA-Z]', '', tok)
            punct = re.sub(r'[a-zA-Z]', '', tok)

            if not clean:
                result.append(tok)
                continue

            low = clean.lower()

            # Skip first word of sentence, common words, known adj/pronouns
            if (i == 0 or
                low in COMMON_WORDS or
                low in KNOWN_ADJECTIVES or
                low in PRONOUN_MAP):
                result.append(tok)
                continue

            if _is_proper_noun(clean):
                result.append(f'[NAME:{clean}]{punct}')
            else:
                result.append(tok)
        result_parts.append(' '.join(result))

    return ' '.join(result_parts)


def tag_adjectives(text: str) -> str:
    """Wrap adjectives in [ADJ], [ADJ(COMP)], [ADJ(SUP)] tags."""
    result = text

    # Superlative: "most X" or "X-est"
    def repl_sup_most(m: re.Match) -> str:
        word = m.group(1).lower()
        if word in KNOWN_ADJECTIVES:
            return f'[ADJ(SUP):{word}]'
        return m.group(0)

    def repl_sup_est(m: re.Match) -> str:
        word = m.group(1).lower()
        if word in NOT_SUPERLATIVE:
            return m.group(0)
        root = word[:-3] if word.endswith('est') else word
        if len(root) >= 3 and (root in KNOWN_ADJECTIVES or root + 'y' in KNOWN_ADJECTIVES):
            return f'[ADJ(SUP):{root}]'
        return m.group(0)

    result = re.sub(r'\bmost\s+(\w+)\b', repl_sup_most, result, flags=re.IGNORECASE)
    result = re.sub(r'\b(\w{5,}est)\b', repl_sup_est, result, flags=re.IGNORECASE)

    # Comparative: "more X" or "X-er"
    def repl_comp_more(m: re.Match) -> str:
        word = m.group(1).lower()
        if word in KNOWN_ADJECTIVES:
            return f'[ADJ(COMP):{word}]'
        return m.group(0)

    def repl_comp_er(m: re.Match) -> str:
        word = m.group(1).lower()
        if word in NOT_COMPARATIVE:
            return m.group(0)
        root = word[:-2] if word.endswith('er') else word
        if len(root) >= 3 and (root in KNOWN_ADJECTIVES or root + 'e' in KNOWN_ADJECTIVES):
            return f'[ADJ(COMP):{root}]'
        return m.group(0)

    result = re.sub(r'\bmore\s+(\w+)\b', repl_comp_more, result, flags=re.IGNORECASE)
    result = re.sub(r'\b(\w{5,}er)\b', repl_comp_er, result, flags=re.IGNORECASE)

    # Base adjective — skip words already wrapped in any tag
    def repl_adj(m: re.Match) -> str:
        word = m.group(0).lower()
        pos = m.start()
        context = m.string[max(0, pos-10):pos]
        if '[' in context and ']' not in context:
            return m.group(0)  # inside a tag already
        if word in KNOWN_ADJECTIVES:
            return f'[ADJ:{word}]'
        return m.group(0)

    # Only tag words not already inside brackets
    parts = re.split(r'(\[[^\]]+\])', result)
    result = ''
    for part in parts:
        if part.startswith('['):
            result += part
        else:
            result += re.sub(r'\b\w+\b', repl_adj, part, flags=re.IGNORECASE)
    return result


def tag_adverbs(text: str) -> str:
    """Wrap -ly adverbs in [ADV], [ADV(COMP)], [ADV(SUP)] tags."""
    def replace(m: re.Match) -> str:
        word = m.group(0).lower()
        root = word[:-2]  # strip -ly

        # Superlative adverb: "most quickly"
        # (handled separately in tag_adjectives for "most X")

        if root in KNOWN_ADVERB_ROOTS or root + 'e' in KNOWN_ADVERB_ROOTS:
            # Check for "more Xly" or "most Xly" in surrounding text
            return f'[ADV:{root}]'
        return m.group(0)

    return re.sub(r'\b\w+ly\b', replace, text, flags=re.IGNORECASE)


def apply(text: str) -> str:
    """
    Full annotation skill pipeline:
      1. Tag pronouns      → [PRON:x]
      2. Tag names         → [NAME:x]
      3. Tag adjectives    → [ADJ:x] / [ADJ(COMP):x] / [ADJ(SUP):x]
      4. Tag adverbs       → [ADV:x] / [ADV(COMP):x] / [ADV(SUP):x]
    """
    text = tag_pronouns(text)
    text = tag_names(text)
    text = tag_adjectives(text)
    text = tag_adverbs(text)
    return text


if __name__ == '__main__':
    tests = [
        "She went to the library with her brother.",
        "He fought harder than the strongest student.",
        "They walked quickly and beautifully through Phoenix.",
        "I don't think the most important thing is speed.",
        "Arlind and Danja studied in Hagenberg.",
    ]
    print(f'{"Input":<55} {"Tagged"}')
    print('-' * 110)
    for t in tests:
        print(f'{t}')
        print(f'→ {apply(t)}')
        print()
