"""宾果卡数据模型：词表解析、随机分卡与校验。"""

from __future__ import annotations

import csv
import io
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

SIZES: Tuple[int, ...] = (3, 4, 5)
MAX_CARDS = 60
MAX_WORD = 8
FREE_MARK = "★"


class BingoError(ValueError):
    """词表、卡片或参数不合法。"""


@dataclass(frozen=True)
class Card:
    """一张宾果卡：尺寸、按行排列的词条与是否启用中心自由格。"""

    size: int
    words: Tuple[str, ...]
    free_center: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.size, bool) or not isinstance(self.size, int):
            raise BingoError("卡片尺寸必须是整数")
        if self.size not in SIZES:
            raise BingoError("卡片尺寸只能是 3、4 或 5")

        try:
            words = tuple(self.words)
        except TypeError as exc:
            raise BingoError("卡片词条必须是序列") from exc
        if len(words) != self.size * self.size:
            raise BingoError(
                "%d×%d 的宾果卡需要 %d 个格子，当前有 %d 个"
                % (self.size, self.size, self.size * self.size, len(words))
            )
        for word in words:
            if not isinstance(word, str):
                raise BingoError("卡片词条必须是文本，当前是 %r" % (word,))
            if not word.strip():
                raise BingoError("卡片里出现了空词条")
        object.__setattr__(self, "words", words)

        has_free = self.free_center and self.size % 2 == 1
        if has_free:
            center = (self.size * self.size) // 2
            if words[center] != FREE_MARK:
                raise BingoError("启用自由格时，卡片正中心必须是「%s」" % FREE_MARK)
        elif FREE_MARK in words:
            raise BingoError("未启用自由格时不能出现「%s」" % FREE_MARK)

    @property
    def has_free_center(self) -> bool:
        """当前卡片是否真的有一个中心自由格。"""
        return self.free_center and self.size % 2 == 1

    def at(self, row: int, col: int) -> str:
        """按行列取词，行列从 0 开始。"""
        if isinstance(row, bool) or not isinstance(row, int):
            raise BingoError("行号必须是整数")
        if isinstance(col, bool) or not isinstance(col, int):
            raise BingoError("列号必须是整数")
        if not 0 <= row < self.size or not 0 <= col < self.size:
            raise BingoError(
                "行列超出范围：(%d, %d)，卡片是 %d×%d"
                % (row, col, self.size, self.size)
            )
        return self.words[row * self.size + col]


def _decode(data: bytes) -> str:
    if not isinstance(data, (bytes, bytearray)):
        raise BingoError("文件内容必须是字节")
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return bytes(data).decode(encoding)
        except UnicodeDecodeError:
            continue
    raise BingoError("无法识别文件编码，请另存为 UTF-8 或 GBK 后重试")


def parse_words(text: str, source: str = "输入内容") -> List[str]:
    """解析词表：每行一个词，取 CSV 首列，跳过空行与 # 注释。"""
    if not isinstance(text, str):
        raise BingoError("词表内容必须是文本")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text))
    words: List[str] = []
    seen: Dict[str, int] = {}
    for line_no, row in enumerate(reader, start=1):
        cell = row[0].strip() if row else ""
        if not cell or cell.startswith("#"):
            continue
        if len(cell) > MAX_WORD:
            raise BingoError(
                "%s 第 %d 行的词条超过 %d 个字符：%s"
                % (source, line_no, MAX_WORD, cell)
            )
        if cell in seen:
            raise BingoError(
                "%s 第 %d 行与第 %d 行重复：%s"
                % (source, line_no, seen[cell], cell)
            )
        seen[cell] = line_no
        words.append(cell)
    if not words:
        raise BingoError("%s 中没有有效的词条" % source)
    return words


def load_words(path: Union[str, Path]) -> List[str]:
    """读取词表文件并解析。"""
    target = Path(path)
    return parse_words(_decode(target.read_bytes()), source=str(target))


def _check_words(words: Sequence[str]) -> List[str]:
    if isinstance(words, (str, bytes)):
        raise BingoError("词表必须是词条列表，不能直接传字符串")
    try:
        items = list(words)
    except TypeError as exc:
        raise BingoError("词表必须是词条列表") from exc
    if not items:
        raise BingoError("词表不能为空")
    for word in items:
        if not isinstance(word, str):
            raise BingoError("词条必须是文本，当前是 %r" % (word,))
        if not word.strip():
            raise BingoError("词表里出现了空词条")
        if word.strip() == FREE_MARK:
            raise BingoError("词表里不能使用保留符号「%s」" % FREE_MARK)
    if len(set(items)) != len(items):
        raise BingoError("词表中有重复词条，请先去重")
    return [word.strip() for word in items]


def needed_words(size: int, free_center: bool = True) -> int:
    """生成指定尺寸卡片所需的词条数量。"""
    if isinstance(size, bool) or not isinstance(size, int):
        raise BingoError("卡片尺寸必须是整数")
    if size not in SIZES:
        raise BingoError("卡片尺寸只能是 3、4 或 5")
    if free_center and size % 2 == 1:
        return size * size - 1
    return size * size


def generate_cards(
    words: Sequence[str],
    size: int = 5,
    count: int = 8,
    seed: Optional[int] = None,
    free_center: bool = True,
) -> List[Card]:
    """随机生成一批互不相同的宾果卡。"""
    items = _check_words(words)
    if isinstance(size, bool) or not isinstance(size, int):
        raise BingoError("卡片尺寸必须是整数")
    if size not in SIZES:
        raise BingoError("卡片尺寸只能是 3、4 或 5")
    if isinstance(count, bool) or not isinstance(count, int):
        raise BingoError("卡片张数必须是整数")
    if not 1 <= count <= MAX_CARDS:
        raise BingoError("卡片张数必须在 1~%d 之间，当前是 %d" % (MAX_CARDS, count))
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise BingoError("随机种子必须是整数")
    if not isinstance(free_center, bool):
        raise BingoError("free_center 必须是布尔值")

    required = needed_words(size, free_center)
    if len(items) < required:
        raise BingoError(
            "%d×%d 宾果卡至少需要 %d 个词，当前只有 %d 个"
            % (size, size, required, len(items))
        )

    rng = random.Random(seed)
    cards: List[Card] = []
    seen = set()
    attempts = 0
    limit = count * 40
    while len(cards) < count and attempts < limit:
        attempts += 1
        picked = rng.sample(items, required)
        if free_center and size % 2 == 1:
            center = len(picked) // 2
            picked.insert(center, FREE_MARK)
        key = tuple(picked)
        if key in seen:
            continue
        seen.add(key)
        cards.append(Card(size=size, words=key, free_center=free_center))
    if len(cards) < count:
        raise BingoError(
            "无法生成 %d 张互不相同的卡片，请增加词条或减少张数" % count
        )
    return cards


def card_words(cards: Sequence[Card]) -> List[str]:
    """收集卡片上出现过的全部词条（不含自由格）。"""
    if not isinstance(cards, (list, tuple)) or not cards:
        raise BingoError("卡片列表不能为空")
    seen: Dict[str, None] = {}
    for card in cards:
        if not isinstance(card, Card):
            raise BingoError("卡片列表里出现了非 Card 对象")
        for word in card.words:
            if word != FREE_MARK:
                seen.setdefault(word, None)
    return list(seen)


def shuffle_words(words: Sequence[str], seed: Optional[int] = None) -> List[str]:
    """把词条随机排序，用于叫号单。"""
    items = _check_words(words)
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise BingoError("随机种子必须是整数")
    rng = random.Random(None if seed is None else seed + 1)
    rng.shuffle(items)
    return items


def call_sheet(cards: Sequence[Card], seed: Optional[int] = None) -> List[str]:
    """叫号单：卡片上出现过的全部词条，随机排序且不重复。"""
    return shuffle_words(card_words(cards), seed=seed)
