"""命令行入口：生成可打印的宾果卡与叫号单。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from .model import MAX_CARDS, Card, BingoError, generate_cards, load_words
from .render import CARDS_PER_PAGE, render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bingo",
        description="课堂宾果卡：从词表生成 A4 可打印卡片与叫号单",
    )
    parser.add_argument("--version", action="version", version="bingo 0.1.0")
    parser.add_argument(
        "-i", "--input", required=True, help="词表文件，每行一个词（CSV 取首列）"
    )
    parser.add_argument(
        "-o", "--output", default="宾果.html", help="输出 HTML 路径"
    )
    parser.add_argument(
        "--size", type=int, default=5, help="卡片尺寸 3、4 或 5，默认 5"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=8,
        help="卡片张数 1~%d，默认 8" % MAX_CARDS,
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="随机种子，便于复现同一批卡片"
    )
    parser.add_argument(
        "--no-free", action="store_true", help="不启用中心自由格"
    )
    parser.add_argument(
        "--no-call-sheet", action="store_true", help="不生成叫号单"
    )
    parser.add_argument("--title", default="单词宾果", help="页面标题")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        words: List[str] = load_words(args.input)
        cards: List[Card] = generate_cards(
            words,
            size=args.size,
            count=args.count,
            seed=args.seed,
            free_center=not args.no_free,
        )
        page = render_html(
            cards,
            title=args.title,
            show_call_sheet=not args.no_call_sheet,
            seed=args.seed,
        )
    except BingoError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误: 读取词表失败: %s" % exc, file=sys.stderr)
        return 1

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入文件失败: %s" % exc, file=sys.stderr)
        return 1

    pages = (len(cards) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE
    if not args.no_call_sheet:
        pages += 1
    print(
        "已生成 %s：%d×%d 卡片 %d 张，词表 %d 个词，共 %d 页"
        % (args.output, args.size, args.size, len(cards), len(words), pages)
    )
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 纵向即可打印")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
