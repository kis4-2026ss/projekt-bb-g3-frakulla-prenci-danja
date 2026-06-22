"""
arkulcis/translator/skills/verb_skill.py

Skill 2 — Verb normalisation pipeline:
  1. Strip English auxiliary verbs (had, has, have, been, was, were, will)
  2. Inject tense markers: [PAST] [PRESENT] [FUTURE] [NEG_PAST] [NEG_PRESENT] [NEG_FUTURE]
  3. Replace irregular verb surface forms with base infinitives
     so the AI only ever receives regular roots + tense markers.
"""

import re

# ── Words that should never be captured as verbs by auxiliary patterns ────────
_AUX_SKIP = {
    # Adverbs
    'often','always','never','already','still','just','also','even','ever',
    'soon','yet','only','nearly','almost','quite','very','really','much',
    'more','less','most','least','enough','well','hard','fast','later',
    'immediately','suddenly','finally','gradually','eventually','perhaps',
    'probably','certainly','definitely','recently','previously','further',
    'quickly','slowly','likely','possibly','probably','apparently','not',
    'together','forward','backward','instead','otherwise','therefore',
    # Pronouns (must not be captured as verbs)
    'i','you','he','she','it','we','they','me','him','her','us','them',
    'who','what','which','that','this','these','those',
    # Common nouns that appear after modals in questions
    'investors','engineers','researchers','governments','analysts','experts',
    'people','users','accounts','files','reports','executives','companies',
    # Prepositions / conjunctions that slip through
    'to','not','no','nor',
    # Indefinite pronouns
    'everyone','someone','anyone','no one','nobody','somebody','anybody','nothing','something','anything','everything',
}

# ── Tense marker injection ─────────────────────────────────────────────────
# Order matters: longer/more-specific patterns first
AUXILIARY_PATTERNS = [
    # ── Future/modal perfect (must come BEFORE simple auxiliary patterns) ──
    # Future perfect with interleaved adverb (MUST BE FIRST)
    (r'\bwill\s+(?:\w+ly|likely|probably|certainly|possibly|still|soon|never|already|just|always|eventually|finally|surely|perhaps)\s+have\s+(\w+)\b', r'[VERB(FUTURE):\1]'),
    # Future perfect: will have + verb → FUTURE (drop "have")
    (r'\bwill\s+have\s+(\w+)\b',           r'[VERB(FUTURE):\1]'),
    # Modal passive (MUST be before generic modal): may have been + main verb
    (r'\b(?:would|could|should|might|may)\s+have\s+been\s+(\w+\w)\b', r'[VERB(PAST):\1]'),
    # Passive: was/were + past participle
    (r'\b(?:was|were)\s+(\w+ed)\b', r'[VERB(PAST):\1]'),
    # Modal past: would/could/should/might/may have + verb → PAST
    (r'\b(?:would|could|should|might|may)\s+have\s+(\w+)\b', r'[VERB(PAST):\1]'),
    # Modal present: would/could/should/might/may + verb
    (r'\b(?:would|could|should|might|may)\s+(\w+)\b', r'[VERB(PRESENT):\1]'),
    # ── Standard auxiliary patterns ──────────────────────────────────────
    # Perfect continuous: had been + verb-ing
    (r'\bhad\s+been\s+(\w+ing)\b',          r'[VERB(PAST):\1]'),
    # Inverted past perfect (Had they known... / Had he seen...)
    (r'\bhad\s+(?:i|you|he|she|it|we|they|\w+)\s+(\w+(?:ed|en|wn|ne|orn|awn|own))\b', r'[VERB(PAST):\1]'),
    # Past perfect with "already"
    (r'\bhad\s+already\s+(\w+(?:ed|en|wn|ne|orn|awn|own|ne))\b', r'already [VERB(PAST):\1]'),
    # Past perfect: had + past participle
    (r'\bhad\s+(\w+(?:ed|en|wn|ne|orn|awn|own|ilt|elt|oken|ozen|olen|osen))\b', r'[VERB(PAST):\1]'),
    # Perfect with interleaved adverb: have/has/had + adverb + verb (have often wondered)
    (r'\b(?:has|have|had)\s+(?:\w+ly|often|always|never|just|recently|ever|finally|already|sometimes|usually|frequently|still|even)\s+(\w+)\b',
     r'[VERB(PAST):\1]'),
    # Present perfect: has/have + past participle
    (r'\bhas\s+(\w+(?:ed|en|wn|ne|orn|awn|own|ilt|elt|oken|ozen|olen|osen))\b', r'[VERB(PRESENT):\1]'),
    (r'\bhave\s+(\w+(?:ed|en|wn|ne|orn|awn|own|ilt|elt|oken|ozen|olen|osen))\b', r'[VERB(PRESENT):\1]'),
    # Past continuous: was/were + verb-ing
    (r'\bwas\s+(\w+ing)\b',                 r'[VERB(PAST):\1]'),
    (r'\bwere\s+(\w+ing)\b',                r'[VERB(PAST):\1]'),
    # Present continuous: is/are + verb-ing
    (r'\bis\s+(\w+ing)\b',                  r'[VERB(PRESENT):\1]'),
    (r'\bare\s+(\w+ing)\b',                 r'[VERB(PRESENT):\1]'),
    # Future continuous: will be + verb-ing
    (r'\bwill\s+be\s+(\w+ing)\b',           r'[VERB(FUTURE):\1]'),
    # Future with interleaved adverb: will + adverb + verb
    (r'\bwill\s+(?:likely|probably|certainly|possibly|still|also|soon|never|already|just|always|eventually|finally|quickly|slowly|surely|perhaps)\s+(\w+)\b', r'[VERB(FUTURE):\1]'),
    # Future negative: will not + verb → NEG&FUTURE
    (r'\bwill\s+not\s+(\w+)\b',              r'[VERB(NEG&FUTURE):\1]'),
    # Future: will + verb
    (r'\bwill\s+(\w+)\b',                    r'[VERB(FUTURE):\1]'),
    # Contractions — negatives first
    (r"\bdidn't\s+(\w+)\b",                 r'[VERB(NEG&PAST):\1]'),
    (r"\bdon't\s+(\w+)\b",                  r'[VERB(NEG&PRESENT):\1]'),
    (r"\bdoesn't\s+(\w+)\b",                r'[VERB(NEG&PRESENT):\1]'),
    (r"\bwon't\s+(\w+)\b",                  r'[VERB(NEG&FUTURE):\1]'),
    (r"\bwouldn't\s+(\w+)\b",               r'[VERB(NEG&PAST):\1]'),
    (r"\bshouldn't\b",                       r'[VERB(NEG&PRESENT):should]'),
    (r"\bcouldn't\b",                        r'[VERB(NEG&PAST):could]'),
    (r"\bwasn't\b",                          r'[VERB(NEG&PAST):be]'),
    (r"\bweren't\b",                         r'[VERB(NEG&PAST):be]'),
    (r"\bisn't\b",                           r'[VERB(NEG&PRESENT):be]'),
    (r"\baren't\b",                          r'[VERB(NEG&PRESENT):be]'),
    (r"\bhadn't\s+(\w+)\b",               r'[VERB(NEG&PAST):\1]'),  # hadn't taken → [NEG&PAST:take]
    (r"\bhadn't\b",                          r'[VERB(NEG&PAST):have]'),
    (r"\bhasn't\b",                          r'[VERB(NEG&PRESENT):have]'),
    (r"\bhaven't\b",                         r'[VERB(NEG&PRESENT):have]'),
    # "had not" / "has not" (non-contracted)
    (r'\bhad\s+not\s+(\w+)\b',              r'[VERB(NEG&PAST):\1]'),
    (r'\bhas\s+not\s+(\w+)\b',              r'[VERB(NEG&PRESENT):\1]'),
    (r'\bwill\s+not\s+(\w+)\b',             r'[VERB(NEG&FUTURE):\1]'),
    # "be + past participle" passive: is/are/was/were + -ed → keep -ed, mark tense
    (r'\bwas\s+(\w+ed)\b',                  r'[VERB(PAST):\1]'),
    (r'\bwere\s+(\w+ed)\b',                 r'[VERB(PAST):\1]'),
    (r'\bis\s+(\w+ed)\b',                   r'[VERB(PRESENT):\1]'),
    (r'\bare\s+(\w+ed)\b',                  r'[VERB(PRESENT):\1]'),
]

# ── Irregular verb surface form → base infinitive ─────────────────────────
IRREGULAR_VERBS = {
    # False positives for -ated rule
    'repeated':'repeat','treated':'treat','defeated':'defeat',
    'heated':'heat','seated':'seat','cheated':'cheat',
    'eaten':'eat','beaten':'beat',
    # Common -ate verbs (explicit entries)
    'generated':'generate','created':'create','located':'locate',
    'regulated':'regulate','evaluated':'evaluate','updated':'update',
    'separated':'separate','demonstrated':'demonstrate',
    'automated':'automate','activated':'activate','validated':'validate',
    'simulated':'simulate','estimated':'estimate','calculated':'calculate',
    'indicated':'indicate','operated':'operate','integrated':'integrate',
    'communicated':'communicate','collaborated':'collaborate',
    # go
    'went':'go','gone':'go',
    # run
    'ran':'run',
    # see
    'saw':'see','seen':'see',
    # think
    'thought':'think',
    # come
    'came':'come',
    # tell
    'told':'tell',
    # say
    'said':'say',
    # catch
    'caught':'catch',
    # bring
    'brought':'bring',
    # fight
    'fought':'fight',
    # give
    'gave':'give','given':'give',
    # drink
    'drank':'drink','drunk':'drink',
    # eat
    'ate':'eat','eaten':'eat',
    # sleep
    'slept':'sleep',
    # know
    'knew':'know','known':'know',
    # lose
    'lost':'lose',
    # find
    'found':'find',
    # speak
    'spoke':'speak','spoken':'speak',
    # sit
    'sat':'sit',
    # steal
    'stole':'steal','stolen':'steal',
    # stand
    'stood':'stand',
    # take
    'took':'take','taken':'take',
    # make
    'made':'make',
    # get
    'got':'get','gotten':'get',
    # leave
    'left':'leave',
    # feel
    'felt':'feel',
    # keep
    'kept':'keep',
    # meet
    'met':'meet',
    # send
    'sent':'send',
    # build
    'built':'build',
    # hold
    'held':'hold',
    # read (past = read, same spelling)
    # lead
    'led':'lead',
    # mean
    'meant':'mean',
    # grow
    'grew':'grow','grown':'grow',
    # fly
    'flew':'fly','flown':'fly',
    # draw
    'drew':'draw','drawn':'draw',
    # throw
    'threw':'throw','thrown':'throw',
    # fall
    'fell':'fall','fallen':'fall',
    # break
    'broke':'break','broken':'break',
    # choose
    'chose':'choose','chosen':'choose',
    # write
    'wrote':'write','written':'write',
    # ride
    'rode':'ride','ridden':'ride',
    # rise
    'rose':'rise','risen':'rise',
    # wear
    'wore':'wear','worn':'wear',
    # wake
    'woke':'wake','woken':'wake',
    # begin
    'began':'begin','begun':'begin',
    # swim
    'swam':'swim','swum':'swim',
    # sing
    'sang':'sing','sung':'sing',
    # ring
    'rang':'ring','rung':'ring',
    # spring
    'sprang':'spring','sprung':'spring',
    # shrink
    'shrank':'shrink','shrunk':'shrink',
    # sink
    'sank':'sink','sunk':'sink',
    # stink
    'stank':'stink','stunk':'stink',
    # wind
    'wound':'wind',
    # bind
    'bound':'bind',
    # find
    'found':'find',
    # grind
    'ground':'grind',
    # to be
    'was':'be','were':'be','been':'be',
    # to have
    'had':'have',
    # to do
    'did':'do','done':'do',
    # to bear
    'bore':'bear','born':'bear','borne':'bear',
    # to hide
    'hid':'hide','hidden':'hide',
    # to bite
    'bit':'bite','bitten':'bite',
    # to freeze
    'froze':'freeze','frozen':'freeze',
    # to forbid
    'forbade':'forbid','forbidden':'forbid',
    # to forgive
    'forgave':'forgive','forgiven':'forgive',
    # to forget
    'forgot':'forget','forgotten':'forget',
    # to forsake
    'forsook':'forsake','forsaken':'forsake',
    # to seek
    'sought':'seek',
    # to buy
    'bought':'buy',
    # to think
    'thought':'think',
    # to bring
    'brought':'bring',
    # to teach
    'taught':'teach',
    # to catch
    'caught':'catch',
    # to fight
    'fought':'fight',
    # to shoot
    'shot':'shoot',
    # to cut (same)
    # to put (same)
    # to let (same)
    # to set (same)
    # to hit (same)
    # to cost (same)
    # to hurt (same)
    'hurt':'hurt',
    # to lay
    'laid':'lay',
    # to pay
    'paid':'pay',
    # to say
    'said':'say',
    # to slay
    'slew':'slay','slain':'slay',
    # to swear
    'swore':'swear','sworn':'swear',
    # to tear
    'tore':'tear','torn':'tear',
    # to bear
    'bore':'bear',
    # to wear
    'wore':'wear',
    # to forbear
    'forbore':'forbear',
    # to bid
    'bade':'bid','bidden':'bid',
    # to give
    'gave':'give',
}

_PUNCT_RE = re.compile(r'^([^a-zA-Z]*)(.*?)([^a-zA-Z]*)$')


def _normalise_word(word: str) -> str:
    """Normalise a single word, preserving punctuation and capitalisation."""
    m = _PUNCT_RE.match(word)
    if not m:
        return word
    pre, core, post = m.group(1), m.group(2), m.group(3)
    clean = core.lower()
    if clean in IRREGULAR_VERBS:
        base = IRREGULAR_VERBS[clean]
        if core and core[0].isupper():
            base = base.capitalize()
        return pre + base + post
    return word


def inject_tense_markers(text: str) -> str:
    """Apply auxiliary stripping and tense marker injection."""
    result = text
    for pattern, replacement in AUXILIARY_PATTERNS:
        def safe_replace(m: re.Match, repl: str = replacement) -> str:
            # Skip if captured verb is actually an adverb/non-verb
            groups = m.groups()
            if groups and groups[-1].lower() in _AUX_SKIP:
                return m.group(0)  # keep original
            return re.sub(r'\\(\d+)', lambda g: m.group(int(g.group(1))), repl)
        result = re.sub(pattern, safe_replace, result, flags=re.IGNORECASE)
    return result


def normalise_irregular_verbs(text: str) -> str:
    """Replace irregular surface forms with base infinitives."""
    return ' '.join(_normalise_word(w) for w in text.split())


def _detect_past_from_context(text: str) -> str:
    """
    If the sentence contains past-tense signal words AND no tense markers yet,
    inject a sentence-level [PAST_CTX] hint for the AI.
    """
    import re
    PAST_SIGNALS = {
        'yesterday', 'last', 'ago', 'earlier', 'previously', 'once',
        'then', 'afterward', 'afterwards', 'later', 'before',
    }
    if '[PAST]' in text or '[FUTURE]' in text or '[NEG_PAST]' in text:
        return text  # already marked
    words = set(re.sub(r'[^a-z ]', '', text.lower()).split())
    if words & PAST_SIGNALS:
        return text + ' [CTX:PAST]'
    return text


def _to_infinitive(verb: str) -> str:
    """Convert a verb form to its base infinitive."""
    clean = re.sub(r"[^a-z]", "", verb.lower().strip())
    # Check irregular map first
    if clean in IRREGULAR_VERBS:
        return IRREGULAR_VERBS[clean]
    # Strip regular -ed ending: vanished→vanish, completed→complete, forced→force
    if clean.endswith("ed") and len(clean) > 4:
        root = clean[:-2]
        # doubled consonant: stopped→stop
        if len(root) > 2 and root[-1] == root[-2]:
            return root[:-1]
        # Silent-e detection using suffix pattern
        # Verbs ending in -ced/-ged/-ved/-zed/-sed: originally ended in -ce/-ge/-ve/-ze/-se
        if len(clean) >= 4 and clean[-3] in 'cgvsz' and clean[-2] == 'e' and clean[-1] == 'd':
            return clean[:-1]   # forced→force, produced→produce, resolved→resolve
        # Verbs ending in -ited/-uted/-eted/-ated (invited, generated, completed, created)
        # -a-: generated/created/located/updated are genuine -ate verbs, NOT repeated/treated
        # Distinguish: generated=g+ener+at+e+d → strip d → generate
        #              repeated=r+e+p+e+at+e+d → strip d → repeate (WRONG)
        # Key difference: genuine -ate verbs have consonant directly before -ated
        #   generated: ..r+at+ed, created: ..e+at+ed (vowel before -at OK for -ate verbs)
        #   repeated: ..e+at+ed — same pattern! Cannot distinguish without wordlist.
        # Solution: treat ALL -ated as → -ate, then add common false positives to IRREGULAR_VERBS
        if (len(clean) >= 6 and clean[-4:] == 'ated'):
            return clean[:-1]   # generated→generate, created→create, located→locate
        if (len(clean) >= 5 and clean[-3] == 't' and clean[-2:] == 'ed'
                and clean[-4] in 'iue'):
            return clean[:-1]   # invited→invite, completed→complete, excited→excite
        # Verbs ending in -ired/-ined/-iled (required, designed, compiled)
        # These have root ending in consonant + 'i' + consonant → add -e
        if (len(clean) >= 5 and clean[-1] == 'd' and clean[-2] == 'e'
                and root[-1] in 'rln' and len(root) >= 2 and root[-2] == 'i'):
            return root + 'e'   # requir→require, compil→compile
        # Default: strip -ed, return root as-is
        return root
    # Strip -ing ending (continuous forms captured): looking→look, running→run
    if clean.endswith("ing") and len(clean) > 5:
        root = clean[:-3]
        # doubled consonant: running→runn→run, sitting→sitt→sit
        if len(root) > 2 and root[-1] == root[-2]:
            return root[:-1]
        # silent-e verb: driving→driv→drive, producing→produc→produce
        # Only add -e for roots ending in: c, g, v, z (clearly need silent-e)
        # NOT: k (look, book, cook), d (lead, read), l, n, r, s, t, m, p
        if root and root[-1] in 'cgvz':
            if len(root) >= 2 and root[-2] in 'aeiou':
                return root + 'e'
        # Special: roots ending in consonant where original clearly had silent-e
        # e.g. "stating"→stat→state (t after a), "driving"→driv→drive (v after i)
        if root and root[-1] in 'pt' and len(root) >= 2 and root[-2] in 'aeiou':
            return root + 'e'
        return root
        return root
    return clean


def _normalise_inside_tags(text: str) -> str:
    """Normalise verb forms captured inside VERB(...) tags to base infinitives.
    Also tags standalone past participles after a comma in series (built, broken, and rebuilt)."""
    # Step 1: normalise verb roots inside existing tags
    def fix_tag(m: re.Match) -> str:
        prefix = m.group(1)
        verb   = m.group(2).strip()
        base   = _to_infinitive(verb)
        return f'[VERB({prefix}):{base}]'
    text = re.sub(r'\[VERB\(([^)]+)\):([^\]]+)\]', fix_tag, text)

    # Step 2: tag comma-series participles after an existing VERB(...) tag
    # e.g. "[VERB(PRESENT):build], broken, and rebuilt" → tag "broken" and "rebuilt" too
    PARTICIPLE_ENDINGS = r'\w+(?:ed|en|wn|ne|orn|awn|own|ilt|oken|uilt)'
    def tag_series(m: re.Match) -> str:
        tense = m.group(1)  # PRESENT or PAST
        word  = m.group(2)
        base  = _to_infinitive(word)
        return f'[VERB({tense}):{base}]'
    # After a VERB(...) tag, tag any comma-separated participles up to "and/or + last"
    series_pat = r'(?<=\])(?:,\s*|\s+and\s+|\s+or\s+)('+ PARTICIPLE_ENDINGS + r')(?=[,\s]|$)'
    # Only fire if there's a VERB tag nearby (within 50 chars)
    def conditional_tag(m: re.Match) -> str:
        pos = m.start()
        context_before = text[:pos] if pos < len(text) else ''
        # Check if a VERB tag ends within 60 chars before
        if re.search(r'\[VERB\([^)]+\):[^\]]+\]\s*$', context_before[-80:]):
            word = m.group(1)
            # Determine tense from the preceding tag
            tense_m = re.search(r'\[VERB\(([^)]+)\)', context_before[-80:])
            tense = tense_m.group(1) if tense_m else 'PRESENT'
            base = _to_infinitive(word)
            return m.group(0).replace(word, f'[VERB({tense}):{base}]')
        return m.group(0)
    text = re.sub(series_pat, conditional_tag, text, flags=re.IGNORECASE)
    return text


KNOWN_VERB_OVERRIDE = set()


def detect_question(text: str) -> str:
    """
    Detect English questions formed with Did/Does/Do/Will/Would/Is/Are/Was/Were
    + subject, and mark them with a leading [Q] tag. Strip the auxiliary
    "Did/Does/Do" (it carries no separate meaning in Arkulcis -- tense is
    on the main verb), and normalise the main verb back to infinitive so
    the existing VERB tag patterns can apply tense correctly.
    """
    stripped = text.strip()
    if not stripped.endswith('?'):
        return text

    # "Did/Does/Do" + subject + verb  → strip auxiliary, tag verb as PAST/PRESENT
    m = re.match(r'^(Did|Does|Do)\s+(.+)\?\s*$', stripped, re.IGNORECASE)
    if m:
        aux, rest = m.group(1).lower(), m.group(2)
        tense = 'PAST' if aux == 'did' else 'PRESENT'
        # rest = "she go home" or "the strongest students read all the forgotten books"
        # Find first verb-like word after the subject and tag it.
        # Heuristic: tag the LAST bare verb token before any trailing object,
        # but simplest robust approach: tag the first word that is not part of
        # a noun phrase -- we approximate by tagging the first untagged word
        # that is NOT in _AUX_SKIP and NOT preceded by "the/a/an".
        words = rest.split(' ')
        SKIP_SUFFIXES = ('est', 'er')
        for i, w in enumerate(words):
            clean = re.sub(r'[^a-zA-Z]', '', w)
            if not clean:
                continue
            low = clean.lower()
            if low in _AUX_SKIP or low in ('the', 'a', 'an', 'all', 'some', 'any', 'every'):
                continue
            # Skip superlatives/comparatives (strongest, faster) -- they are adjectives
            if low.endswith(SKIP_SUFFIXES) and low not in KNOWN_VERB_OVERRIDE:
                continue
            # Skip plural nouns (students, books) heuristically: word ends in -s,
            # is not in IRREGULAR_VERBS, and the NEXT word also looks like a verb
            # (a simple plural-noun-before-verb heuristic)
            if low.endswith('s') and low not in IRREGULAR_VERBS and i + 1 < len(words):
                continue
            base = _to_infinitive(low) if low.endswith(('ed', 'ing')) else low
            words[i] = f'[VERB({tense}):{base}]'
            break
        return f'[Q] {" ".join(words)}'

    return text


# Common verb roots used to detect the main verb in a bare-present sentence
# (no auxiliary, e.g. "They love reading books." / "She runs every day.")
_COMMON_VERB_ROOTS = {
    'love','like','want','need','know','think','believe','see','hear','feel',
    'run','walk','read','write','speak','work','play','live','eat','drink',
    'sleep','study','teach','learn','build','make','create','find','lose',
    'win','help','support','support','enjoy','prefer','hate','hope','wish',
    'own','have','hold','carry','bring','take','give','send','receive',
    'open','close','start','begin','finish','end','continue','stop',
    'buy','sell','pay','cost','spend','save','earn','use','try','attempt',
    'speak','talk','say','tell','ask','answer','explain','describe','show',
}


def _tag_bare_present_verb(text: str) -> str:
    """
    If a sentence has NO [VERB(...)] tag, no [Q] tag, and no [CTX] tag yet,
    it's likely a bare present-tense sentence with no auxiliary to strip
    (e.g. "They love reading books."). Tag the first recognised verb root
    as PRESENT so the AI has something deterministic to apply -as to.
    """
    if '[VERB(' in text or '[Q]' in text:
        return text  # already handled

    words = text.split(' ')
    for i, w in enumerate(words):
        clean = re.sub(r'[^a-zA-Z]', '', w)
        if not clean:
            continue
        low = clean.lower()
        # Strip 3rd-person -s ending (runs→run, works→work) before checking
        candidate = low
        if low.endswith('s') and low[:-1] in _COMMON_VERB_ROOTS:
            candidate = low[:-1]
        elif low.endswith('es') and low[:-2] in _COMMON_VERB_ROOTS:
            candidate = low[:-2]
        if candidate in _COMMON_VERB_ROOTS or low in IRREGULAR_VERBS.values():
            punct = re.sub(r'[a-zA-Z]', '', w)
            words[i] = f'[VERB(PRESENT):{candidate}]{punct}'
            return ' '.join(words)
    return text


def apply(text: str) -> str:
    """
    Full verb skill pipeline:
      0. Detect Did/Does/Do questions, mark with [Q] and tag the main verb
      1. Inject tense markers (strips auxiliaries — must run on original English)
      2. Normalise irregular verbs inside tags + in free text
      3. Detect past context from signal words
      4. Fallback: tag bare present-tense verbs with no auxiliary
    """
    text = detect_question(text)
    text = inject_tense_markers(text)
    text = _normalise_inside_tags(text)   # fix irregular forms captured inside tags
    text = normalise_irregular_verbs(text) # fix remaining irregular forms in free text
    text = _detect_past_from_context(text)
    text = _tag_bare_present_verb(text)
    return text


if __name__ == '__main__':
    tests = [
        ("She had been looking for it.",         "loking [PAST] for it."),
        ("He fought hard and never gave up.",    "He fight hard and never give up."),
        ("She said she didn't know that.",        "She say she [NEG_PAST] know that."),
        ("He had already seen the film.",         "He already see [PAST] the film."),
        ("She had not slept well.",               "[NEG_PAST] sleep well."),
        ("Tomorrow she will wake up.",            "Tomorrow she wake [FUTURE] up."),
        ("They came back home.",                  "They come back home."),
        ("He brought him to the police.",         "He bring him to the police."),
        ("She drank some tea and ate a meal.",    "She drink some tea and eat a meal."),
        ("He thought it was wonderful.",          "He think it be wonderful."),
    ]
    print(f'{"Input":<50} {"Output"}')
    print('-' * 100)
    all_pass = True
    for inp, expected in tests:
        got = apply(inp)
        ok  = '✓' if expected.lower() in got.lower() else '~'
        if ok == '~':
            all_pass = False
        print(f'{ok}  {inp:<50} {got}')
    print(f'\n{"All tests passed!" if all_pass else "Some outputs differ — review above."}')
