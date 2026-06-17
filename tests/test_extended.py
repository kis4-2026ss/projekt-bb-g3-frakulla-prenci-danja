"""
tests/test_extended.py
Extended integration tests — extreme sentences and number conversion.
These tests require a GROQ_API_KEY in your .env file to run.
Skip them locally with: pytest tests/ -m "not api"
Run them with:          pytest tests/ -m api
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from translator.numeral import to_arkulcis_number


# ─────────────────────────────────────────────
# Number converter — no API needed
# ─────────────────────────────────────────────

class TestExtendedNumbers:

    def test_99(self):
        assert to_arkulcis_number(99) == 'lanbil-fan'

    def test_9999999(self):
        assert to_arkulcis_number(9999999) == 'fanjil-ganhil-dangil-fanfil-hanbil-fan'

    def test_number_in_sentence(self):
        import re
        def convert(text):
            return re.sub(r'\b\d+\b',
                lambda m: to_arkulcis_number(int(m.group(0))), text)
        assert convert('The number 99 in Arkulcis.') == \
               'The number lanbil-fan in Arkulcis.'
        assert convert('The number 9999999 in Arkulcis.') == \
               'The number fanjil-ganhil-dangil-fanfil-hanbil-fan in Arkulcis.'


# ─────────────────────────────────────────────
# Live API tests — require GROQ_API_KEY
# ─────────────────────────────────────────────

@pytest.mark.api
class TestExtendedTranslation:
    """
    These tests call the Groq API.
    Run with: pytest tests/test_extended.py -m api
    Skip with: pytest tests/ -m "not api"
    """

    @pytest.fixture(autouse=True)
    def skip_without_key(self):
        import os
        from dotenv import load_dotenv
        load_dotenv()
        if not os.getenv('GROQ_API_KEY'):
            pytest.skip('GROQ_API_KEY not set — skipping API tests')

    def test_negation_future(self):
        from translator.translate import translate_to_arkulcis
        result = translate_to_arkulcis(
            'We will not forget the beautiful city of Phoenix.')
        assert 'no-forgotul' in result.lower() or 'forgotul' in result.lower()

    def test_question_word_order(self):
        from translator.translate import translate_to_arkulcis
        result = translate_to_arkulcis('Did she go home?')
        assert result.lower().startswith('ka')

    def test_present_tense(self):
        from translator.translate import translate_to_arkulcis
        result = translate_to_arkulcis('They love reading books.')
        assert 'luvas' in result.lower()

    def test_superlative_adjective(self):
        from translator.translate import translate_to_arkulcis
        result = translate_to_arkulcis(
            'Did the strongest students read all the forgotten books?')
        assert result.lower().startswith('ka')
        assert 'strongrots' in result.lower() or 'strongrot' in result.lower()

    def test_future_negation_adverb(self):
        from translator.translate import translate_to_arkulcis
        result = translate_to_arkulcis(
            'I will not slowly walk from the small house to the big school.')
        assert 'no-walkul' in result.lower() or 'walkul' in result.lower()

    def test_reverse_simple(self):
        from translator.translate import translate_to_english
        result = translate_to_english('runas mi fastly.')
        assert 'run' in result.lower() or 'fast' in result.lower()

    def test_reverse_question(self):
        from translator.translate import translate_to_english
        result = translate_to_english('ka goed pi hom?')
        assert '?' in result
        assert 'home' in result.lower() or 'go' in result.lower()


# ─────────────────────────────────────────────
# Document pipeline test — no API needed
# ─────────────────────────────────────────────

class TestDocumentFixture:

    def test_fixture_exists(self):
        fixture = Path(__file__).parent / 'fixtures' / 'test_document.txt'
        assert fixture.exists(), 'test_document.txt fixture is missing'

    def test_fixture_has_paragraphs(self):
        fixture = Path(__file__).parent / 'fixtures' / 'test_document.txt'
        content = fixture.read_text(encoding='utf-8')
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        assert len(paragraphs) >= 3, 'Expected at least 3 paragraphs'
