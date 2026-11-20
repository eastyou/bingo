"""render 模块单元测试。"""

from __future__ import annotations

import unittest
from typing import List

from bingo.model import Card, BingoError, call_sheet, generate_cards
from bingo.render import (
    CARDS_PER_PAGE,
    card_font_pt,
    render_card,
    render_html,
)

WORDS: List[str] = [
    "苹果", "香蕉", "西瓜", "葡萄", "草莓",
    "铅笔", "尺子", "橡皮", "书包", "课本",
    "老虎", "大象", "猴子", "熊猫", "长颈鹿",
    "足球", "篮球", "排球", "乒乓", "羽毛球",
    "春天", "夏天", "秋天", "冬天", "彩虹",
    "老师", "同学", "教室", "操场", "图书角",
]


class RenderCardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cards = generate_cards(WORDS, size=5, count=5, seed=1)

    def test_contains_grid_and_number(self) -> None:
        markup = render_card(self.cards[0], 1)
        self.assertIn('<div class="card">', markup)
        self.assertIn("第 1 张", markup)
        self.assertIn("5×5", markup)
        self.assertEqual(markup.count("<tr>"), 5)
        self.assertEqual(markup.count("<td"), 25)

    def test_free_cell_markup(self) -> None:
        markup = render_card(self.cards[0], 1)
        self.assertIn('<td class="free">★</td>', markup)

    def test_bad_number(self) -> None:
        for value in (0, -1, True, "1"):
            with self.assertRaises(BingoError):
                render_card(self.cards[0], value)  # type: ignore[arg-type]

    def test_non_card(self) -> None:
        with self.assertRaises(BingoError):
            render_card("苹果", 1)  # type: ignore[arg-type]


class RenderHtmlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cards = generate_cards(WORDS, size=5, count=5, seed=1)

    def test_basic_document(self) -> None:
        page = render_html(self.cards, title="水果宾果", seed=1)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("水果宾果", page)
        self.assertIn("A4 portrait", page)

    def test_card_pages_and_call_sheet(self) -> None:
        page = render_html(self.cards, seed=1)
        pages = page.count('<section class="sheet">')
        self.assertEqual(pages, 2)
        self.assertEqual(page.count('<section class="sheet call">'), 1)
        self.assertIn("叫号单", page)

    def test_four_cards_per_page(self) -> None:
        self.assertEqual(CARDS_PER_PAGE, 4)
        page = render_html(self.cards, seed=1)
        self.assertEqual(page.count('<div class="card">'), 5)
        self.assertEqual(page.count('<div class="card blank">'), 3)

    def test_card_numbers_continue(self) -> None:
        page = render_html(self.cards, seed=1)
        for number in range(1, 6):
            self.assertIn("第 %d 张" % number, page)

    def test_no_call_sheet(self) -> None:
        page = render_html(self.cards, show_call_sheet=False)
        self.assertNotIn("叫号单", page)
        self.assertEqual(page.count('<section class="sheet">'), 2)

    def test_call_sheet_checkboxes(self) -> None:
        page = render_html(self.cards, seed=1)
        expected = len(call_sheet(self.cards, seed=1))
        self.assertEqual(page.count('class="box"'), expected)

    def test_custom_call_words(self) -> None:
        page = render_html(self.cards, call_words=["苹果", "香蕉"])
        self.assertIn('<span class="word">苹果</span>', page)
        self.assertEqual(page.count('class="box"'), 2)

    def test_title_escaped(self) -> None:
        page = render_html(self.cards, title="<宾果>")
        self.assertIn("&lt;宾果&gt;", page)
        self.assertNotIn("<宾果>", page)

    def test_empty_cards(self) -> None:
        with self.assertRaises(BingoError):
            render_html([])

    def test_non_sequence(self) -> None:
        with self.assertRaises(BingoError):
            render_html("卡片")  # type: ignore[arg-type]

    def test_mixed_sizes(self) -> None:
        mixed = self.cards[:1] + generate_cards(WORDS, size=3, count=1, seed=2)
        with self.assertRaises(BingoError):
            render_html(mixed)

    def test_non_card_item(self) -> None:
        with self.assertRaises(BingoError):
            render_html([Card(size=3, words=("a", "b", "c", "d", "★", "e", "f", "g", "h")), "x"])  # type: ignore[list-item]

    def test_empty_title(self) -> None:
        with self.assertRaises(BingoError):
            render_html(self.cards, title="  ")

    def test_bad_show_flag(self) -> None:
        with self.assertRaises(BingoError):
            render_html(self.cards, show_call_sheet=1)  # type: ignore[arg-type]

    def test_bad_seed(self) -> None:
        with self.assertRaises(BingoError):
            render_html(self.cards, seed=True)  # type: ignore[arg-type]

    def test_empty_call_word(self) -> None:
        with self.assertRaises(BingoError):
            render_html(self.cards, call_words=["苹果", " "])

    def test_call_words_string(self) -> None:
        with self.assertRaises(BingoError):
            render_html(self.cards, call_words="苹果")  # type: ignore[arg-type]

    def test_empty_call_words(self) -> None:
        with self.assertRaises(BingoError):
            render_html(self.cards, call_words=[])

    def test_blank_slot_page(self) -> None:
        cards = generate_cards(WORDS, size=4, count=1, seed=4)
        page = render_html(cards, show_call_sheet=False)
        self.assertEqual(page.count('<div class="card blank">'), 3)

    def test_footer_present(self) -> None:
        page = render_html(self.cards, seed=1)
        self.assertIn("连成一条线", page)


class FontTest(unittest.TestCase):
    def test_size5_upper_bound(self) -> None:
        card = generate_cards(WORDS, size=5, count=1, seed=1)[0]
        size = card_font_pt(card)
        self.assertLessEqual(size, 10.5)
        self.assertGreaterEqual(size, 4.5)

    def test_size3_larger(self) -> None:
        three = generate_cards(WORDS, size=3, count=1, seed=1)[0]
        self.assertLessEqual(card_font_pt(three), 15.0)

    def test_long_word_smaller(self) -> None:
        short = generate_cards(WORDS, size=5, count=1, seed=1)[0]
        long_words = ["一二三四五六七八"] * 24
        long_card = Card(size=5, words=tuple(long_words[:12] + ["★"] + long_words[12:]))
        self.assertLess(card_font_pt(long_card), card_font_pt(short))

    def test_non_card(self) -> None:
        with self.assertRaises(BingoError):
            card_font_pt("x")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
