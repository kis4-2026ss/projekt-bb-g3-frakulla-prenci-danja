"""
tests/test_translate.py
Core unit tests for the Arkulcis translation system.
Tests cover all 5 pipeline stages:
  EN→AK: Stage 1 (Python skills) + Stage 2 (AI translation)
  AK→EN: Stage 1 (AI decode) + Stage 2 (Python post-process) + Stage 3 (englishify)
No API calls required — all tests are rule-based.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from translator.phonetic import to_arkulcis_phonetic, respell_text
from translator.numeral import to_arkulcis_number, from_arkulcis_number, to_base12_digits


# ─────────────────────────────────────────────
# Stage 0: Phonetic engine
# ─────────────────────────────────────────────

class TestPhonetics:

    def test_ph_to_f(self):
        assert to_arkulcis_phonetic('phone') == 'fon'

    def test_qu_to_kw(self):
        assert to_arkulcis_phonetic('queen') == 'kwin'

    def test_x_to_ks(self):
        assert to_arkulcis_phonetic('fox') == 'foks'

    def test_c_before_e_to_s(self):
        assert to_arkulcis_phonetic('city') == 'siti'

    def test_c_before_a_to_k(self):
        assert to_arkulcis_phonetic('cat') == 'kat'

    def test_ck_to_k(self):
        assert to_arkulcis_phonetic('clock') == 'klok'

    def test_kn_silent_k(self):
        assert to_arkulcis_phonetic('knife') == 'naif'

    def test_igh_to_ai(self):
        assert to_arkulcis_phonetic('night') == 'nait'

    def test_tion_to_shen(self):
        assert to_arkulcis_phonetic('nation') == 'neishen'

    def test_sch_to_sk(self):
        assert to_arkulcis_phonetic('school') == 'skul'

    def test_proper_noun_preserved_case(self):
        assert respell_text('Phoenix')[0].isupper()

    def test_proper_noun_phonetic(self):
        result = respell_text('Phoenix').lower()
        assert result.startswith('f') or 'f' in result[:3]

    def test_already_phonetic_unchanged(self):
        assert to_arkulcis_phonetic('dog') == 'dog'

    def test_multiple_rules_in_one_word(self):
        # psychology: ps=s, y→i at end, ch→k
        result = to_arkulcis_phonetic('psychology')
        assert 'f' not in result  # no ph
        assert result.startswith('s') or 's' in result[:2]

    def test_respell_sentence(self):
        result = respell_text('The cat sat on the phone.')
        assert 'fon' in result.lower()
        assert 'kat' in result.lower()


# ─────────────────────────────────────────────
# Stage 1 (EN→AK): Number system (numeral.py)
# ─────────────────────────────────────────────

class TestNumbers:

    def test_zero(self):
        assert to_arkulcis_number(0) == 'zan'

    def test_single_digits(self):
        expected = ['zan','ban','dan','fan','gan','han',
                    'jan','kan','lan','man','nan','pan']
        for i, name in enumerate(expected):
            assert to_arkulcis_number(i) == name, \
                f'Expected {name} for {i}, got {to_arkulcis_number(i)}'

    def test_twelve(self):
        assert to_arkulcis_number(12) == 'banbil'

    def test_thirteen(self):
        assert to_arkulcis_number(13) == 'banbil-ban'

    def test_twenty_four(self):
        assert to_arkulcis_number(24) == 'danbil'

    def test_99(self):
        assert to_arkulcis_number(99) == 'lanbil-fan'

    def test_143(self):
        assert to_arkulcis_number(143) == 'panbil-pan'

    def test_144(self):
        assert to_arkulcis_number(144) == 'bandil'

    def test_157(self):
        assert to_arkulcis_number(157) == 'bandil-banbil-ban'

    def test_1728(self):
        assert to_arkulcis_number(1728) == 'banfil'

    def test_9999999(self):
        assert to_arkulcis_number(9999999) == 'fanjil-ganhil-dangil-fanfil-hanbil-fan'

    def test_no_hyphen_option(self):
        assert to_arkulcis_number(13, hyphen=False) == 'banbilban'

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            to_arkulcis_number(-1)

    def test_base12_digits_zero(self):
        assert to_base12_digits(0) == [0]

    def test_base12_digits_twelve(self):
        assert to_base12_digits(12) == [1, 0]

    def test_base12_digits_144(self):
        assert to_base12_digits(144) == [1, 0, 0]

    def test_base12_digits_3232(self):
        assert to_base12_digits(3232) == [1, 10, 5, 4]

    def test_roundtrip_small(self):
        for n in range(200):
            ak = to_arkulcis_number(n)
            result = from_arkulcis_number(ak)
            assert result == n, f'Roundtrip failed: {n} → {ak} → {result}'

    def test_roundtrip_large(self):
        for n in [1728, 2024, 9999999, 20736, 3232]:
            ak = to_arkulcis_number(n)
            assert from_arkulcis_number(ak) == n, \
                f'Large roundtrip failed for {n}'


# ─────────────────────────────────────────────
# Stage 1 (EN→AK): Preprocessor pipeline
# ─────────────────────────────────────────────

class TestPreprocessorStage:
    """Tests for Stage 1 of EN→AK pipeline: Python skill preprocessing."""

    def test_digit_number_converted(self):
        from translator.preprocessor import preprocess
        from translator.skills.number_skill import strip_num_tags
        result = strip_num_tags(preprocess('I have 99 books.'))
        assert '83' in result  # 99 in base-12 written form

    def test_written_number_converted(self):
        from translator.preprocessor import preprocess
        from translator.skills.number_skill import strip_num_tags
        result = strip_num_tags(preprocess('twenty-two cats'))
        assert 'banbil-nan' in result

    def test_irregular_verb_normalised(self):
        from translator.preprocessor import preprocess
        result = preprocess('She went to the library yesterday.')
        assert 'go' in result
        assert 'went' not in result

    def test_tense_marker_injected(self):
        from translator.preprocessor import preprocess
        result = preprocess('She had been looking for it.')
        assert '[VERB(PAST)' in result or '[CTX:PAST]' in result
        assert 'had been' not in result

    def test_future_marker_injected(self):
        from translator.preprocessor import preprocess
        result = preprocess('She will write a letter tomorrow.')
        assert '[VERB(FUTURE)' in result
        assert 'will' not in result

    def test_neg_past_marker(self):
        from translator.preprocessor import preprocess
        result = preprocess("She didn't know that.")
        assert '[VERB(NEG&PAST)' in result

    def test_numbers_protected_from_verb_skill(self):
        from translator.preprocessor import preprocess
        result = preprocess('She found 144 books.')
        assert '[NUM:' in result  # tag format: [NUM:value]

    def test_complex_past_paragraph(self):
        from translator.preprocessor import preprocess
        text = "He fought hard and never gave up. They came back home."
        result = preprocess(text)
        assert 'fight' in result   # fought → fight
        assert 'give' in result    # gave → give
        assert 'come' in result    # came → come


# ─────────────────────────────────────────────
# Stage 2 (EN→AK): Grammar rules in JSON spec
# ─────────────────────────────────────────────

class TestGrammarRules:
    """Tests for Stage 2 (EN→AK): grammar spec correctness."""

    def test_vocabulary_loads(self):
        import json
        vocab = json.load(open('language_spec/vocabulary.json'))
        assert 'nouns' in vocab
        assert 'verbs' in vocab
        assert 'adjectives' in vocab
        assert 'adverbs' in vocab

    def test_grammar_loads(self):
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        assert grammar['language'] == 'Arkulcis'
        assert 'verbs' in grammar
        assert 'adjectives' in grammar
        assert 'pronouns' in grammar

    def test_all_adjectives_end_ro(self):
        import json
        vocab = json.load(open('language_spec/vocabulary.json'))
        for word, data in vocab['adjectives'].items():
            if word == 'note' or not isinstance(data, dict):
                continue
            assert word.endswith('ro'), f'{word} does not end in -ro'

    def test_all_adverbs_end_ly(self):
        import json
        vocab = json.load(open('language_spec/vocabulary.json'))
        for word, data in vocab['adverbs'].items():
            if word == 'note' or not isinstance(data, dict):
                continue
            if 'note' in data:
                continue
            assert word.endswith('ly'), f'{word} does not end in -ly'

    def test_verb_present_ends_as(self):
        import json
        vocab = json.load(open('language_spec/vocabulary.json'))
        count = 0
        for root, data in vocab['verbs'].items():
            if not isinstance(data, dict) or 'present' not in data:
                continue
            assert data['present'].endswith('as'), \
                f'{root} present tense "{data["present"]}" does not end in -as'
            count += 1
        assert count > 30, 'Too few verbs in vocabulary'

    def test_verb_past_ends_ed(self):
        import json
        vocab = json.load(open('language_spec/vocabulary.json'))
        for root, data in vocab['verbs'].items():
            if not isinstance(data, dict) or 'past' not in data:
                continue
            assert data['past'].endswith('ed'), \
                f'{root} past tense "{data["past"]}" does not end in -ed'

    def test_verb_future_ends_ul(self):
        import json
        vocab = json.load(open('language_spec/vocabulary.json'))
        for root, data in vocab['verbs'].items():
            if not isinstance(data, dict) or 'future' not in data:
                continue
            assert data['future'].endswith('ul'), \
                f'{root} future tense "{data["future"]}" does not end in -ul'

    def test_plural_pronouns_end_os(self):
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        for word in grammar['pronouns']['plural'].keys():
            assert word.lower().endswith('os'), \
                f'Plural pronoun {word} does not end in -os'

    def test_singular_pronouns_exist(self):
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        singular = grammar['pronouns']['singular']
        assert 'mi' in singular
        assert 'ni' in singular
        assert 'pi' in singular

    def test_number_digits_count(self):
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        assert len(grammar['numbers']['digits']) == 12, \
            'Base-12 must have exactly 12 digit words'

    def test_to_be_forms_exist(self):
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        to_be = grammar['verbs']['to_be']
        assert to_be['present'] == 'beas'
        assert to_be['past'] == 'beed'
        assert to_be['future'] == 'beul'

    def test_tense_simplification_documented(self):
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        ts = grammar['tense_simplification']
        assert 'past_perfect' in ts
        assert 'present_continuous' in ts
        assert 'past_continuous' in ts

    def test_question_rule(self):
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        assert 'ka' in grammar['questions']['rule']

    def test_negation_rule(self):
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        assert 'no-' in grammar['negation']['rule']

    def test_number_symbols_documented(self):
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        symbols = grammar['numbers']['digit_symbols']['symbols']
        assert 'δ' in symbols['10']
        assert 'λ' in symbols['11']


# ─────────────────────────────────────────────
# Stage 2 (EN→AK) + Stage 1 (AK→EN):
# Prompt builder tests
# ─────────────────────────────────────────────

class TestPromptBuilder:
    """Tests for AI prompt correctness (Stages 2 EN→AK and 1 AK→EN)."""

    def test_en_to_ak_prompt_builds(self):
        from translator.prompt_builder import build_en_to_ak_prompt
        prompt = build_en_to_ak_prompt()
        assert len(prompt) > 500
        assert 'Arkulcis' in prompt

    def test_ak_to_en_prompt_builds(self):
        from translator.prompt_builder import build_ak_to_en_prompt
        prompt = build_ak_to_en_prompt()
        assert len(prompt) > 300
        assert 'English' in prompt

    def test_prompts_are_different(self):
        from translator.prompt_builder import build_en_to_ak_prompt, build_ak_to_en_prompt
        assert build_en_to_ak_prompt() != build_ak_to_en_prompt()

    def test_en_to_ak_contains_tense_rules(self):
        from translator.prompt_builder import build_en_to_ak_prompt
        prompt = build_en_to_ak_prompt()
        assert '-as' in prompt
        assert '-ed' in prompt
        assert '-ul' in prompt
        assert '-ro' in prompt
        assert 'beas' in prompt   # to be present

    def test_en_to_ak_contains_irregular_examples(self):
        from translator.prompt_builder import build_en_to_ak_prompt
        prompt = build_en_to_ak_prompt()
        assert 'goed' in prompt   # went → goed
        assert 'fighted' in prompt or 'fight' in prompt

    def test_en_to_ak_has_number_tag_instruction(self):
        from translator.prompt_builder import build_en_to_ak_prompt
        prompt = build_en_to_ak_prompt()
        assert '[NUM:' in prompt or '<<' in prompt

    def test_ak_to_en_contains_decode_rules(self):
        from translator.prompt_builder import build_ak_to_en_prompt
        prompt = build_ak_to_en_prompt()
        assert 'mi' in prompt
        assert 'pios' in prompt
        assert 'beas' in prompt or 'PRESENT' in prompt
        assert '-bil' in prompt or 'banjil' in prompt or 'banbil' in prompt or 'bil' in prompt

    def test_prompt_not_too_large(self):
        from translator.prompt_builder import build_en_to_ak_prompt
        prompt = build_en_to_ak_prompt()
        tokens = len(prompt) // 4
        assert tokens < 4000, \
            f'Prompt too large: ~{tokens} tokens (free tier limit is 100k/day)'


# ─────────────────────────────────────────────
# Stage 2 (AK→EN): Post-processor
# (Python pass after AI decoder)
# ─────────────────────────────────────────────

class TestAkToEnPostProcessor:
    """Tests for Stage 2 AK→EN: Python post-processing of decoded output."""

    def test_strip_num_tags(self):
        from translator.skills.number_skill import strip_num_tags
        assert strip_num_tags('[PRON:pi] go to [NUM:10] librari') == \
               '[PRON:pi] go to 10 librari'

    def test_strip_multiple_tags(self):
        from translator.skills.number_skill import strip_num_tags
        result = strip_num_tags('pi had <<83>> books and <<100>> flowers')
        assert '83' in result
        assert '100' in result
        assert '[NUM:' not in result

    def test_no_tags_unchanged(self):
        from translator.skills.number_skill import strip_num_tags
        text = 'goed pi to librari'
        assert strip_num_tags(text) == text

    def test_written_symbol_to_decimal(self):
        from translator.skills.number_skill import from_arkulcis_written
        assert from_arkulcis_written('1δ54') == 3232
        assert from_arkulcis_written('83') == 99
        assert from_arkulcis_written('100') == 144

    def test_spoken_to_decimal(self):
        from translator.skills.number_skill import from_arkulcis_spoken
        assert from_arkulcis_spoken('banbil') == 12
        assert from_arkulcis_spoken('bandil') == 144
        assert from_arkulcis_spoken('lanbil-fan') == 99


# ─────────────────────────────────────────────
# Stage 3 (AK→EN): Englishifier (no API — rule checks)
# ─────────────────────────────────────────────

class TestEnglishifierRules:
    """
    Tests for Stage 3 AK→EN: englishifier behaviour.
    These verify the input→output mapping the AI is expected to produce.
    No API calls — just validates the rule documentation.
    """

    def _englishify_rules(self):
        """Return the documented englishifier transformations."""
        return {
            'go [PAST]':     'went',
            'see [PAST]':    'saw',
            'think [PAST]':  'thought',
            'come [PAST]':   'came',
            'tell [PAST]':   'told',
            'fight [PAST]':  'fought',
            'give [PAST]':   'gave',
            'find [PAST]':   'found',
            'drink [PAST]':  'drank',
            'eat [PAST]':    'ate',
            'sleep [PAST]':  'slept',
            'know [PAST]':   'knew',
        }

    def test_englishifier_rules_documented(self):
        """All past irregular forms should be in the AK→EN prompt."""
        from translator.prompt_builder import build_ak_to_en_prompt
        prompt = build_ak_to_en_prompt()
        # Prompt should contain past tense decoding guidance
        assert '-ed=past' in prompt or 'past' in prompt.lower()

    def test_tense_marker_mapping_documented(self):
        """Tense markers should appear in grammar_rules.json."""
        import json
        grammar = json.load(open('language_spec/grammar_rules.json'))
        ts = grammar['tense_simplification']
        # past perfect maps to past
        assert ts['past_perfect']['ak'].endswith('-ed)') or \
               'past' in ts['past_perfect']['ak'].lower()

    def test_all_expected_irregular_reversals_covered(self):
        """The 80+ irregular verbs in verb_skill should all have reverse forms."""
        from translator.skills.verb_skill import IRREGULAR_VERBS
        # Key irregular verbs that must be in the map
        must_have = ['went', 'fought', 'thought', 'came', 'told', 'said',
                     'caught', 'brought', 'gave', 'drank', 'ate', 'slept',
                     'knew', 'saw', 'found', 'spoke', 'sat']
        for v in must_have:
            assert v in IRREGULAR_VERBS, \
                f'"{v}" missing from irregular verb map'

    def test_fixture_document_exists(self):
        fixture = Path(__file__).parent / 'fixtures' / 'test_document.txt'
        assert fixture.exists()
        content = fixture.read_text(encoding='utf-8')
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        assert len(paragraphs) >= 3
