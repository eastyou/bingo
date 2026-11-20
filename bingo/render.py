"""把宾果卡渲染成可打印的 A4 页面。"""

from __future__ import annotations

import html
import math
from typing import List, Optional, Sequence

from .model import FREE_MARK, Card, BingoError, call_sheet

PAGE_WIDTH_MM = 210.0
PAGE_HEIGHT_MM = 297.0
CARDS_PER_PAGE = 4
MAX_FONT_PT = {3: 15.0, 4: 12.5, 5: 10.5}


def card_font_pt(card: Card) -> float:
    """按卡片尺寸与最长词条估算字号，保证词不溢出格子。"""
    if not isinstance(card, Card):
        raise BingoError("card 必须是 Card 对象")
    longest = max(len(word) for word in card.words)
    cell_mm = 80.0 / card.size
    width_per_char = 0.3528
    fit = cell_mm * 0.82 / (width_per_char * max(1, longest))
    return round(min(MAX_FONT_PT[card.size], max(4.5, fit)), 1)


def _num(value: float) -> str:
    text = "%.1f" % value
    return text.rstrip("0").rstrip(".") if "." in text else text


def render_card(card: Card, number: int) -> str:
    """生成一张卡片（不含外层纸张）的 HTML。"""
    if not isinstance(card, Card):
        raise BingoError("card 必须是 Card 对象")
    if isinstance(number, bool) or not isinstance(number, int):
        raise BingoError("卡片编号必须是整数")
    if number < 1:
        raise BingoError("卡片编号必须从 1 开始")

    font = _num(card_font_pt(card))
    rows: List[str] = []
    for row in range(card.size):
        cells: List[str] = []
        for col in range(card.size):
            word = card.at(row, col)
            if word == FREE_MARK:
                cells.append('<td class="free">%s</td>' % FREE_MARK)
            else:
                cells.append('<td style="font-size:%spt">%s</td>' % (font, html.escape(word)))
        rows.append("<tr>%s</tr>" % "".join(cells))

    return (
        '<div class="card">'
        '<div class="card-head"><span>第 %d 张</span><span>%d×%d</span></div>'
        '<table class="grid"><tbody>%s</tbody></table>'
        '<div class="card-foot">班级 ________　姓名 ________</div>'
        "</div>" % (number, card.size, card.size, "".join(rows))
    )


def _card_page(
    cards: Sequence[Card], start: int, page: int, total: int, title: str
) -> str:
    blocks: List[str] = []
    for offset in range(CARDS_PER_PAGE):
        position = start + offset
        if position < len(cards):
            blocks.append(render_card(cards[position], position + 1))
        else:
            blocks.append('<div class="card blank"></div>')
    head = (
        '<header class="head"><h1>%s</h1>'
        "<span>%d×%d · 共 %d 张 · 第 %d / %d 页</span></header>"
        % (
            html.escape(title),
            cards[0].size,
            cards[0].size,
            len(cards),
            page,
            total,
        )
    )
    return (
        '<section class="sheet">%s<div class="cards">%s</div>%s</section>'
        % (head, "".join(blocks), _foot("连成一条线（横、竖、斜）即获胜"))
    )


def _foot(text: str) -> str:
    return '<footer class="foot"><span>%s</span><span>bingo · 零依赖打印工具</span></footer>' % html.escape(text)


def _call_page(words: Sequence[str], page: int, total: int) -> str:
    rows = max(1, int(math.ceil(len(words) / 3.0)))
    parts: List[str] = []
    for row in range(rows):
        cells: List[str] = []
        for col in range(3):
            index = col * rows + row
            if index < len(words):
                cells.append(
                    '<td><span class="no">%d</span><span class="box"></span>'
                    '<span class="word">%s</span></td>'
                    % (index + 1, html.escape(words[index]))
                )
            else:
                cells.append("<td></td>")
        parts.append("<tr>%s</tr>" % "".join(cells))
    head = (
        '<header class="head"><h1>叫号单</h1>'
        "<span>共 %d 个词 · 随机顺序 · 第 %d / %d 页</span></header>"
        % (len(words), page, total)
    )
    note = (
        '<p class="note">按编号依次叫词，学生在卡片上划掉；'
        "连成一条线（横、竖、斜）即获胜。叫完可在方框里打勾。</p>"
    )
    return (
        '<section class="sheet call">%s%s'
        '<table class="call"><tbody>%s</tbody></table>%s</section>'
        % (head, note, "".join(parts), _foot("叫号单 · 可单独打印"))
    )


def render_html(
    cards: Sequence[Card],
    title: str = "单词宾果",
    show_call_sheet: bool = True,
    seed: Optional[int] = None,
    call_words: Optional[Sequence[str]] = None,
) -> str:
    """生成完整 HTML：每页 2×2 四张卡，末页可附叫号单。"""
    if not isinstance(cards, (list, tuple)):
        raise BingoError("cards 必须是卡片列表")
    if not cards:
        raise BingoError("至少需要一张宾果卡")
    for card in cards:
        if not isinstance(card, Card):
            raise BingoError("卡片列表里出现了非 Card 对象")
    if len({card.size for card in cards}) != 1:
        raise BingoError("同一份文档里的卡片尺寸必须一致")
    if not isinstance(title, str) or not title.strip():
        raise BingoError("标题不能为空")
    if not isinstance(show_call_sheet, bool):
        raise BingoError("show_call_sheet 必须是布尔值")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise BingoError("随机种子必须是整数")

    if call_words is None:
        words: List[str] = call_sheet(cards, seed=seed)
    else:
        if isinstance(call_words, (str, bytes)):
            raise BingoError("叫号词表必须是词条列表")
        words = []
        for word in call_words:
            if not isinstance(word, str) or not word.strip():
                raise BingoError("叫号词表里出现了空词条")
            words.append(word.strip())

    card_pages = int(math.ceil(len(cards) / float(CARDS_PER_PAGE)))
    total = card_pages + (1 if show_call_sheet else 0)
    sheets: List[str] = []
    for page in range(card_pages):
        sheets.append(
            _card_page(cards, page * CARDS_PER_PAGE, page + 1, total, title.strip())
        )
    if show_call_sheet:
        if not words:
            raise BingoError("叫号单没有可用的词条")
        sheets.append(_call_page(words, total, total))

    toolbar = (
        '<div class="toolbar"><strong>%s</strong>'
        "<span>%d×%d · 共 %d 张 · %s</span></div>"
        % (
            html.escape(title.strip()),
            cards[0].size,
            cards[0].size,
            len(cards),
            "含叫号单" if show_call_sheet else "仅卡片",
        )
    )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n%s\n</body>\n</html>\n"
        % (html.escape(title.strip()), STYLE, toolbar, "\n".join(sheets))
    )


STYLE = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 8mm 0 12mm;
    background: #e2e8f0;
    color: #0f172a;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  .toolbar {
    width: 210mm;
    margin: 0 auto 6mm;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    color: #334155;
    font-size: 13px;
  }
  .toolbar strong { font-size: 15px; letter-spacing: 1px; }
  .toolbar span { color: #64748b; font-size: 12px; }
  .sheet {
    width: 210mm;
    height: 297mm;
    margin: 0 auto 8mm;
    padding: 13mm 15mm 9mm;
    background: #fff;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.14);
    display: flex;
    flex-direction: column;
    page-break-after: always;
    break-after: page;
    overflow: hidden;
  }
  .sheet:last-child { page-break-after: auto; break-after: auto; }
  .head { text-align: center; margin-bottom: 5mm; }
  .head h1 {
    margin: 0 0 1.5mm;
    font-size: 20pt;
    font-weight: 600;
    letter-spacing: 4pt;
  }
  .head span { font-size: 9pt; color: #64748b; letter-spacing: 0.5pt; }
  .cards {
    display: grid;
    grid-template-columns: repeat(2, 87mm);
    grid-template-rows: repeat(2, 100mm);
    gap: 5mm 6mm;
    justify-content: center;
    align-content: start;
  }
  .card {
    border: 0.6mm solid #0f172a;
    border-radius: 2.5mm;
    background: #fff;
    display: flex;
    flex-direction: column;
    padding: 2mm 2.5mm 1.5mm;
    overflow: hidden;
  }
  .card.blank {
    border: 0.25mm dashed #cbd5e1;
    background: #f8fafc;
  }
  .card-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 8pt;
    color: #475569;
    padding: 0 1mm 1mm;
  }
  .card-foot {
    padding: 1.2mm 1mm 0;
    font-size: 7pt;
    color: #94a3b8;
    text-align: center;
  }
  table.grid {
    width: 100%;
    flex: 1;
    table-layout: fixed;
    border-collapse: collapse;
  }
  table.grid td {
    border: 0.25mm solid #94a3b8;
    text-align: center;
    vertical-align: middle;
    padding: 0.5mm;
    overflow: hidden;
    overflow-wrap: anywhere;
    line-height: 1.15;
  }
  table.grid td.free {
    background: #fef3c7;
    color: #b45309;
    font-size: 16pt;
    font-weight: 600;
  }
  .foot {
    margin-top: auto;
    padding-top: 2.5mm;
    display: flex;
    justify-content: space-between;
    font-size: 8pt;
    color: #94a3b8;
    border-top: 0.2mm solid #e2e8f0;
  }
  .note {
    margin: 0 0 4mm;
    padding: 2.5mm 4mm;
    background: #f1f5f9;
    border-left: 1.2mm solid #0f172a;
    font-size: 9pt;
    color: #334155;
    line-height: 1.6;
  }
  table.call { width: 100%; border-collapse: collapse; table-layout: fixed; }
  table.call td {
    border-bottom: 0.2mm solid #e2e8f0;
    padding: 2.6mm 2mm;
    font-size: 10.5pt;
    vertical-align: middle;
    white-space: nowrap;
    overflow: hidden;
  }
  table.call .no {
    display: inline-block;
    width: 8mm;
    color: #94a3b8;
    font-size: 8.5pt;
  }
  table.call .box {
    display: inline-block;
    width: 3.2mm;
    height: 3.2mm;
    border: 0.25mm solid #64748b;
    vertical-align: -0.3mm;
    margin-right: 2mm;
  }
  table.call .word { letter-spacing: 0.5pt; }
  @page { size: A4 portrait; margin: 0; }
  @media print {
    body { background: #fff; padding: 0; }
    .toolbar { display: none; }
    .sheet { margin: 0; box-shadow: none; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""
