"""
arkulcis/translator/translate.py
Bidirectional translation engine: English ↔ Arkulcis.
Uses the Groq API (completely free, no credit card, no expiry).
Numbers are converted via the rule-based numeral.py, not the AI.

Free API key: https://console.groq.com → sign in with Google → API Keys
"""

import os
import re
import time
from groq import Groq
from groq import (
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
    APIStatusError,
)
from dotenv import load_dotenv
from translator.prompt_builder import build_en_to_ak_prompt, build_ak_to_en_prompt
from translator.numeral import to_arkulcis_number, from_arkulcis_number
from translator.preprocessor import preprocess
from translator.skills.number_skill import strip_num_tags

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Set DEBUG=true in your .env or environment to see intermediary pipeline steps
DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')


def _debug(label: str, value: str) -> None:
    """Print a debug step if DEBUG mode is enabled."""
    if not DEBUG:
        return
    border = '─' * 60
    print(f'\n\033[90m{border}')
    print(f'[DEBUG] {label}')
    print(border)
    print(value)
    print(f'{border}\033[0m')

# Load both prompts once at startup
_EN_TO_AK_PROMPT = build_en_to_ak_prompt()
_AK_TO_EN_PROMPT = build_ak_to_en_prompt()


def convert_numbers_in_text(text: str) -> str:
    """Replace all decimal integers in text with Arkulcis number words.
    e.g. 'I have 99 books' → 'I have lanbil-fan books'
    """
    def replace_number(match: re.Match) -> str:
        return to_arkulcis_number(int(match.group(0)))
    return re.sub(r'\b\d+\b', replace_number, text)


def _friendly_error(e: Exception) -> str:
    """Convert a Groq API exception into a clear, human-readable message."""
    if isinstance(e, AuthenticationError):
        return (
            'Invalid API key.\n'
            '  → Check your GROQ_API_KEY in the .env file.\n'
            '  → Get a free key at: https://console.groq.com'
        )
    if isinstance(e, RateLimitError):
        msg = str(e)
        # Extract retry time if present
        retry_hint = ''
        if 'Please try again in' in msg:
            try:
                retry_part = msg.split('Please try again in')[1].split('.')[0].strip()
                retry_hint = f'\n  → Retry in {retry_part}.'
            except Exception:
                pass
        # Distinguish daily vs per-minute limit
        if 'tokens per day' in msg or 'TPD' in msg:
            return (
                f'Daily token limit reached.{retry_hint}\n'
                '  → Free tier allows 100,000 tokens/day on llama-3.3-70b.\n'
                '  → Wait until tomorrow or reduce the size of your input.'
            )
        if 'prepayment' in msg.lower() or 'credits' in msg.lower():
            return (
                'Prepay credits depleted.\n'
                '  → Your API key was set up with paid credits that have run out.\n'
                '  → Create a new FREE key at: https://console.groq.com\n'
                '  → On the new-key page, do NOT add billing — free tier is automatic.'
            )
        return (
            f'Rate limit exceeded.{retry_hint}\n'
            '  → Free tier: 15 requests/minute, 100k tokens/day.\n'
            '  → Wait a moment and try again.'
        )
    if isinstance(e, APIConnectionError):
        return (
            'Could not connect to Groq API.\n'
            '  → Check your internet connection.\n'
            '  → Groq status: https://status.groq.com'
        )
    if isinstance(e, APIStatusError):
        code = e.status_code
        if code == 404:
            return (
                f'Model not found (404).\n'
                '  → The model name may have changed.\n'
                '  → Current model in use: llama-3.3-70b-versatile\n'
                '  → Check available models at: https://console.groq.com/docs/models'
            )
        if code == 503:
            return (
                'Groq API is temporarily unavailable (503).\n'
                '  → This is a server-side issue, not your fault.\n'
                '  → Check status at: https://status.groq.com\n'
                '  → Try again in a few minutes.'
            )
        return f'API error {code}: {e.message}'
    # Fallback for unexpected errors
    return f'Unexpected error: {type(e).__name__}: {e}'


def _call_api(system_prompt: str, text: str,
              retries: int, delay: float) -> str:
    """Internal helper — calls Groq API with friendly error handling."""
    last_error = None

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user',   'content': text},
                ]
            )
            result = (response.choices[0].message.content or '').strip()
            return strip_num_tags(result)

        except (AuthenticationError, RateLimitError,
                APIConnectionError, APIStatusError) as e:
            last_error = e
            friendly = _friendly_error(e)
            # Don't retry auth errors or daily limits — they won't recover
            if isinstance(e, AuthenticationError):
                print(f'\n❌ Authentication error:\n   {friendly}\n')
                break
            if isinstance(e, RateLimitError) and (
                'tokens per day' in str(e) or
                'TPD' in str(e) or
                'prepayment' in str(e).lower()
            ):
                print(f'\n❌ Quota error:\n   {friendly}\n')
                break
            # Retryable errors
            print(f'\n⚠ Attempt {attempt + 1}/{retries}: {friendly}')
            if attempt < retries - 1:
                print(f'  Retrying in {delay}s...\n')
                time.sleep(delay)

        except Exception as e:
            last_error = e
            print(f'\n⚠ Attempt {attempt + 1}/{retries}: {_friendly_error(e)}')
            if attempt < retries - 1:
                time.sleep(delay)

    friendly_final = _friendly_error(last_error) if last_error else 'Unknown error'
    print(f'\n❌ Translation failed after {retries} attempt(s):\n   {friendly_final}\n')
    return f'[Translation failed: {type(last_error).__name__}]'


def translate_to_arkulcis(text: str, retries: int = 3,
                           delay: float = 1.0) -> str:
    """Translate English → Arkulcis.
    Numbers are pre-converted by the rule-based converter.

    Args:
        text:    English input text.
        retries: Retry attempts on API failure.
        delay:   Seconds between retries.

    Returns:
        Arkulcis translation string, or an error message if it fails.
    """
    if not text.strip():
        return ''
    _debug('STEP 1 — Original input', text)

    # Skill 1: number conversion
    from translator.skills.number_skill import apply as num_skill
    after_numbers = num_skill(text)
    _debug('STEP 2 — After number skill (digits→symbols, words→spoken)', after_numbers)

    # Skill 2: verb normalisation + tense markers
    from translator.skills.verb_skill import apply as verb_skill
    after_verbs = verb_skill(after_numbers)
    _debug('STEP 3 — After verb skill (irregular→infinitive, tense markers)', after_verbs)

    # Skill 3: semantic annotation
    from translator.skills.annotation_skill import apply as ann_skill
    after_annotation = ann_skill(after_verbs)
    _debug('STEP 4 — After annotation skill (pronouns, names, adj, adv)', after_annotation)

    # Strip number tags before AI
    text_for_ai = strip_num_tags(after_annotation)
    _debug('STEP 5 — Sent to AI (NUM tags stripped, all other tags intact)', text_for_ai)

    result = _call_api(_EN_TO_AK_PROMPT, text_for_ai, retries, delay)
    _debug('STEP 6 — AI output (Arkulcis)', result)
    return result


def translate_to_english(text: str, retries: int = 3,
                          delay: float = 1.0) -> str:
    """Translate Arkulcis → English.

    Args:
        text:    Arkulcis input text.
        retries: Retry attempts on API failure.
        delay:   Seconds between retries.

    Returns:
        English translation string, or an error message if it fails.
    """
    if not text.strip():
        return ''
    _debug('STEP 1 — Arkulcis input', text)

    # Pass 1: AI decoder — Arkulcis → raw English with tense markers
    raw = _call_api(_AK_TO_EN_PROMPT, text, retries, delay)
    _debug('STEP 2 — AI decoder output (raw English + tense markers)', raw)

    # Pass 2: Python post-processor — convert numbers, restore pronouns
    from translator.skills.ak_decoder_skill import apply as ak_postprocess
    processed = ak_postprocess(raw)
    _debug('STEP 3 — After Python post-processor (numbers + pronouns)', processed)

    # Pass 3: AI englishifier — make it natural
    from translator.prompt_builder import build_ak_to_en_englishify_prompt
    _AK_ENGLISHIFY_PROMPT = build_ak_to_en_englishify_prompt()
    natural = _call_api(_AK_ENGLISHIFY_PROMPT, processed, retries, delay)
    _debug('STEP 4 — Englishified output', natural)
    return natural


def translate_batch_to_arkulcis(sentences: list[str]) -> list[str]:
    """Translate a list of English sentences to Arkulcis."""
    results = []
    for i, s in enumerate(sentences):
        print(f'[{i+1}/{len(sentences)}] EN→AK: {s[:55]}...')
        results.append(translate_to_arkulcis(s))
        if i < len(sentences) - 1:
            time.sleep(0.5)
    return results


def translate_batch_to_english(sentences: list[str]) -> list[str]:
    """Translate a list of Arkulcis sentences to English."""
    results = []
    for i, s in enumerate(sentences):
        print(f'[{i+1}/{len(sentences)}] AK→EN: {s[:55]}...')
        results.append(translate_to_english(s))
        if i < len(sentences) - 1:
            time.sleep(0.5)
    return results


if __name__ == '__main__':
    en_examples = [
        'I run fast.',
        'The cats sat on the wooden shelves.',
        'Did she go home?',
        'We will not forget the beautiful city of Phoenix.',
        'They love reading books and exploring new ideas.',
        'I have 99 books on my shelf.',
    ]

    ak_examples = [
        'runas mi fastly.',
        'sitas katos on woodenro shelvos.',
        'ka goed pi hom?',
        'no-forgotul mios biutifro siti di Finiks.',
        'luvas pios redas bukos and eksploras newro ideaos.',
        'lanbil-fan bukos ias on shelfmi.',
    ]

    print('=== Arkulcis Translator (Groq — free forever) ===\n')
    print('── English → Arkulcis ──────────────────────────\n')
    for sentence in en_examples:
        result = translate_to_arkulcis(sentence)
        print(f'EN: {sentence}')
        print(f'AK: {result}')
        print()

    print('── Arkulcis → English ──────────────────────────\n')
    for sentence in ak_examples:
        result = translate_to_english(sentence)
        print(f'AK: {sentence}')
        print(f'EN: {result}')
        print()
