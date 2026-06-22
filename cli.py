"""
arkulcis/cli.py
Interactive command-line interface for the Arkulcis translator.

Run from the project root:
    python cli.py
"""

from translator.translate import translate_to_arkulcis, translate_to_english

# Show debug hint if DEBUG is not set
import os
_DEBUG_ACTIVE = os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')

BANNER = """
╔══════════════════════════════════════════╗
║        Arkulcis Translator CLI           ║
║  The constructed language — EN ↔ AK      ║
╚══════════════════════════════════════════╝
"""

DEBUG_HINT = "  [debug mode ON — pipeline steps visible]\n" if _DEBUG_ACTIVE else              "  tip: set DEBUG=true in .env to see pipeline steps\n"

MENU = """
  1  →  English   →  Arkulcis
  2  →  Arkulcis  →  English
  q  →  Quit
"""


def run():
    print(BANNER)
    print(DEBUG_HINT)

    while True:
        print(MENU)
        choice = input("  Choose an option (1/2/q): ").strip().lower()

        if choice == '1':
            print()
            text = input("  English text: ").strip()
            if not text:
                print("  ⚠ No input provided.\n")
                continue
            print()
            print("  Translating from English to Arkulcis...")
            result = translate_to_arkulcis(text)
            print(f"\n  ✓ Arkulcis: {result}\n")

        elif choice == '2':
            print()
            text = input("  Arkulcis text: ").strip()
            if not text:
                print("  ⚠ No input provided.\n")
                continue
            print()
            print("  Translating from Arkulcis to English...")
            result = translate_to_english(text)
            print(f"\n  ✓ English: {result}\n")

        elif choice == 'q':
            print("\n  Goodbye!\n")
            break

        else:
            print("  ⚠ Invalid option. Please enter 1, 2, or q.\n")


if __name__ == '__main__':
    run()
