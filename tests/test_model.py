"""model 模块单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import List

from bingo.model import (
    FREE_MARK,
    MAX_CARDS,
    BingoError,
    Card,
    call_sheet,
    card_words,
    generate_cards,
    load_words,
    needed_words,
    parse_words,
    shuffle_words,
)

WORDS: List[str] = [
    "苹果", "香蕉", "西瓜", "葡萄", "草莓",
    "铅笔", "尺子", "橡皮", "书包", "课本",
    "老虎", "大象", "猴子", "熊猫", "长颈鹿",
    "足球", "篮球", "排球", "乒乓", "羽毛球",
    "春天", "夏天", "秋天", "冬天", "彩虹",
    "老师", "同学", "教室", "操场", "图书角",
]


def grid(size: int, free: bool = True) -> List[str]:
    words = ["词%02d" % index for index in range(1, size * size + 1)]
    if free and size % 2 == 1:
        words[(size * size) // 2] = FREE_MARK
    return words


class ParseWordsTest(unittest.TestCase):
    def test_plain_lines(self) -> None:
        self.assertEqual(parse_words("苹果\n香蕉\n"), ["苹果", "香蕉"])

    def test_skip_blank_and_comment(self) -> None:
        text = "\n# 这是注释\n苹果\n\n香蕉\n"
        self.assertEqual(parse_words(text), ["苹果", "香蕉"])

    def test_csv_first_column(self) -> None:
        text = "苹果,水果\n香蕉,水果\n"
        self.assertEqual(parse_words(text), ["苹果", "香蕉"])

    def test_duplicate_reports_line(self) -> None:
        with self.assertRaises(BingoError) as ctx:
            parse_words("苹果\n香蕉\n苹果\n")
        self.assertIn("第 3 行", str(ctx.exception))
        self.assertIn("第 1 行", str(ctx.exception))

    def test_word_too_long(self) -> None:
        with self.assertRaises(BingoError) as ctx:
            parse_words("一二三四五六七八九\n")
        self.assertIn("第 1 行", str(ctx.exception))

    def test_empty_text(self) -> None:
        with self.assertRaises(BingoError):
            parse_words("\n# 只有注释\n")

    def test_non_text(self) -> None:
        with self.assertRaises(BingoError):
            parse_words(123)  # type: ignore[arg-type]

    def test_bom_removed(self) -> None:
        self.assertEqual(parse_words("\ufeff苹果\n"), ["苹果"])

    def test_load_utf8_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "words.txt"
            path.write_text("苹果\n香蕉\n", encoding="utf-8")
            self.assertEqual(load_words(path), ["苹果", "香蕉"])

    def test_load_gbk_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "words.txt"
            path.write_bytes("苹果\n香蕉\n".encode("gbk"))
            self.assertEqual(load_words(path), ["苹果", "香蕉"])

    def test_unknown_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "words.txt"
            path.write_bytes(b"\xff\xff\xff")
            with self.assertRaises(BingoError):
                load_words(path)

    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_words("/tmp/definitely-missing-bingo-words.txt")


class CardTest(unittest.TestCase):
    def test_valid_card(self) -> None:
        card = Card(size=5, words=tuple(grid(5)))
        self.assertTrue(card.has_free_center)
        self.assertEqual(card.at(2, 2), FREE_MARK)

    def test_wrong_size(self) -> None:
        with self.assertRaises(BingoError):
            Card(size=6, words=tuple(grid(6)))

    def test_bool_size(self) -> None:
        with self.assertRaises(BingoError):
            Card(size=True, words=tuple(grid(3)))  # type: ignore[arg-type]

    def test_wrong_length(self) -> None:
        with self.assertRaises(BingoError):
            Card(size=5, words=("苹果",))

    def test_empty_word(self) -> None:
        words = grid(5)
        words[0] = " "
        with self.assertRaises(BingoError):
            Card(size=5, words=tuple(words))

    def test_non_text_word(self) -> None:
        words = grid(3)
        words[0] = 1  # type: ignore[list-item]
        with self.assertRaises(BingoError):
            Card(size=3, words=tuple(words))

    def test_missing_center_mark(self) -> None:
        words = grid(5, free=False)
        with self.assertRaises(BingoError):
            Card(size=5, words=tuple(words))

    def test_mark_without_free_center(self) -> None:
        words = grid(5)
        with self.assertRaises(BingoError):
            Card(size=5, words=tuple(words), free_center=False)

    def test_even_size_has_no_center(self) -> None:
        card = Card(size=4, words=tuple(grid(4, free=False)))
        self.assertFalse(card.has_free_center)

    def test_at_out_of_range(self) -> None:
        card = Card(size=3, words=tuple(grid(3)))
        with self.assertRaises(BingoError):
            card.at(3, 0)

    def test_at_negative(self) -> None:
        card = Card(size=3, words=tuple(grid(3)))
        with self.assertRaises(BingoError):
            card.at(-1, 0)

    def test_at_non_int(self) -> None:
        card = Card(size=3, words=tuple(grid(3)))
        with self.assertRaises(BingoError):
            card.at("0", 0)  # type: ignore[arg-type]

    def test_needed_words(self) -> None:
        self.assertEqual(needed_words(5), 24)
        self.assertEqual(needed_words(3), 8)
        self.assertEqual(needed_words(4), 16)
        self.assertEqual(needed_words(5, free_center=False), 25)

    def test_needed_words_bad_size(self) -> None:
        with self.assertRaises(BingoError):
            needed_words(7)


class GenerateCardsTest(unittest.TestCase):
    def test_count_and_unique(self) -> None:
        cards = generate_cards(WORDS, size=5, count=8, seed=7)
        self.assertEqual(len(cards), 8)
        self.assertEqual(len({card.words for card in cards}), 8)
        for card in cards:
            self.assertEqual(len(card.words), 25)
            self.assertEqual(card.at(2, 2), FREE_MARK)

    def test_seed_reproducible(self) -> None:
        first = generate_cards(WORDS, count=6, seed=42)
        second = generate_cards(WORDS, count=6, seed=42)
        self.assertEqual([card.words for card in first], [card.words for card in second])

    def test_different_seed(self) -> None:
        first = generate_cards(WORDS, count=6, seed=1)
        second = generate_cards(WORDS, count=6, seed=2)
        self.assertNotEqual(first[0].words, second[0].words)

    def test_size3(self) -> None:
        cards = generate_cards(WORDS, size=3, count=4, seed=3)
        self.assertEqual(cards[0].size, 3)
        self.assertEqual(cards[0].at(1, 1), FREE_MARK)

    def test_size4(self) -> None:
        cards = generate_cards(WORDS, size=4, count=3, seed=3)
        self.assertEqual(len(cards[0].words), 16)
        self.assertNotIn(FREE_MARK, cards[0].words)

    def test_not_enough_words(self) -> None:
        with self.assertRaises(BingoError) as ctx:
            generate_cards(WORDS[:10], size=5, count=2)
        self.assertIn("24", str(ctx.exception))

    def test_size3_requires_eight(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS[:7], size=3, count=1)

    def test_size4_requires_sixteen(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS[:15], size=4, count=1)

    def test_count_zero(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS, count=0)

    def test_count_too_many(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS, count=MAX_CARDS + 1)

    def test_count_bool(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS, count=True)  # type: ignore[arg-type]

    def test_bad_size(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS, size=6)

    def test_size_bool(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS, size=True)  # type: ignore[arg-type]

    def test_duplicate_words(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(["苹果", "苹果"], size=3, count=1)

    def test_string_words(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards("苹果香蕉", size=3, count=1)  # type: ignore[arg-type]

    def test_empty_words(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards([], size=3, count=1)

    def test_empty_word_item(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS[:7] + [" "], size=3, count=1)

    def test_free_mark_reserved(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS[:7] + [FREE_MARK], size=3, count=1)

    def test_seed_bool(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS, seed=True)  # type: ignore[arg-type]

    def test_free_center_not_bool(self) -> None:
        with self.assertRaises(BingoError):
            generate_cards(WORDS, free_center=1)  # type: ignore[arg-type]

    def test_exact_minimum_words(self) -> None:
        cards = generate_cards(WORDS[:24], size=5, count=10, seed=11)
        self.assertEqual(len(cards), 10)


class CallSheetTest(unittest.TestCase):
    def test_excludes_free_mark(self) -> None:
        cards = generate_cards(WORDS, count=3, seed=5)
        words = call_sheet(cards, seed=5)
        self.assertNotIn(FREE_MARK, words)

    def test_distinct_and_complete(self) -> None:
        cards = generate_cards(WORDS, count=3, seed=5)
        words = call_sheet(cards)
        self.assertEqual(len(words), len(set(words)))
        self.assertEqual(set(words), set(card_words(cards)))

    def test_seed_reproducible(self) -> None:
        cards = generate_cards(WORDS, count=2, seed=9)
        self.assertEqual(call_sheet(cards, seed=9), call_sheet(cards, seed=9))

    def test_unseeded_keeps_set(self) -> None:
        cards = generate_cards(WORDS, count=2, seed=9)
        self.assertEqual(set(call_sheet(cards)), set(card_words(cards)))

    def test_shuffle_empty(self) -> None:
        with self.assertRaises(BingoError):
            shuffle_words([])

    def test_card_words_empty_list(self) -> None:
        with self.assertRaises(BingoError):
            card_words([])

    def test_card_words_non_card(self) -> None:
        with self.assertRaises(BingoError):
            card_words(["苹果"])  # type: ignore[list-item]


if __name__ == "__main__":
    unittest.main()
