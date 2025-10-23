#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test emoji handler functionality
"""

import sys
import os
import io

# Set UTF-8 encoding for stdout/stderr to handle emoji
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path to import md2pdf
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from md2pdf.emoji_handler import detect_emoji, is_simple_symbol, remove_unsupported_emoji, EmojiHandler


def test_detect_emoji():
    """Test emoji detection"""
    print("Testing emoji detection...")

    # Test cases
    test_cases = [
        ("Hello World", 0, "No emoji"),
        ("Hello 😀 World", 1, "Single emoji"),
        ("✅ Task completed", 1, "Checkmark emoji"),
        ("→ Arrow symbol", 1, "Arrow (should be detected)"),
        ("🎉 🎊 🎈 Party!", 3, "Multiple emoji"),
        ("👨‍💻 Developer", 1, "ZWJ sequence"),
    ]

    for text, expected_count, description in test_cases:
        emoji_list = detect_emoji(text)
        print(f"  {description}: '{text}'")
        print(f"    Found {len(emoji_list)} emoji (expected {expected_count})")
        for emoji, start, end in emoji_list:
            print(f"    - '{emoji}' at position {start}-{end}")
        print()


def test_simple_symbols():
    """Test simple symbol detection"""
    print("Testing simple symbol detection...")

    symbols = [
        ('→', True, "Right arrow"),
        ('←', True, "Left arrow"),
        ('✓', True, "Checkmark"),
        ('✗', True, "X mark"),
        ('😀', False, "Grinning face"),
        ('🎉', False, "Party popper"),
    ]

    for char, expected, description in symbols:
        is_simple = is_simple_symbol(char)
        status = "✓" if is_simple == expected else "✗"
        print(f"  {status} {description}: '{char}' -> {is_simple} (expected {expected})")
    print()


def test_remove_emoji():
    """Test emoji removal"""
    print("Testing emoji removal...")

    test_cases = [
        ("Hello 😀 World", "Hello  World", "Remove emoji, keep text"),
        ("✅ Task done", "✅ Task done", "Keep simple symbols"),
        ("→ Direction", "→ Direction", "Keep arrows"),
        ("🎉 Party 🎊 Time 🎈", " Party  Time ", "Remove multiple emoji"),
    ]

    for input_text, expected, description in test_cases:
        result = remove_unsupported_emoji(input_text, keep_simple_symbols=True)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {description}")
        print(f"    Input:    '{input_text}'")
        print(f"    Output:   '{result}'")
        print(f"    Expected: '{expected}'")
        print()


def test_emoji_handler():
    """Test EmojiHandler class"""
    print("Testing EmojiHandler...")

    # Test with 'remove' strategy (doesn't require Pilmoji)
    handler = EmojiHandler(strategy='remove')

    test_text = "✅ Task completed 🎉\n→ Next step"
    result = handler.process_text(test_text)

    print(f"  Input:  '{test_text}'")
    print(f"  Output: '{result}'")
    print()

    # Try auto strategy
    print("Testing auto strategy (will try Pilmoji, fallback to remove)...")
    handler_auto = EmojiHandler(strategy='auto')
    result_auto = handler_auto.process_text(test_text)
    print(f"  Input:  '{test_text}'")
    print(f"  Output: '{result_auto}'")
    print()

    handler.cleanup()
    handler_auto.cleanup()


if __name__ == '__main__':
    print("=" * 60)
    print("EMOJI HANDLER TEST SUITE")
    print("=" * 60)
    print()

    test_detect_emoji()
    test_simple_symbols()
    test_remove_emoji()
    test_emoji_handler()

    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)
