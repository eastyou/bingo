"""命令行入口单元测试。"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import List

from bingo.cli import main

WORDS: List[str] = [
    "苹果", "香蕉", "西瓜", "葡萄", "草莓",
    "铅笔", "尺子", "橡皮", "书包", "课本",
    "老虎", "大象", "猴子", "熊猫", "长颈鹿",
    "足球", "篮球", "排球", "乒乓", "羽毛球",
    "春天", "夏天", "秋天", "冬天", "彩虹",
    "老师", "同学", "教室", "操场", "图书角",
]


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.words = self.root / "words.txt"
        self.words.write_text("\n".join(WORDS) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> int:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return main(argv)

    def test_generate(self) -> None:
        target = self.root / "cards.html"
        code = self.run_cli(["-i", str(self.words), "-o", str(target), "--seed", "1"])
        self.assertEqual(code, 0)
        page = target.read_text(encoding="utf-8")
        self.assertIn("<!doctype html>", page)
        self.assertIn("叫号单", page)

    def test_no_call_sheet(self) -> None:
        target = self.root / "cards.html"
        code = self.run_cli(
            ["-i", str(self.words), "-o", str(target), "--no-call-sheet", "--count", "3"]
        )
        self.assertEqual(code, 0)
        page = target.read_text(encoding="utf-8")
        self.assertNotIn("叫号单", page)
        self.assertEqual(page.count('<section class="sheet">'), 1)

    def test_size3_count2(self) -> None:
        target = self.root / "small.html"
        code = self.run_cli(
            [
                "-i", str(self.words), "-o", str(target),
                "--size", "3", "--count", "2", "--seed", "3",
            ]
        )
        self.assertEqual(code, 0)
        page = target.read_text(encoding="utf-8")
        self.assertIn("3×3", page)
        self.assertIn('<div class="card blank">', page)

    def test_no_free(self) -> None:
        target = self.root / "nofree.html"
        code = self.run_cli(
            ["-i", str(self.words), "-o", str(target), "--no-free", "--seed", "2"]
        )
        self.assertEqual(code, 0)
        page = target.read_text(encoding="utf-8")
        self.assertNotIn('<td class="free">', page)

    def test_seed_reproducible(self) -> None:
        first = self.root / "a.html"
        second = self.root / "b.html"
        args = ["-i", str(self.words), "--seed", "8", "--count", "2"]
        self.assertEqual(self.run_cli(args + ["-o", str(first)]), 0)
        self.assertEqual(self.run_cli(args + ["-o", str(second)]), 0)
        self.assertEqual(
            first.read_text(encoding="utf-8"), second.read_text(encoding="utf-8")
        )

    def test_title(self) -> None:
        target = self.root / "t.html"
        self.assertEqual(
            self.run_cli(["-i", str(self.words), "-o", str(target), "--title", "水果宾果", "--count", "1"]),
            0,
        )
        self.assertIn("水果宾果", target.read_text(encoding="utf-8"))

    def test_bad_count(self) -> None:
        target = self.root / "bad.html"
        code = self.run_cli(["-i", str(self.words), "-o", str(target), "--count", "0"])
        self.assertEqual(code, 2)
        self.assertFalse(target.exists())

    def test_bad_size(self) -> None:
        target = self.root / "bad.html"
        code = self.run_cli(["-i", str(self.words), "-o", str(target), "--size", "8"])
        self.assertEqual(code, 2)

    def test_too_few_words(self) -> None:
        small = self.root / "few.txt"
        small.write_text("苹果\n香蕉\n西瓜\n", encoding="utf-8")
        code = self.run_cli(["-i", str(small), "-o", str(self.root / "x.html")])
        self.assertEqual(code, 2)

    def test_missing_file(self) -> None:
        code = self.run_cli(["-i", str(self.root / "missing.txt"), "-o", str(self.root / "x.html")])
        self.assertEqual(code, 1)

    def test_missing_input_argument(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["-o", str(self.root / "x.html")])
        self.assertEqual(ctx.exception.code, 2)

    def test_help(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
