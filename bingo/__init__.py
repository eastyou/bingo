"""bingo：A4 可打印课堂宾果卡。"""

from __future__ import annotations

from .model import (
    FREE_MARK,
    MAX_CARDS,
    MAX_WORD,
    SIZES,
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
from .render import CARDS_PER_PAGE, card_font_pt, render_card, render_html

__version__ = "0.1.0"

__all__ = [
    "CARDS_PER_PAGE",
    "FREE_MARK",
    "MAX_CARDS",
    "MAX_WORD",
    "SIZES",
    "BingoError",
    "Card",
    "call_sheet",
    "card_font_pt",
    "card_words",
    "generate_cards",
    "load_words",
    "needed_words",
    "parse_words",
    "render_card",
    "render_html",
    "shuffle_words",
    "__version__",
]
