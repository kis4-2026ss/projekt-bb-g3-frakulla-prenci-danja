# Arkulcis — Full Technical Documentation
## KIS4 2026 · FH Hagenberg

---

## 1. Language specification

### 1.1 Core principle
One letter = one sound, always. No silent letters, no irregular forms, no exceptions.

### 1.2 Alphabet (23 letters)
A B D E F G H I J K L M N O P R S T U V W Y Z

Removed: C (→K before a/o/u, →S before e/i), Q (→KW), X (→KS). PH always written as F.

Vowels: A=ah · E=eh · I=ee · O=oh · U=oo

### 1.3 Grammar reference

**Word order:** Verb first, then subject, then rest. Every sentence, no exceptions.

**Articles:** None. Drop the/a/an entirely.

**Pronouns:**
| Singular | | Plural | |
|----------|--|--------|--|
| mi | I | mios | we |
| ni | you | nios | you all |
| pi | he/she/it | pios | they |

**Verb tenses** (same suffix for all subjects, never changes by person):

| Tense | Suffix | Example |
|-------|--------|---------|
| Present | -as | runas (I/she/they run) |
| Past | -ed | runed |
| Future | -ul | runul |

**To be:**

| English | Arkulcis |
|---------|----------|
| am/is/are | beas |
| was/were | beed |
| will be | beul |
| am not/isn't | no-beas |
| was not | no-beed |
| will not be | no-beul |

BANNED forms: ar, is, am, was, were, ias, iaed.

**Complex tense simplification** (Arkulcis has only 3 tenses):

| English | Arkulcis |
|---------|----------|
| has seen | sias (drop has) |
| had found | finded (drop had) |
| had been looking | loking (drop had been) |
| is running | runas (drop is, -ing→-as) |
| was running | runed (drop was, -ing→-ed) |
| will be running | runul (drop will be, -ing→-ul) |

BANNED: haded, beed (as auxiliary), bein, wased.

**Adjectives:** -ro (base), -rot (comparative), -rots (superlative)
`fastro · fastrot · fastrots`

**Adverbs:** -ly (base), -lyt (comparative), -lyts (superlative)
`fastly · fastlyt · fastlyts`

**Negation:** no- prefix before verb.
`no-runas mi` (I don't run)

**Questions:** ka + verb + subject + rest.
`ka goed pi hom?` (Did she go home?)

**Possession:**
- Pronoun: attach suffix to noun — katmi (my cat), bukni (your book)
- Names/nouns: use di (of) — buk di Arlind, brodor di pi

**Plurals:** add -os suffix — katos (cats), studentos (students)

### 1.4 Number system (base-12)

| Decimal | Spoken | Symbol |
|---------|--------|--------|
| 0 | zan | 0 |
| 1–9 | ban dan fan gan han jan kan lan man | 1–9 |
| 10 | nan | δ |
| 11 | pan | λ |
| 12 | banbil | 10 |
| 144 | bandil | 100 |
| 1728 | banfil | 1000 |
| 20736 | bangil | 10000 |

Multipliers (full set): -bil(×12), -dil(×144), -fil(×1728), -gil(×20736),
-hil(×248832), -jil(×2985984), -kil(×35831808)...

**Conversion modes:**
- Digit input (3232) → written symbols: [NUM:1δ54]
- Written words (twenty-two) → spoken form: [NUM:TEXT:banbil-nan]

---

## 2. System architecture

### 2.1 EN → Arkulcis pipeline (5 steps)

```
English input
    ↓
[STEP 1] number_skill.py
    Protect times (3:47) with placeholders
    Strip commas: 4,782,391 → 4782391
    Digit numbers → [NUM:base12symbol]
    Written words → [NUM:TEXT:spoken]
    ↓
[STEP 2] verb_skill.py
    Run AUXILIARY_PATTERNS in priority order
    Inject VERB(PAST/PRESENT/FUTURE/NEG&...) tags
    _to_infinitive() normalises irregular + regular -ed/-ing
    _detect_past_from_context() adds [CTX:PAST] hint
    ↓
[STEP 3] annotation_skill.py
    tag_pronouns()   → [PRON:mi/ni/pi/mios/nios/pios]
    tag_names()      → [NAME:x] (proper nouns, skips common words)
    tag_adjectives() → [ADJ:x] / [ADJ(COMP):x] / [ADJ(SUP):x]
    tag_adverbs()    → [ADV:x] / [ADV(COMP):x] / [ADV(SUP):x]
    ↓
[STEP 4] strip_num_tags()
    Remove [NUM:...] wrappers, leave values for AI to copy
    ↓
[STEP 5] AI (Groq llama-3.3-70b-versatile)
    Receives tagged text, applies one rule per tag
    Outputs Arkulcis
```

### 2.2 Arkulcis → English pipeline (4 steps)

```
Arkulcis input
    ↓
[STEP 1] AI decoder
    Reverses Arkulcis grammar rules
    Outputs raw English with [PAST]/[PRESENT]/[FUTURE] markers
    "goed pi hom" → "she go [PAST] home"
    ↓
[STEP 2] ak_decoder_skill.py
    Protect times before number conversion
    Written base-12 symbols → decimal (1727707 → 4,782,391)
    Spoken Arkulcis numbers → decimal (banjil-... → 4,782,391)
    Merge split large spoken numbers (a + b where b << a)
    Restore Arkulcis pronouns to English (pi → they)
    ↓
[STEP 3] AI englishifier
    Tense markers → natural English (go [PAST] → went)
    Restore irregular past forms
    Restore articles, contractions, complex tenses
    ↓
Natural English output
```

### 2.3 Complete tag reference

| Tag | Injected by | AI rule |
|-----|-------------|---------|
| [NUM:x] | number_skill | copy x verbatim (base-12 symbol) |
| [NUM:TEXT:x] | number_skill | copy x verbatim (spoken form) |
| [VERB(PAST):x] | verb_skill | phonics(x) + -ed |
| [VERB(PRESENT):x] | verb_skill | phonics(x) + -as |
| [VERB(FUTURE):x] | verb_skill | phonics(x) + -ul |
| [VERB(NEG&PAST):x] | verb_skill | no- + phonics(x) + -ed |
| [VERB(NEG&PRESENT):x] | verb_skill | no- + phonics(x) + -as |
| [VERB(NEG&FUTURE):x] | verb_skill | no- + phonics(x) + -ul |
| [CTX:PAST] | verb_skill | hint: whole sentence is past (no output) |
| [PRON:mi/ni/pi/...] | annotation_skill | copy pronoun |
| [NAME:x] | annotation_skill | phonetic respell of x |
| [ADJ:x] | annotation_skill | phonics(x) + -ro |
| [ADJ(COMP):x] | annotation_skill | phonics(x) + -rot |
| [ADJ(SUP):x] | annotation_skill | phonics(x) + -rots |
| [ADV:x] | annotation_skill | phonics(x) + -ly |
| [ADV(COMP):x] | annotation_skill | phonics(x) + -lyt |
| [ADV(SUP):x] | annotation_skill | phonics(x) + -lyts |

---

## 3. Translation accuracy analysis

### 3.1 EN → Arkulcis results (5 test paragraphs)

**Overall accuracy: ~85–89%**

| Paragraph | Theme | Score | Notes |
|-----------|-------|-------|-------|
| P1 | Business audit | 89% | Best result. All key verbs tagged correctly. |
| P2 | Driving / platform | 84% | Drive→drived (silent-e doubling occasional). |
| P3 | Research team | 83% | Built/break tagged ✓. rebuilt still missed. |
| P4 | Data / zettabytes | 85% | generate→generatul ✓. |
| P5 | Emergency anomaly | 82% | 3:47 preserved ✓. $23691λ269 preserved ✓. |

**What works reliably:**
- Number conversion: all digit and word-form numbers convert correctly
- Large numbers: 4,782,391 → 1727707 ✓, 987,654,321 → 23691λ269 ✓
- Symbol preservation: δ and λ pass through the AI unchanged
- Time formats: 3:47 a.m. never converted to base-12
- Pronoun replacement: mi/ni/pi/mios/nios/pios consistent
- Tense tagging: had/was/will patterns correctly classified
- Verb-first word order: consistently applied
- Complex tenses: future perfect (will have written → writul), modal past (would have made → maked) both correctly simplified

**Remaining error classes (~11–15%):**
- Silent-e doubling: `drive+ed = driveed` instead of `drived` (AI phonics not 100% reliable)
- Untagged bare verbs: `go/begin/run/send` have no auxiliary to strip, get inconsistent treatment
- Phonetic variance: `decision` → `desishen/desijon/desijen` varies across runs
- Series verbs: `built, broken, and rebuilt` — only first two tagged, third missed

### 3.2 Arkulcis → English results (5 test paragraphs)

**Overall accuracy: ~82–88%**

| Paragraph | Theme | Score | Notes |
|-----------|-------|-------|-------|
| P1 | Business audit | 88% | Near-perfect. $4,782,391 ✓. Verb tenses natural. |
| P2 | Driving / platform | 85% | Numbers correct ✓. Tenses mostly restored. |
| P3 | Research team | 82% | 73,500 decoded correctly ✓. 1,000,000 ✓. |
| P4 | Data / zettabytes | 84% | 2050 ✓. 175 ✓. Natural English output good. |
| P5 | Emergency anomaly | 83% | 3:47 ✓. $987,654,321 ✓. |

**What works reliably:**
- Written number reverse: 1727707 → 4,782,391 ✓
- Large spoken number reverse: banjil-kanhil-dangil-kanfil-kandil-kan → 4,782,391 ✓
- Split spoken number merge: danlil-...hanbil + banbil-man → 987,654,321 ✓
- Time format preservation: 3:47 never converted ✓
- Tense naturalisation: go [PAST] → went, make [PAST] → made ✓
- Complex tense restoration: englishifier recovers had been / would have ✓
- Article restoration: the/a/an added naturally by englishifier

**Remaining imperfections:**
- Duplicate dollar amounts: "involving $4,782,391, which is 4,782,391 dollars" — 
  the "which is..." clause should be dropped but the englishifier keeps it
- `five years` in P3 decoded as "five years" correctly, but via spoken number han→5
  rather than the original English — acceptable result
- Sentence-level rephrasing: englishifier occasionally adds/removes sentences
  (P3 adds "a position she has held" — not in original but accurate)

### 3.3 Interesting observations

**The numbers were the hardest part technically** but the most satisfying when solved.
The base-12 system required: digit→symbol conversion, word→spoken conversion,
time format protection, and full round-trip reversal. Handling a number like
987,654,321 (which in Arkulcis spoken form spans two separate [NUM:TEXT:...] tokens
that must be summed back together) required non-obvious merge logic.

**The AI is better at English→Arkulcis than expected** for grammar rules, but worse
than expected at phonetics. It applies verb-first word order reliably, handles
pronouns, and respects number tags. But its phonetic respelling is inconsistent
across runs — the same word may become desishen, desijon, or desijen.

**The englishifier (AK→EN Pass 3) is surprisingly powerful.** Given very crude input
like "she go [PAST] home" it produces "she went home". Given "We not take [PAST]
immediate action, the situation be [PAST] much worse" it produces "We didn't take
immediate action, and the situation was much worse." The tense marker hints carry
enough information for a second AI to fully naturalise the output.

**Prompt engineering has hard limits.** Over 20+ iterations we improved accuracy
from ~65% to ~88%. The remaining ~12% cannot be addressed by prompt changes —
it requires the two-AI annotator architecture (AI-1 tags every word, AI-2 translates
only tagged tokens). This is the design described in PROTOCOL.md Phase 4.

**The _to_infinitive() function is a microcosm of English morphology complexity.**
What seems simple — "convert a verb to its base form" — required handling:
regular -ed (vanished→vanish), silent-e -ed (forced→force, but NOT predicted→predicte),
-ated verbs (generated→generate, but NOT repeated→repeat), -iled/-ired verbs
(compiled→compile, required→require), doubled consonant -ing (running→run),
silent-e -ing (driving→drive, but NOT looking→looke). A 130-entry explicit
IRREGULAR_VERBS map handles the rest.

---

## 4. File structure

```
arkulcis/
├── language_spec/
│   ├── grammar_rules.json     — All grammar rules + number system + tense simplification
│   └── vocabulary.json        — 150+ words (nouns, verbs, adjectives, adverbs)
├── translator/
│   ├── phonetic.py            — Rule-based phonetic respelling (C→K/S, PH→F, etc.)
│   ├── numeral.py             — Base-12 spoken number converter (legacy)
│   ├── preprocessor.py        — Skill pipeline orchestrator (3 skills)
│   ├── prompt_builder.py      — All AI system prompts (EN→AK, AK decoder, englishifier)
│   ├── translate.py           — Translation engine (Groq API, DEBUG mode)
│   └── skills/
│       ├── number_skill.py    — Digit+word number conversion, time protection
│       ├── verb_skill.py      — Auxiliary stripping, 130+ irregular verbs, tense tags
│       ├── annotation_skill.py — PRON/NAME/ADJ/ADV tagging
│       └── ak_decoder_skill.py — AK→EN post-processor (number reverse, pronoun restore)
├── document_pipeline/
│   └── doc_translate.py       — Long document translation (chunked)
├── tests/
│   ├── test_translate.py      — Core pipeline tests (phonetics, grammar, prompt builder)
│   ├── test_skills.py         — Skill unit tests (182 passing, 7 skipped)
│   ├── test_extended.py       — API integration tests (@api marker)
│   └── fixtures/
│       └── test_document.txt
├── docs/
│   ├── PROTOCOL.md            — Development protocol + iteration log
│   └── DOCUMENTATION.md       — This file
├── cli.py                     — Interactive CLI (DEBUG=true for pipeline steps)
├── run.py                     — Quick demo script
├── .env.example               — GROQ_API_KEY + DEBUG=false
└── pytest.ini
```

---

## 5. Setup and usage

```bash
git clone https://github.com/kis4-2026ss/projekt-bb-g3-frakulla-prenci-danja
cd projekt-bb-g3-frakulla-prenci-danja
pip install -r requirements.txt
cp .env.example .env
# Add your Groq API key (free at console.groq.com)
python cli.py
```

**Enable debug mode** (shows all 5/6 pipeline steps):
```
# In .env:
DEBUG=true
```

**Run tests** (no API key required):
```bash
pytest tests/                    # all tests
pytest tests/ -m "not api"       # skip live API tests
pytest tests/test_skills.py      # skill unit tests only
```

---

## 6. Team

| Member | Student ID | Contribution |
|--------|------------|--------------|
| Danja Arens | S2410307006 | Language design, grammar spec, vocabulary |
| Arlind Frakulla | S2410307009 | Translation engine, API integration, architecture |
| Erti Prenci | S2410307030 | Document pipeline, testing, debugging |
