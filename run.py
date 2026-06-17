"""
Run this from the project root: python run.py
Demonstrates both translation directions.
"""
from translator.translate import translate_to_arkulcis, translate_to_english

en_examples = [
    'I run fast.',
    'The cats sat on the wooden shelves.',
    'Did she go home?',
    'We will not forget the beautiful city of Phoenix.',
    'They love reading books and exploring new ideas.',
]

ak_examples = [
    'runas mi fastly.',
    'sitas katos on woodenro shelvos.',
    'ka goed pi hom?',
    'no-forgotul mios biutifro siti di Finiks.',
    'luvas pios redas bukos and eksploras newro ideaos.',
]

print('=== English → Arkulcis ===\n')
for s in en_examples:
    print(f'EN: {s}')
    print(f'AK: {translate_to_arkulcis(s)}')
    print()

print('=== Arkulcis → English ===\n')
for s in ak_examples:
    print(f'AK: {s}')
    print(f'EN: {translate_to_english(s)}')
    print()
