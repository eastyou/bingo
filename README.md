# bingo

[![CI](https://github.com/eastyou/bingo/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/bingo/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给老师用的课堂宾果卡生成器：把单词表整理成每行一个词的文本，一条命令生成 A4 可打印的宾果卡和叫号单。**零依赖，不联网，打印即用。**

每张卡随机排列、互不重复，5×5 默认保留中心自由格；末页附三列叫号单，老师按顺序叫词、学生划掉，连成一线就获胜。

## 特性

- **一页四张**：A4 纵向 2×2 排版，每张卡带编号和「班级 / 姓名」填写栏
- **三种尺寸**：`--size 3/4/5`，3×3 适合低年级，5×5 适合单词复习
- **卡片不重复**：同一批卡片随机抽样且互不相同，避免同桌答案一样
- **中心自由格**：奇数尺寸默认正中心为「★」，`--no-free` 可关闭
- **叫号单**：全部词条随机排序、三列编号、带勾选框，`--no-call-sheet` 可关闭
- **随机种子**：`--seed` 固定后每次生成同一批卡片，方便补印
- **词表宽松**：纯文本每行一词，或 CSV 只取首列；空行与 `#` 注释自动跳过
- **逐行校验**：重复词、超长词、空词表都会指出具体行号
- **94 个单元测试**：覆盖词表解析、编码识别、卡片生成、叫号单、渲染与命令行

## 安装

```bash
pip install bingo
```

也可以直接下载源码，在项目目录里运行：

```bash
python -m bingo --help
```

## 用法

准备词表 `单词表.csv`：

```text
苹果
香蕉
西瓜
...
```

生成 8 张 5×5 宾果卡和一张叫号单：

```bash
python -m bingo -i 单词表.csv -o 宾果.html
```

生成 30 张 3×3 卡片、不印叫号单、固定随机结果：

```bash
python -m bingo -i 单词表.csv --size 3 --count 30 --seed 2026 --no-call-sheet
```

### 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `-i, --input` | 词表文件，每行一个词（CSV 取首列） | 必填 |
| `-o, --output` | 输出 HTML 路径 | `宾果.html` |
| `--size` | 卡片尺寸：3、4、5 | `5` |
| `--count` | 卡片张数 1~60 | `8` |
| `--seed` | 随机种子，固定后结果可复现 | 随机 |
| `--no-free` | 不启用中心自由格 | 关闭 |
| `--no-call-sheet` | 不生成叫号单 | 关闭 |
| `--title` | 页面标题 | `单词宾果` |

### 词表格式

每行一个词，最多 8 个字符：

```text
# 以 # 开头的是注释，会被跳过
苹果
香蕉

西瓜,水果
```

- 纯文本：整行就是一个词
- CSV：只取第一列，后面的列忽略
- 编码：UTF-8（含 BOM）与 GBK 自动识别
- 重复词会报错并指出两次出现的行号

### 各尺寸所需词数

| 尺寸 | 自由格 | 至少需要 |
| --- | --- | --- |
| 5×5 | 中心 1 格 | 24 个词 |
| 4×4 | 无 | 16 个词 |
| 3×3 | 中心 1 格 | 8 个词 |

词越多，卡片重复的概率越低。

## 打印

用浏览器打开生成的 HTML，按 `Ctrl/Cmd + P`：

- 纸张：A4 纵向
- 边距：无 / 默认
- 勾选「背景图形」，卡片边框和自由格底色才会打印

## 项目结构

```text
bingo/
├── bingo/
│   ├── model.py    # 词表解析、卡片生成与校验
│   ├── render.py   # A4 卡片与叫号单排版
│   └── cli.py      # 命令行入口
├── tests/          # 94 个单元测试
└── examples/       # 示例词表
```

## 开发

```bash
python -m unittest discover -s tests
```

## 许可证

[MIT](LICENSE) © 2026 eastyou
