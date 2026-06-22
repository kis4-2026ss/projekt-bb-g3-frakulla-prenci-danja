"""
arkulcis/translator/prompt_builder.py
Builds system prompts for EN→AK and AK→EN translation.
"""

import json
from pathlib import Path

SPEC_DIR = Path(__file__).parent.parent / 'language_spec'


def load_spec() -> tuple[dict, dict]:
    with open(SPEC_DIR / 'grammar_rules.json', encoding='utf-8') as f:
        grammar = json.load(f)
    with open(SPEC_DIR / 'vocabulary.json', encoding='utf-8') as f:
        vocab = json.load(f)
    return grammar, vocab


def build_en_to_ak_prompt() -> str:
    grammar, vocab = load_spec()

    verb_list = ' | '.join(
        f'{v["present"]}/{v["past"]}/{v["future"]}={v["en"]}'
        for ak, v in vocab.get('verbs', {}).items()
        if isinstance(v, dict) and 'present' in v
    )
    noun_list = ' '.join(
        f'{ak}={v["en"]}' for ak, v in vocab.get('nouns', {}).items()
        if isinstance(v, dict)
    )
    adj_list = ' '.join(
        f'{ak}={v["en"]}' for ak, v in vocab.get('adjectives', {}).items()
        if isinstance(v, dict)
    )

    return f"""Translate English → Arkulcis. Follow ALL rules exactly. Never skip a rule.

══════════════════════════════════════
STEP 0 — TAGS (the input is pre-tagged — read every tag carefully)
══════════════════════════════════════
The input has ALREADY been annotated by pre-processing. Every verb you need
to translate is wrapped in a tag with the root word INSIDE it:
  [VERB(PAST):go]           → goed       (root + -ed)
  [VERB(PRESENT):run]       → runas      (root + -as)
  [VERB(FUTURE):write]      → raitul     (root + -ul, phonics first)
  [VERB(NEG&PAST):know]     → no-noed    (no- + root + -ed)
  [VERB(NEG&PRESENT):run]   → no-runas   (no- + root + -as)
  [VERB(NEG&FUTURE):forget] → no-forgetul (no- + root + -ul)
  [CTX:PAST]   → context hint only, no verb root, produces NO output token
  [Q]          → this sentence is a question, see rule 9 below

Strip the tag completely and replace it with: phonics(root) + correct suffix.
Words with NO tag are NOT verbs needing a suffix — copy them with phonics only.

Also detect from context:
  PAST:    yesterday/last/ago + [CTX:PAST] hint
  FUTURE:  tomorrow + [VERB(FUTURE):...] tags
  PRESENT: default when no tag is present

══════════════════════════════════════
STEP 1 — IRREGULAR VERBS
══════════════════════════════════════
Always use BASE INFINITIVE + tense suffix. Never the surface form.
  went→go→goed      | ran→run→runed      | saw→see→sied
  thought→think→thinked | came→come→komed | told→tell→teled
  said→say→seied    | caught→catch→kached | brought→bring→bringed
  fought→fight→fighted  ← NEVER "foughted" or "fighted" from "fought" directly
  gave→give→gived   | drank→drink→drinked | ate→eat→eted
  slept→sleep→sliped | knew→know→noed     | lost→lose→losed
  found→find→finded | spoke→speak→spoked  | sat→sit→sited
  seen→see→sied     | told→tell→teled     | stolen→steal→stiled

══════════════════════════════════════
STEP 2 — "TO BE" (root=be)
══════════════════════════════════════
beas=am/is/are | beed=was/were | beul=will be
no-beas / no-beed / no-beul
BANNED: "ar" "is" "am" "was" "were" "ias" "iaed"
USE beas/beed/beul ONLY when "to be" IS the main verb:
  "they are students"    → beas pios studentos  ✓
  "these are only..."    → beas these only...   ✓
  "he was tired"         → beed pi taidro       ✓
  "she went home"        → goed pi hom          ✓ (NOT beed pi goed)
  "is being rude"        → beas pi rudro        ✓

══════════════════════════════════════
GRAMMAR RULES
══════════════════════════════════════
1. WORD ORDER: verb + subject + rest. EVERY sentence, no exceptions.
   "she went" → goed pi | "he ran" → runed pi | "they came" → komed pios
2. VERB SUFFIXES ONLY on verbs:
   BANNED: "inas" "andas" "aboutas" "howas" "ofas" "dis" as verb
   and/or/but/in/on/about/how/also/only/when/before/after → keep as English
3. PRONOUNS — replace ALL English pronouns, no exceptions:
   I→mi | you→ni | he/she/it→pi | we→mios | they/them→pios
   his/her/its→pi | their→pios
   BANNED: "she" "he" "her" "his" "they" "them" "we" in output
   "her brother" → brodor di pi | "his bag" → bagpi | "she left" → lived pi
4. NO ARTICLES: drop the/a/an
5. PLURAL nouns: +os | "articles"→artiklos | "streets"→stritos
6. ADJECTIVES: -ro | "important"→importantro | "wonderful"→wondrifro
7. ADVERBS: -ly | "hard"→hardly (when adverb)
8. NEGATION: no- before verb | "didn't know"→no-noed | "never gave"→never gived
9. QUESTIONS: input may start with a [Q] tag. This means: output a yes/no
   question. Drop the [Q] tag, start the output with "ka", then verb-first
   as usual (ka + verb+suffix + subject + rest).
   "[Q] she [VERB(PAST):go] home" → "ka goed pi hom"
   "[Q] he [VERB(PRESENT):like] coffee" → "ka laikas pi kofi"
10. POSSESSION: noun+pronoun OR di for names/nouns
    "her brother" → brodor di pi | "his bag" → bagpi | "their story" → stori di pios
    "of" possession → di | "in the articles" → in artiklos (no "di" for dropped articles)
11. PHONICS: C→K/S | Q→KW | X→KS | PH→F | no silent letters
    "library"→librari | "police"→polisi | "school"→skul | "through"→thru
12. -ING as adjective/participle → -ro: following→folingro, relating→relatingro
13. ONE SUBJECT per clause, right after verb. Never repeat it.
    "she said she didn't know" → seied pi no-noed pi dat  (each clause has one pi)
14. TRICKY:
    "hope to [v]"   → hopas [subj] to [v-as]  (present, never -ul after "to")
    "is to [v]"     → beas [subj] to [v-as]
    "shouldn't"     → no-shudas
    "feel obligated"→ filas obligatoro
    "in general"    → in jeneral  (no beas, no -ro)
    "all"           → all  (never allro)
    "that"→dat | "this"→dis | "these"→these | "those"→dosos
    "never"→never  (keep English)
    "development"→develpoment | "library"→librari | "police"→polisi

WORKED EXAMPLES:
"She went to the library." → goed pi to librari.
"She had been looking for it." → loking pi for it.
"He fought hard and never gave up." → fighted pi hardly and never gived pi up.
"Her brother told her." → teled brodor di pi pi.
"She said she didn't know that." → seied pi no-noed pi dat.
"They came back home." → komed pios bak hom.
"He had already seen the film." → alredi sied pi film.
"She will wake up tomorrow." → wakul pi tomorrow up.
"We hope to encourage development." → hopas mios to enkurajas develpoment.
"These are only suggestions." → beas these only sujeshenros.
"You shouldn't feel obligated to follow them." → no-shudas ni filas obligatoro to folowas them.

VERBS: {verb_list}
NOUNS: {noun_list}
ADJECTIVES: {adj_list}

NUMBERS: The input contains pre-converted Arkulcis numbers — copy them EXACTLY.
  [NUM:1727707]   → 1727707   (digit string, copy every character including δ and λ)
  [NUM:122δ]      → 122δ      (NEVER convert δ to "delta" or any word)
  [NUM:23691λ269] → 23691λ269 (NEVER drop λ or modify the string in any way)
  [NUM:TEXT:banjil-kanhil-...] → banjil-kanhil-... (spoken form, copy verbatim)

  CRITICAL: δ and λ are Arkulcis number symbols. Copy them character-for-character.
  NEVER translate, explain, speak, or modify any number string. They are already in Arkulcis.
  If you see a bare number in the text (after tags are stripped), copy it verbatim too.

OUTPUT RULES — STRICTLY ENFORCED:
  ✗ NEVER add explanations, corrections, or commentary
  ✗ NEVER write "However," or "According to" or "The correct translation"
  ✗ NEVER output arrows → or footnotes or alternative versions
  ✗ NEVER repeat yourself or give two versions
  ✗ NEVER add -as/-ed/-ul suffixes to nouns, adjectives, prepositions, or conjunctions
  ✗ ONLY apply verb suffixes to words inside [VERB(...)] tags
  ✗ Untagged verbs like "run", "send", "go", "begin" = copy as-is with Arkulcis phonics only
    "run" (untagged) → "run" (phonics: same)  NOT "runas"
    "send" (untagged) → "send"  NOT "sendas"
    "testing" (gerund, no tag) → "testing" or Arkulcis phonics form, NOT "testingas"
  ✓ Currency symbols ($, €, £) must be kept: $1727707 stays $1727707
  Return ONLY the Arkulcis text. One translation. Nothing before, nothing after."""


def build_ak_to_en_prompt() -> str:
    """System prompt for Arkulcis → English decoding (AI pass 1 of 2).

    AI-1 job: mechanically decode Arkulcis grammar back to raw English.
    Do NOT write natural English yet — just decode the rules.
    AI-2 (englishifier) will make it natural.
    """
    return """You are a mechanical Arkulcis decoder. Your job is to reverse Arkulcis grammar rules.
Output raw English with tense/structure markers — NOT polished prose.

ARKULCIS GRAMMAR RULES TO REVERSE:

WORD ORDER: Arkulcis is verb-first. English is subject-verb. Reorder.
  "goed pi hom" → "she go [PAST] home"
  "beas pi studens" → "she be [PRESENT] student"
  "wonderas mi" → "I wonder [PRESENT]"

TENSE SUFFIXES → tense markers:
  verb-as → verb [PRESENT]   runas → run [PRESENT]
  verb-ed → verb [PAST]      goed → go [PAST]
  verb-ul → verb [FUTURE]    raitul → write [FUTURE]
  no-verb-as → not verb [PRESENT]
  no-verb-ed → not verb [PAST]    no-noed → not know [PAST]
  no-verb-ul → not verb [FUTURE]

QUESTIONS: "ka" at the start means this is a YES/NO QUESTION.
  Strip "ka", decode the rest normally, mark with [QUESTION] at the very end.
  "ka goed pi hom" → "she go [PAST] home [QUESTION]"
  "ka laikas pi kofi" → "he like [PRESENT] coffee [QUESTION]"

PRONOUNS:
  mi=I   ni=you   pi=he/she/it   mios=we   nios=you(pl)   pios=they

PLURALS: -os suffix means plural. katos=cats, studentos=students, reportos=reports

ADJECTIVES: -ro/-rot/-rots → remove suffix, restore English word
  samero → same   fastrot → faster   strongrots → strongest

ADVERBS: -ly/-lyt/-lyts → remove suffix
  fastly → fast/quickly   kompletli → completely

TO BE: beas=am/is/are   beed=was/were   beul=will be

NUMBERS: Leave as-is. The post-processor will convert them.
  1727707 → leave as 1727707
  banjil-kanhil-... → leave as-is
  3:47 → leave as 3:47

ARTICLES: Arkulcis has none. Add "a/an/the" where natural in the raw output.

OUTPUT FORMAT:
- Raw English only. Use [PAST], [PRESENT], [FUTURE] markers after verbs.
- Keep word order natural for English (subject first).
- Do NOT fully naturalise yet — the englishifier will handle that.
- Do NOT add explanations or commentary.

EXAMPLE:
Input:  "noed ni dat kompani losed 1727707 dolars"
Output: "you not know [PAST] that the company lose [PAST] 1727707 dollars"

Input:  "writul bord danbil-fan reportos"
Output: "the board write [FUTURE] danbil-fan reports"
"""


def build_ak_to_en_englishify_prompt() -> str:
    """System prompt for the englishifier (AI pass 2 of 2).

    Takes raw decoded English with tense markers and makes it natural.
    """
    return """You are an English naturaliser. You receive raw decoded text with tense markers.
Your job: transform it into fluent, natural English prose.

TENSE MARKERS → natural English:
  verb [PAST]     → correct past form  (go [PAST] → went, know [PAST] → knew)
  verb [PRESENT]  → correct present form (run [PRESENT] → runs/run)
  verb [FUTURE]   → will + verb  (write [FUTURE] → will write)
  not verb [PAST] → did not + verb  (not know [PAST] → did not know)
  not verb [PRESENT] → do not + verb
  not verb [FUTURE] → will not + verb

IRREGULAR PAST FORMS to restore:
  go [PAST] → went    see [PAST] → saw    think [PAST] → thought
  come [PAST] → came  tell [PAST] → told  know [PAST] → knew
  make [PAST] → made  find [PAST] → found fight [PAST] → fought
  give [PAST] → gave  lose [PAST] → lost  write [PAST] → wrote
  drive [PAST] → drove  wonder [PAST] → wondered  vanish [PAST] → vanished
  force [PAST] → forced  register [PAST] → registered  predict [PAST] → predicted

RESTORE WHAT ARKULCIS DROPS:
  - Add articles (a, an, the) where natural
  - Restore contractions if appropriate (did not → didn't)
  - Restore correct pronouns (pi = he/she/it depending on context)
  - Make plural -os forms natural English plurals (reportos → reports)

QUESTIONS: if the text ends with [QUESTION], rewrite as a proper English
yes/no question (Did/Does/Will + subject + verb) and end with "?".
Remove the [QUESTION] marker itself from the output.
  "she go [PAST] home [QUESTION]" → "Did she go home?"
  "he like [PRESENT] coffee [QUESTION]" → "Does he like coffee?"

OUTPUT: Fluent natural English only. No markers, no brackets, no commentary.
"""

def build_system_prompt() -> str:
    return build_en_to_ak_prompt()


if __name__ == '__main__':
    p1 = build_en_to_ak_prompt()
    p2 = build_ak_to_en_prompt()
    print(f'EN→AK: {len(p1)} chars (~{len(p1)//4} tokens)')
    print(f'AK→EN: {len(p2)} chars (~{len(p2)//4} tokens)')
