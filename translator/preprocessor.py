"""
arkulcis/translator/preprocessor.py

Preprocessor pipeline — applied BEFORE sending text to the AI.
Runs registered skills in order, each transforming the text.

Skills:
  1. number_skill  — converts digit + written English numbers → Arkulcis
  2. verb_skill    — strips auxiliaries, normalises irregular verbs, injects tense markers

The AI receives clean text with:
  - All numbers already in Arkulcis spoken form
  - All auxiliary verbs stripped
  - All irregular verbs replaced with base infinitives
  - Tense markers: [PAST] [PRESENT] [FUTURE] [NEG_PAST] [NEG_PRESENT] [NEG_FUTURE]
"""

from translator.skills.number_skill     import apply as number_skill
from translator.skills.verb_skill       import apply as verb_skill
from translator.skills.annotation_skill import apply as annotation_skill


SKILLS = [
    ('Number Skill',     number_skill),
    ('Verb Skill',       verb_skill),
    ('Annotation Skill', annotation_skill),
]


def preprocess(text: str, verbose: bool = False) -> str:
    """
    Run all skills on input text in order.

    Args:
        text:    Raw English text.
        verbose: If True, print each skill's output for debugging.

    Returns:
        Pre-processed text ready for the AI translator.
    """
    result = text
    for name, skill in SKILLS:
        result = skill(result)
        if verbose:
            print(f'[{name}] → {result}')
    return result


if __name__ == '__main__':
    tests = [
        "She had been looking for a book for twenty-two days.",
        "He fought hard and never gave up.",
        "She said she didn't know that.",
        "One hundred and forty-four insects were found.",
        "Tomorrow she will wake up and write a letter.",
        "He thought it was wonderful.",
        "She had not slept well, so she drank some tea.",
        "They came back home after twelve hours.",
        "A dozen students had already seen the film.",
    ]

    print('=== Preprocessor pipeline output ===\n')
    for t in tests:
        print(f'IN:  {t}')
        print(f'OUT: {preprocess(t, verbose=False)}')
        print()
