[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/5deAuAXI)

# Arkulcis — AI-Assisted Constructed Language Translator

**KIS4 Project | FH Hagenberg | 2026**

Team: Danja Arens · Arlind Frakulla · Erti Prenci

---

## What is Arkulcis?

Arkulcis is a constructed language (conlang) built on one principle:
**one letter = one sound, always.** No silent letters, no irregular forms,
no exceptions. It is structurally similar to English but removes all ambiguity
from spelling, pronunciation, and grammar.

### Core rules at a glance

| Rule | Pattern | Example |
|---|---|---|
| Phonics | 1 letter = 1 sound · no C, Q, X | phone → fon |
| Word order | Verb first, then subject, then rest | runas mi fastly |
| No articles | Drop the / a / an | kat (not "the cat") |
| Pronouns | mi ni pi / mios nios pios | mi = I, pios = they |
| Plural | +os | katos = cats |
| Verbs | -as / -ed / -ul | runas / runed / runul |
| Adjectives | -ro / -rot / -rots | fastro / fastrot / fastrots |
| Adverbs | -ly / -lyt / -lyts | fastly / fastlyt / fastlyts |
| Negation | no- prefix before verb | no-runas mi |
| Questions | ka + verb + subject + rest | ka runas ni? |
| Possession | noun+pronoun or di | katmi / buk di Arlind |
| Casing | Uppercase optional for sentences & names | Runas mi. or runas mi. |
| Numbers | Base-12 | 12=banbil · 99=lanbil-fan · 144=bandil |

### Pronouns

| Singular | | Plural | |
|---|---|---|---|
| mi | I | mios | we |
| ni | you | nios | you all |
| pi | he / she / it | pios | they |

> pi is gender-neutral — no separate he/she in Arkulcis.

### Verb tenses

| Tense | Suffix | Example |
|---|---|---|
| Present | -as | runas (runs / run) |
| Past | -ed | runed (ran) |
| Future | -ul | runul (will run) |

The verb suffix **never changes** based on who is speaking.

### Question word order

```
ka  +  verb  +  subject  +  rest
ka     runas    ni?              →  Do you run?
ka     goed     pi     hom?      →  Did she go home?
ka     komul    pios?            →  Will they come?
```

### Alphabet (23 letters — no C, Q, X)

A B D E F G H I J K L M N O P R S T U V W Y Z

Every letter makes exactly one sound, always.

### Base-12 number system

| Decimal | Arkulcis |
|---|---|
| 0–11 | zan ban dan fan gan han jan kan lan man nan pan |
| 12 | banbil |
| 99 | lanbil-fan |
| 144 | bandil |
| 157 | bandil-banbil-ban |
| 9,999,999 | fanjil-ganhil-dangil-fanfil-hanbil-fan |

---

## Project Goal

Build an AI-assisted **bidirectional** translation system:
- **English → Arkulcis** using a grammar-spec system prompt
- **Arkulcis → English** using a decoding system prompt
- Numbers are always handled by the rule-based `numeral.py`, never the AI

**Validation:** unit tests covering phonetics, numbers, grammar rules,
number pre-conversion, and prompt builder — all passing without any API calls.

---

## How AI Assistance is Used

| Stage | AI Tool | Role |
|---|---|---|
| Language design | ChatGPT / Gemini | Brainstorm vocabulary, edge cases |
| Code writing | GitHub Copilot | Generate boilerplate and helpers |
| Translation engine | Groq API (llama-3.3-70b) | Perform actual translations |
| Test generation | GitHub Copilot | Generate pytest unit tests |
| Documentation | GitHub Copilot | Generate docstrings |

---

## Project Structure

```
but could change
arkulcis/
├── language_spec/
│   ├── grammar_rules.json   ← All Arkulcis grammar rules
│   └── vocabulary.json      ← 150+ words (nouns, verbs, adj, adv, numbers)
├── translator/
│   ├── phonetic.py          ← Rule-based phonetic respelling (EN → AK)
│   ├── numeral.py           ← Base-12 number converter (both directions)
│   ├── prompt_builder.py    ← Builds EN→AK and AK→EN system prompts
│   └── translate.py         ← Bidirectional translation engine (Groq API)
├── document_pipeline/
│   └── doc_translate.py     ← Long document translation (chunked)
├── tests/
│   └── test_translate.py    ← 51 pytest unit tests (no API needed)
├── docs/
│   └── architecture.md      ← System architecture
├── .env.example             ← API key template
├── requirements.txt
├── run.py                   ← Quick run script from project root
└── README.md
```

---

## Setup

### 1. Requirements
- Python 3.11+
- Git
- A GitHub account
- A free Groq API key (no credit card, no expiry)

### 2. Clone and install

```bash
git clone https://github.com/kis4-2026ss/projekt-bb-g3-frakulla-prenci-danja
cd projekt-bb-g3-frakulla-prenci-danja
pip install -r requirements.txt
.env file with GROQ_API_KEY will be needed too
```

### 3. Why Groq API

It is a free option, offers similar experience as Open API the tool can be anything what matters is the usability of it

### 4. Translate English → Arkulcis

```bash
python -m translator.translate
```

### 6. Translate a document

```bash
python document_pipeline/doc_translate.py my_document.txt
```

### 7. Run tests (no API needed)

```bash
pytest tests/
```

---

## Example Translations

### English → Arkulcis

| English | Arkulcis |
|---|---|
| I run fast. | runas mi fastly. |
| The cats sat on the shelves. | sitas katos on shelvos. |
| Did she go home? | ka goed pi hom? |
| We will not forget. | no-forgotul mios. |
| The mind of the people. | mindos di personos. |
| My book. | bukmi. |
| I have 99 books. | runas mi lanbil-fan bukos. |

### Arkulcis → English

| Arkulcis | English |
|---|---|
| runas mi fastly. | I run fast. |
| ka goed pi hom? | Did she go home? |
| no-forgotul mios biutifro siti. | We will not forget the beautiful city. |
| luvas pios redas bukos. | They love reading books. |

---

## Team & Responsibilities

| Member | Student ID | Responsibility |
|---|---|---|
| Danja Arens | S2410307006 | Language design, grammar spec, documentation |
| Arlind Frakulla | S2410307009 | Translation engine, API integration, vocabulary |
| Erti Prenci | S2410307030 | Document pipeline, testing, architecture diagram |

---
