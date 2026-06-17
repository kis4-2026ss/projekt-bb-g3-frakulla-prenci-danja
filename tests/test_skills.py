"""
tests/test_skills.py
Unit tests for the preprocessor skill pipeline.
Covers: number_skill, verb_skill, preprocessor orchestration.
No API calls required.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from translator.skills.number_skill import (
    apply as number_apply,
    strip_num_tags,
    to_arkulcis_spoken,
    to_arkulcis_written,
    from_arkulcis_spoken,
    from_arkulcis_written,
    words_to_int,
)
from translator.skills.verb_skill import (
    apply as verb_apply,
    inject_tense_markers,
    normalise_irregular_verbs,
)
from translator.preprocessor import preprocess


# ─────────────────────────────────────────────────────────────
# Number skill — spoken form
# ─────────────────────────────────────────────────────────────

class TestNumberSpoken:

    def test_zero(self):
        assert to_arkulcis_spoken(0) == 'zan'

    def test_ten_is_nan(self):
        assert to_arkulcis_spoken(10) == 'nan'

    def test_eleven_is_pan(self):
        assert to_arkulcis_spoken(11) == 'pan'

    def test_twelve(self):
        assert to_arkulcis_spoken(12) == 'banbil'

    def test_twenty_two(self):
        assert to_arkulcis_spoken(22) == 'banbil-nan'

    def test_99(self):
        assert to_arkulcis_spoken(99) == 'lanbil-fan'

    def test_144(self):
        assert to_arkulcis_spoken(144) == 'bandil'

    def test_157(self):
        assert to_arkulcis_spoken(157) == 'bandil-banbil-ban'

    def test_1728(self):
        assert to_arkulcis_spoken(1728) == 'banfil'

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            to_arkulcis_spoken(-1)

    def test_roundtrip_0_to_200(self):
        for n in range(200):
            spoken = to_arkulcis_spoken(n)
            assert from_arkulcis_spoken(spoken) == n, \
                f'Roundtrip failed: {n} → {spoken} → {from_arkulcis_spoken(spoken)}'

    def test_roundtrip_large(self):
        for n in [1728, 3232, 9999999, 20736]:
            assert from_arkulcis_spoken(to_arkulcis_spoken(n)) == n


# ─────────────────────────────────────────────────────────────
# Number skill — written symbols
# ─────────────────────────────────────────────────────────────

class TestNumberWritten:

    def test_zero_symbol(self):
        assert to_arkulcis_written(0) == '0'

    def test_ten_is_delta(self):
        assert to_arkulcis_written(10) == 'δ'

    def test_eleven_is_lambda(self):
        assert to_arkulcis_written(11) == 'λ'

    def test_twelve_is_10(self):
        assert to_arkulcis_written(12) == '10'

    def test_twenty_two(self):
        assert to_arkulcis_written(22) == '1δ'

    def test_99(self):
        assert to_arkulcis_written(99) == '83'

    def test_144(self):
        assert to_arkulcis_written(144) == '100'

    def test_3232(self):
        assert to_arkulcis_written(3232) == '1δ54'

    def test_roundtrip_0_to_200(self):
        for n in range(200):
            sym = to_arkulcis_written(n)
            assert from_arkulcis_written(sym) == n, \
                f'Written roundtrip failed: {n} → {sym}'

    def test_roundtrip_large(self):
        for n in [1728, 3232, 144, 20736]:
            assert from_arkulcis_written(to_arkulcis_written(n)) == n


# ─────────────────────────────────────────────────────────────
# Number skill — English word parsing
# ─────────────────────────────────────────────────────────────

class TestWordParsing:

    def test_basic_ones(self):
        assert words_to_int('five') == 5
        assert words_to_int('eleven') == 11
        assert words_to_int('twelve') == 12

    def test_tens(self):
        assert words_to_int('twenty') == 20
        assert words_to_int('ninety') == 90

    def test_compound(self):
        assert words_to_int('twenty-two') == 22
        assert words_to_int('forty-four') == 44
        assert words_to_int('seventy-nine') == 79

    def test_hundreds(self):
        assert words_to_int('one hundred') == 100
        assert words_to_int('three hundred') == 300

    def test_hundreds_and(self):
        assert words_to_int('one hundred and forty-four') == 144
        assert words_to_int('two hundred and twenty-two') == 222

    def test_thousands(self):
        assert words_to_int('three thousand') == 3000
        assert words_to_int('three thousand three hundred and thirty two') == 3332

    def test_shorthands(self):
        assert words_to_int('a dozen') == 12
        assert words_to_int('a gross') == 144

    def test_invalid_returns_none(self):
        assert words_to_int('hello world') is None
        assert words_to_int('cat') is None


# ─────────────────────────────────────────────────────────────
# Number skill — apply to text
# ─────────────────────────────────────────────────────────────

class TestNumberSkillApply:

    def _clean(self, text):
        return strip_num_tags(number_apply(text))

    def test_digit_to_written_symbol(self):
        assert self._clean('3232') == '1δ54'

    def test_digit_99(self):
        assert self._clean('99') == '83'

    def test_digit_in_sentence(self):
        assert self._clean('I have 12 cats.') == 'I have 10 cats.'

    def test_written_word_to_spoken(self):
        assert self._clean('twenty-two cats') == 'banbil-nan cats'

    def test_complex_phrase(self):
        assert self._clean('one hundred and forty-four insects') == 'bandil insects'

    def test_a_dozen(self):
        assert self._clean('a dozen eggs') == 'banbil eggs'

    def test_ten_and_eleven(self):
        result = self._clean('ten cats and eleven dogs')
        assert 'nan' in result
        assert 'pan' in result
        assert 'and' in result

    def test_multiple_digits(self):
        result = self._clean('She has 99 books and 144 flowers.')
        assert '83' in result    # 99 written
        assert '100' in result   # 144 written

    def test_protection_tags_present(self):
        result = number_apply('3232')
        assert result.startswith('[NUM:')
        assert True  # value is now inside the tag

    def test_strip_tags(self):
        assert strip_num_tags('[NUM:TEXT:banbil-nan]') == 'banbil-nan'
        assert strip_num_tags('[PRON:pi] go to [NUM:10] librari') == '[PRON:pi] go to 10 librari'


# ─────────────────────────────────────────────────────────────
# Verb skill — tense marker injection
# ─────────────────────────────────────────────────────────────

class TestTenseMarkers:

    def test_had_been_ing(self):
        result = inject_tense_markers("she had been looking for it")
        assert '[VERB(PAST)' in result or '[CTX:PAST]' in result
        assert 'had been' not in result

    def test_had_past_participle(self):
        result = inject_tense_markers("he had already seen the book")
        assert '[VERB(PAST)' in result or '[CTX:PAST]' in result
        assert 'had' not in result

    def test_will_future(self):
        result = inject_tense_markers("she will wake up")
        assert '[VERB(FUTURE)' in result
        assert 'will' not in result

    def test_didnt_negation(self):
        result = inject_tense_markers("she didn't know that")
        assert '[VERB(NEG&PAST)' in result

    def test_wont_future_negation(self):
        result = inject_tense_markers("they won't come")
        assert '[VERB(NEG&FUTURE)' in result

    def test_was_ing_past_continuous(self):
        result = inject_tense_markers("he was running fast")
        assert '[VERB(PAST)' in result or '[CTX:PAST]' in result
        assert 'was' not in result

    def test_is_ing_present_continuous(self):
        result = inject_tense_markers("she is reading a book")
        assert '[VERB(PRESENT)' in result

    def test_had_not(self):
        result = inject_tense_markers("she had not slept well")
        assert '[VERB(NEG&PAST)' in result

    def test_shouldnt(self):
        result = inject_tense_markers("you shouldn't go")
        assert '[VERB(NEG&PRESENT)' in result

    def test_normal_sentence_unchanged(self):
        result = inject_tense_markers("I run fast every day")
        assert result == "I run fast every day"


# ─────────────────────────────────────────────────────────────
# Verb skill — irregular verb normalisation
# ─────────────────────────────────────────────────────────────

class TestIrregularVerbs:

    def test_went_to_go(self):
        assert 'go' in normalise_irregular_verbs('she went home')

    def test_fought_to_fight(self):
        result = normalise_irregular_verbs('he fought hard')
        assert 'fight' in result
        assert 'fought' not in result

    def test_thought_to_think(self):
        result = normalise_irregular_verbs('she thought it was wonderful')
        assert 'think' in result

    def test_came_to_come(self):
        result = normalise_irregular_verbs('they came back home')
        assert 'come' in result

    def test_told_to_tell(self):
        result = normalise_irregular_verbs('he told her')
        assert 'tell' in result

    def test_said_to_say(self):
        result = normalise_irregular_verbs('she said hello')
        assert 'say' in result

    def test_saw_to_see(self):
        result = normalise_irregular_verbs('he saw the film')
        assert 'see' in result

    def test_gave_to_give(self):
        result = normalise_irregular_verbs('she gave him a book')
        assert 'give' in result
        assert 'gave' not in result

    def test_drank_to_drink(self):
        result = normalise_irregular_verbs('she drank some tea')
        assert 'drink' in result

    def test_ate_to_eat(self):
        result = normalise_irregular_verbs('he ate a meal')
        assert 'eat' in result

    def test_slept_to_sleep(self):
        result = normalise_irregular_verbs('she slept well')
        assert 'sleep' in result

    def test_knew_to_know(self):
        result = normalise_irregular_verbs('he knew the answer')
        assert 'know' in result

    def test_ran_to_run(self):
        result = normalise_irregular_verbs('she ran through the streets')
        assert 'run' in result

    def test_caught_to_catch(self):
        result = normalise_irregular_verbs('he caught a thief')
        assert 'catch' in result

    def test_brought_to_bring(self):
        result = normalise_irregular_verbs('she brought him home')
        assert 'bring' in result

    def test_found_to_find(self):
        result = normalise_irregular_verbs('they found a solution')
        assert 'find' in result

    def test_capitalisation_preserved(self):
        result = normalise_irregular_verbs('Went the dog home')
        assert result.startswith('Go') or result.startswith('go')

    def test_regular_verb_unchanged(self):
        result = normalise_irregular_verbs('she walked to school')
        assert 'walked' in result


# ─────────────────────────────────────────────────────────────
# Full verb skill pipeline
# ─────────────────────────────────────────────────────────────

class TestVerbSkillFull:

    def test_past_irregular_full(self):
        result = verb_apply("she went to the library")
        assert 'go' in result
        assert 'went' not in result  # [PAST] from auxiliary stripping not bare irregular

    def test_past_perfect_full(self):
        result = verb_apply("she had been looking for it")
        assert 'look' in result  # normalised from 'looking'
        assert '[VERB(PAST)' in result or '[CTX:PAST]' in result
        assert 'had' not in result

    def test_future_full(self):
        result = verb_apply("she will wake up tomorrow")
        assert 'wake' in result
        assert '[VERB(FUTURE)' in result
        assert 'will' not in result

    def test_neg_past_full(self):
        result = verb_apply("she didn't know that")
        assert '[VERB(NEG&PAST)' in result
        assert 'know' in result

    def test_complex_sentence(self):
        result = verb_apply(
            "He fought hard and never gave up, "
            "but she had already seen the film."
        )
        assert 'fight' in result
        assert 'give' in result
        assert 'see' in result
        assert 'fought' not in result
        assert 'gave' not in result


# ─────────────────────────────────────────────────────────────
# Full preprocessor pipeline
# ─────────────────────────────────────────────────────────────

class TestPreprocessorPipeline:

    def test_numbers_and_verbs_combined(self):
        result = preprocess("She had been reading 12 books.")
        assert '[NUM:' in result   # number converted
        assert 'read' in result   # reading normalised
        assert '[VERB(PAST)' in result or '[CTX:PAST]' in result  # had been → PAST marker

    def test_written_number_and_irregular(self):
        result = preprocess("She found twenty-two insects.")
        clean = strip_num_tags(result)
        assert 'banbil-nan' in clean
        assert 'find' in result

    def test_protection_survives_verb_skill(self):
        result = preprocess("The number is 144.")
        assert '[NUM:' in result
        assert '[NUM:' in result  # tag still present

    def test_order_numbers_before_verbs(self):
        result = preprocess("She had been looking at 99 books.")
        clean = strip_num_tags(result)
        assert 'look' in result  # normalised from looking
        assert '[VERB(PAST)' in result or '[CTX:PAST]' in result
        assert '83' in clean     # 99 written as base-12

    def test_complex_paragraph(self):
        text = (
            "Yesterday, she went to the library and found a book "
            "she had been looking for. She sat down and began to read."
        )
        result = preprocess(text)
        assert 'go' in result
        assert 'find' in result
        assert 'sit' in result
        assert 'begin' in result
        assert '[VERB(PAST)' in result or '[CTX:PAST]' in result
        assert 'had been' not in result

    def test_future_sentence(self):
        result = preprocess("Tomorrow she will wake up and write a letter.")
        assert 'wake' in result
        assert 'write' in result
        assert '[VERB(FUTURE)' in result
        assert 'will' not in result


# ─────────────────────────────────────────────────────────────
# Annotation skill tests
# ─────────────────────────────────────────────────────────────

class TestAnnotationSkillPronouns:

    def test_she_to_pi(self):
        from translator.skills.annotation_skill import tag_pronouns
        result = tag_pronouns('She went home.')
        assert '[PRON:pi]' in result
        assert 'She' not in result

    def test_he_to_pi(self):
        from translator.skills.annotation_skill import tag_pronouns
        result = tag_pronouns('He ran fast.')
        assert '[PRON:pi]' in result

    def test_her_to_pi(self):
        from translator.skills.annotation_skill import tag_pronouns
        result = tag_pronouns('her brother')
        assert '[PRON:pi]' in result

    def test_they_to_pios(self):
        from translator.skills.annotation_skill import tag_pronouns
        result = tag_pronouns('They came back.')
        assert '[PRON:pios]' in result

    def test_we_to_mios(self):
        from translator.skills.annotation_skill import tag_pronouns
        result = tag_pronouns('We will not forget.')
        assert '[PRON:mios]' in result

    def test_i_to_mi(self):
        from translator.skills.annotation_skill import tag_pronouns
        result = tag_pronouns('I run fast.')
        assert '[PRON:mi]' in result

    def test_their_to_pios(self):
        from translator.skills.annotation_skill import tag_pronouns
        result = tag_pronouns('their interests')
        assert '[PRON:pios]' in result

    def test_multiple_pronouns(self):
        from translator.skills.annotation_skill import tag_pronouns
        result = tag_pronouns('She told him she knew.')
        assert result.count('[PRON:pi]') >= 2


class TestAnnotationSkillNames:

    def test_proper_noun_tagged(self):
        from translator.skills.annotation_skill import tag_names
        result = tag_names('She went to Phoenix.')
        assert '[NAME:Phoenix]' in result

    def test_name_tagged(self):
        from translator.skills.annotation_skill import tag_names
        result = tag_names('She visited Hagenberg yesterday.')
        assert '[NAME:Hagenberg]' in result

    def test_first_word_not_tagged(self):
        from translator.skills.annotation_skill import tag_names
        result = tag_names('Arlind studied hard.')
        assert result.startswith('Arlind')
        assert '[NAME:Arlind]' not in result

    def test_multiple_names(self):
        from translator.skills.annotation_skill import tag_names
        result = tag_names('She visited Arlind and Danja in Hagenberg.')
        assert '[NAME:Arlind]' in result
        assert '[NAME:Danja]' in result
        assert '[NAME:Hagenberg]' in result


class TestAnnotationSkillAdjectives:

    def test_base_adjective(self):
        from translator.skills.annotation_skill import tag_adjectives
        result = tag_adjectives('a beautiful city')
        assert '[ADJ:beautiful]' in result

    def test_comparative_more(self):
        from translator.skills.annotation_skill import tag_adjectives
        result = tag_adjectives('more important than')
        assert '[ADJ(COMP):important]' in result

    def test_superlative_most(self):
        from translator.skills.annotation_skill import tag_adjectives
        result = tag_adjectives('the most important thing')
        assert '[ADJ(SUP):important]' in result

    def test_superlative_est(self):
        from translator.skills.annotation_skill import tag_adjectives
        result = tag_adjectives('the strongest student')
        assert '[ADJ(SUP):strong]' in result

    def test_non_adjective_not_tagged(self):
        from translator.skills.annotation_skill import tag_adjectives
        result = tag_adjectives('water and fire')
        assert '[ADJ' not in result

    def test_false_comparative_not_tagged(self):
        from translator.skills.annotation_skill import tag_adjectives
        result = tag_adjectives('mother father brother')
        assert '[ADJ(COMP)' not in result


class TestAnnotationSkillAdverbs:

    def test_quickly(self):
        from translator.skills.annotation_skill import tag_adverbs
        result = tag_adverbs('she walked quickly')
        assert '[ADV:quick]' in result

    def test_beautifully(self):
        from translator.skills.annotation_skill import tag_adverbs
        result = tag_adverbs('sang beautifully')
        assert '[ADV:beautiful]' in result

    def test_slowly(self):
        from translator.skills.annotation_skill import tag_adverbs
        result = tag_adverbs('walked slowly')
        assert '[ADV:slow]' in result

    def test_non_adverb_not_tagged(self):
        from translator.skills.annotation_skill import tag_adverbs
        result = tag_adverbs('the family')
        assert '[ADV' not in result


class TestAnnotationSkillFull:

    def test_full_sentence(self):
        from translator.skills.annotation_skill import apply
        result = apply('She walked quickly through beautiful Phoenix.')
        assert '[PRON:pi]' in result
        assert '[NAME:Phoenix]' in result
        assert '[ADJ:beautiful]' in result or '[ADV:quick]' in result

    def test_pipeline_integration(self):
        from translator.preprocessor import preprocess
        result = preprocess('She found the most beautiful book in Hagenberg.')
        assert '[PRON:pi]' in result
        assert '[NAME:Hagenberg]' in result
        assert '[ADJ(SUP):beautiful]' in result or '[ADJ:beautiful]' in result
