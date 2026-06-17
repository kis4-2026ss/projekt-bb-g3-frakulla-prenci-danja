# Arkulcis — Development Protocol
## KIS4 2026 · FH Hagenberg · Frakulla · Prenci · Arens

This document chronicles the full development process of the Arkulcis translation
system — what we tried, what failed, why it failed, and how we fixed it.

---

## Phase 1 — Language design

### Core principle
Arkulcis is a constructed language (conlang) with one rule above all others:
**one letter = one sound, always.** No silent letters. No exceptions.

### Phonics
Removed from the English alphabet: C (→ K or S), Q (→ KW), X (→ KS), PH (→ F).
The 23-letter alphabet: A B D E F G H I J K L M N O P R S T U V W Y Z.
Vowels are always: A=ah, E=eh, I=ee, O=oh, U=oo.

### Grammar decisions
- **Word order:** Verb-first, then subject, then rest. Always.
- **Pronouns:** mi/ni/pi (singular, pi gender-neutral), mios/nios/pios (plural +os).
- **Tenses:** Three only — -as (present), -ed (past), -ul (future). Never conjugated by subject.
- **To be:** beas/beed/beul, never ar/is/am/was/were.
- **Articles:** None. Drop the/a/an entirely.
- **Adjectives:** -ro (base), -rot (comparative), -rots (superlative).
- **Adverbs:** -ly (base), -lyt (comparative), -lyts (superlative).
- **Negation:** no- prefix before verb.
- **Questions:** ka + verb + subject + rest.

### Number system (base-12)
Digits 0–9 use Arabic numerals; 10=δ (spoken: nan), 11=λ (spoken: pan).
Multipliers: -bil (×12), -dil (×144), -fil (×1728), -gil (×20736), and beyond.
Two modes: digit input → written symbols (3232→1δ54); written words → spoken (twenty-two→banbil-nan).

---

## Phase 2 — Single-pass AI translation (first attempt)

### Approach
Send raw English directly to Groq API (llama-3.3-70b-versatile) with a large
system prompt encoding all grammar rules.

### Problems encountered and iteration log

**Problem 1 — Irregular verb forms**
The model used surface forms as roots: fought→foughted ✗, went→wented ✗.
*Fix attempts:* Added 20+ explicit examples. Partial improvement.

**Problem 2 — Tense detection in long paragraphs**
Model defaulted to present tense even in clearly past paragraphs.
"She went to the library" → "wantas pi to librari" ✗
*Fix attempts:* Added STEP 0 tense detection guide with signal words.

**Problem 3 — Auxiliary verb leakage**
"had been looking" → "had beed loking" ✗, "will not forget" → "wil forgetas" ✗.
*Fix attempts:* Explicit auxiliary stripping rules in prompt. Limited effect.

**Problem 4 — Suffix over-application**
Model added -as to non-verbs: "in" → "inas", "and" → "andas".
*Fix attempts:* Blocklist of conjunctions/prepositions. Still leaked.

**Problem 5 — "To be" confusion**
Model invented forms like ias, iaed. Inserted "to be" before other verbs.
*Fix attempts:* Explicit beas/beed/beul table with banned forms.

**Problem 6 — Pronoun leakage**
English pronouns survived: "goed she" instead of "goed pi".
*Fix attempts:* Pronoun replacement table in prompt. Inconsistent.

**Problem 7 — Number mangling**
Pre-converted numbers (banbil-nan) got verb suffixes: banbil-nanas ✗.
*Fix attempts:* Added <<...>> protection markers.

### Conclusion of Phase 2
Single-pass AI plateaued at ~65% accuracy with ~3,500 token prompts.
Token usage hit Groq free tier (100k/day) after ~22 translations.
Adding more rules caused regressions elsewhere — the approach was fundamentally fragile.

---

## Phase 3 — Preprocessor skill pipeline

### Architecture shift
Move deterministic work to Python BEFORE the AI sees the text.
Three skills run sequentially: number_skill → verb_skill → annotation_skill.

### Skill 1: number_skill.py
- Protects time patterns (3:47 stays 3:47) using placeholder tokens.
- Strips commas from digit groups: 4,782,391 → 4782391.
- Converts digit numbers to base-12 written symbols: 3232 → [NUM:1δ54].
- Converts written English numbers to spoken Arkulcis: twenty-two → [NUM:TEXT:banbil-nan].
- Tags are stripped before the AI call so it receives clean symbols to copy.

**Key bug fixed:** comma-separated numbers were splitting into separate tokens ($4,782,391 → three separate [NUM] tags). Fixed with pre-processing regex.

**Key bug fixed:** time formats (3:47) were being converted as numbers (47 in base-12 = 55). Fixed with placeholder protection matching \d{1,2}:\d{2} before digit conversion.

### Skill 2: verb_skill.py
Pattern ordering is critical — longer/more-specific patterns must come first.

Patterns in order of priority:
1. `will + adverb + have + verb` → [VERB(FUTURE):x] — MUST BE FIRST
2. `will have + verb` → [VERB(FUTURE):x]
3. `modal have been + participle` → [VERB(PAST):x] (passive)
4. `modal have + verb` → [VERB(PAST):x]
5. `modal + verb` → [VERB(PRESENT):x]
6. Inverted past perfect: `Had + subject + participle` → [VERB(PAST):x]
7. `had been + -ing` → [VERB(PAST):x]
8. `had/has/have + adverb + participle` → [VERB(PAST):x] (have often wondered)
9. `had + participle` → [VERB(PAST):x]
10. `has/have + participle` → [VERB(PRESENT):x]
11. `was/were + -ing` → [VERB(PAST):x]
12. `will not + verb` → [VERB(NEG&FUTURE):x]
13. `will + verb` → [VERB(FUTURE):x]
14. Contractions (didn't/won't/shouldn't etc.) → [VERB(NEG&...):x]

**Key bug fixed:** `will likely have generated` was giving PRESENT because `have + participle` (pattern 10) fired before `will + adverb + have + verb` (pattern 1). Fixed by moving the adverb-interleaved future perfect to position 0.

**Key bug fixed:** `have often wondered` — "often" ends in "en" so it was matching the `have + (ed|en)` pattern, tagging "often" as the verb. Fixed by adding `had/has/have + adverb + participle` pattern before the simple `have + ed/en` pattern.

**Key bug fixed:** `had known` not tagged — "known" ends in "wn" not "en". Fixed by extending participle endings to include wn, ne, orn, awn, own, ilt, elt, oken, ozen, olen, osen.

The `_AUX_SKIP` set prevents common words from being captured as verbs:
- Adverbs: often, likely, probably, not, already, soon, etc.
- Pronouns: I, you, he, she, they, we, etc.
- Common nouns: investors, engineers, researchers, governments, etc.

The `_to_infinitive()` function converts captured verb forms to base infinitives:
- Regular -ed: predicted→predict, vanished→vanish
- Silent-e -ed: forced→force (ced/ged/ved/zed pattern), resolved→resolve
- -ated verbs: generated→generate, created→create (explicit map)
- False positives blocked: repeated→repeat, treated→treat, defeated→defeat
- Regular -ing: looking→look, running→run (doubled consonant detection)
- Silent-e -ing: driving→drive, producing→produce (consonant+vowel check)

### Skill 3: annotation_skill.py
Wraps tokens in semantic tags so AI-2 applies exactly one rule per token.

Tag types produced:
- `[PRON:mi/ni/pi/mios/nios/pios]` — pronoun replacement
- `[NAME:x]` — proper noun phonetic respelling
- `[ADJ:x]`, `[ADJ(COMP):x]`, `[ADJ(SUP):x]` — adjective suffixes
- `[ADV:x]`, `[ADV(COMP):x]`, `[ADV(SUP):x]` — adverb suffixes

**Key bug fixed:** annotation ran inside existing VERB tags, producing
[VERB(PRESENT):[PRON:ni]]. Fixed by splitting on existing [...]  brackets
and only processing non-tag parts.

**Key bug fixed:** Common words at sentence start were getting [NAME:] tags
(Last → [NAME:Last], Have → [NAME:Have]). Fixed with 150-word blocklist.

---

## Phase 4 — Tag system design

### Self-contained tags (final design)
Every tag contains its content — the AI applies exactly one rule per token:

| Tag | Rule | Example output |
|-----|------|----------------|
| [NUM:1δ54] | copy verbatim | 1δ54 |
| [NUM:TEXT:banbil-nan] | copy verbatim | banbil-nan |
| [VERB(PAST):go] | root + -ed | goed |
| [VERB(PRESENT):run] | root + -as | runas |
| [VERB(FUTURE):write] | phonics + -ul | raitul |
| [VERB(NEG&PAST):know] | no- + root + -ed | no-noed |
| [VERB(NEG&PRESENT):run] | no- + root + -as | no-runas |
| [VERB(NEG&FUTURE):forget] | no- + phonics + -ul | no-forgotul |
| [CTX:PAST] | sentence hint | (no output) |
| [PRON:pi] | copy pronoun | pi |
| [NAME:Phoenix] | phonetic respell | Finiks |
| [ADJ:beautiful] | root + -ro | biutifro |
| [ADJ(COMP):fast] | root + -rot | fastrot |
| [ADJ(SUP):strong] | root + -rots | strongrots |
| [ADV:quick] | root + -ly | fastly |

NUM tags are stripped before the AI call; all other tags pass through.

---

## Phase 5 — Arkulcis → English pipeline

### Three-pass design
**Pass 1 — AI decoder:** Reads Arkulcis, reverses grammar rules,
outputs raw English with tense markers: "goed pi hom" → "she go [PAST] home".

**Pass 2 — Python post-processor (ak_decoder_skill.py):**
- Protects time patterns before number conversion.
- Converts written base-12 symbols back to decimal (1727707 → 4,782,391).
- Converts spoken Arkulcis numbers back to decimal (banjil-kanhil-... → 4,782,391).
- Merges adjacent spoken number tokens that represent one split large number.
- Restores Arkulcis pronouns to English (pi → they, mios → we).

**Key bug fixed:** long spoken numbers use multipliers beyond -bil/-dil/-fil/-gil.
Full set: bil, dil, fil, gil, hil, jil, kil, lil, mil, nil. The original regex
only included 4, so numbers like 4,782,391 (using -jil/-kil/-hil) were partially decoded.

**Key bug fixed:** large numbers split across two [NUM:TEXT:...] tokens in the
forward pipeline were decoded as two separate numbers. Added merge logic:
if two adjacent decoded spoken numbers satisfy b < a and b < 10M, they represent
one number (a + b).

**Pass 3 — AI englishifier:** Takes raw decoded English, restores natural grammar:
irregular past forms (go [PAST] → went), articles, contractions, complex tenses.

---

## Phase 6 — Key lessons learned

1. **Deterministic > probabilistic for rule-based tasks.**
   Python code is 100% reliable for anything with an exact answer: numbers,
   irregular verb lookup, auxiliary stripping, pronoun replacement.
   The AI is for judgment tasks: phonetic respelling, word-order application,
   naturalisation.

2. **Pattern ordering is a bug source.**
   Every time a new pattern was added to AUXILIARY_PATTERNS, it could break
   existing patterns by matching first. The will+adverb+have bug (generating
   PRESENT instead of FUTURE) was caused by pattern 10 firing before pattern 1.
   Always add more specific patterns before less specific ones.

3. **Prompt size has a real cost.**
   Each token added to reduce one error type risks creating new errors elsewhere.
   The sweet spot was a ~2,100 token prompt with worked examples rather than
   exhaustive rules.

4. **One job per AI pass.**
   Splitting annotation from translation reduced errors significantly. The decoder
   only needs to know Arkulcis grammar; the englishifier only needs to know English
   grammar. Neither needs to know both.

5. **The englishifier is essential and surprisingly good.**
   Information lost in Arkulcis (articles, perfect tense, irregular past forms,
   word order) is largely recoverable in a second pass. The englishifier turned
   "she go [PAST] home" into "she went home" reliably.

6. **Iterative prompt engineering has diminishing returns.**
   After ~15 iterations the single-pass prompt plateaued at ~65%. Architectural
   changes (skill pipeline, tag system, two-AI approach) each bought 10-15%
   improvement that no amount of prompt tweaking could achieve.
