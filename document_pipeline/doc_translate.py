"""
arkulcis/document_pipeline/doc_translate.py
Translates a full .txt document to Arkulcis by chunking into paragraphs,
translating each one, and reassembling into an output file.
"""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from translator.translate import translate_to_arkulcis


MAX_WORDS_PER_CHUNK = 80   # Split paragraphs longer than this into sentences


def split_into_sentences(paragraph: str) -> list[str]:
    """Split a long paragraph into individual sentences."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
    return [s for s in sentences if s.strip()]


def chunk_paragraph(paragraph: str) -> list[str]:
    """
    Return paragraph as-is if short enough,
    or split into sentences if too long.
    """
    words = paragraph.split()
    if len(words) <= MAX_WORDS_PER_CHUNK:
        return [paragraph]
    return split_into_sentences(paragraph)


def translate_document(
    input_path: str,
    output_path: str | None = None,
    delay: float = 0.5,
    verbose: bool = True,
) -> str:
    """
    Translate a .txt document from English to Arkulcis.

    Args:
        input_path:  Path to the input .txt file.
        output_path: Path for the output file. If None, auto-generates name.
        delay:       Seconds between API calls (avoids rate limits).
        verbose:     Print progress to console.

    Returns:
        Full translated text as a string.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f'Input file not found: {input_path}')

    if output_path is None:
        output_path = input_file.stem + '_arkulcis.txt'

    with open(input_file, encoding='utf-8') as f:
        raw = f.read()

    # Split into paragraphs on blank lines
    paragraphs = [p.strip() for p in raw.split('\n\n') if p.strip()]

    if verbose:
        print(f'Document loaded: {len(paragraphs)} paragraph(s), '
              f'{len(raw.split())} words total.')
        print(f'Output will be saved to: {output_path}\n')

    translated_paragraphs = []
    total_chunks = sum(len(chunk_paragraph(p)) for p in paragraphs)
    chunk_count = 0

    for para_idx, paragraph in enumerate(paragraphs):
        chunks = chunk_paragraph(paragraph)
        translated_chunks = []

        for chunk in chunks:
            chunk_count += 1
            if verbose:
                print(f'[{chunk_count}/{total_chunks}] '
                      f'Para {para_idx + 1}: {chunk[:60]}...')

            result = translate_to_arkulcis(chunk)
            translated_chunks.append(result)

            if delay > 0:
                time.sleep(delay)

        translated_paragraphs.append(' '.join(translated_chunks))

    full_translation = '\n\n'.join(translated_paragraphs)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_translation)

    if verbose:
        print(f'\nDone! Translated {chunk_count} chunk(s).')
        print(f'Saved to: {output_path}')

    return full_translation


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Translate a .txt document to Arkulcis.'
    )
    parser.add_argument('input',  help='Input .txt file path')
    parser.add_argument('--output', help='Output file path (optional)')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Delay between API calls in seconds (default 0.5)')
    args = parser.parse_args()

    translate_document(args.input, args.output, args.delay)
