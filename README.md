<h1 align=center>
  <img src="https://github.com/user-attachments/assets/9d626e0f-0601-4640-8981-ad66d8ac4853" alt="TypeWords" style="width: 500px;"/>
</h1>

<p align="center">
  <a href="/README.md">English</a> |
  <a href="/docs/README.es.md">Español</a> |
  <a href="/docs/README.de.md">Deutsch</a> |
  <a href="/docs/README.fr.md">Français</a> |
  <a href="/docs/README.pt.md">Português</a> |
  <a href="/docs/README.ru.md">Русский</a> |
  <a href="/docs/README.uk.md">Українська</a> |
  <a href="/docs/README.ja.md">日本語</a> |
  <a href="/docs/README.ko.md">한국인</a> |
  <a href="/docs/README.th.md">ไทย</a> |
  <a href="/docs/README.vi.md">Tiếng Việt</a> |
  <a href="/docs/README.id.md">Bahasa Indonesia</a> |
  <a href="/docs/README.zh-TW.md">繁體中文</a> |
  <a href="/docs/README.zh-CN.md">简体中文</a> 
</p>

<p align="center">
  <b>Learn English, one keystroke at a time; smarter memorization, more efficient learning - an open-source word and article practice tool</b>
</p>

## 本仓库说明（改编版）

本项目在 [zyronon/TypeWords](https://github.com/zyronon/TypeWords) 基础上改编，保留原有网页端全部功能，并做了三处扩展：

1. **可以在 Android 上使用**：用精简后的静态站点 + Capacitor 打包成 APK（`apk/build-web.mjs`，产物见 `apk/`、`TypeWords-lite.apk`），手机上不依赖服务器，纯本地背单词。
2. **可以打包成 Windows 单文件 EXE**：`desktop/build-exe.mjs` 生成静态站点并内嵌进 C# 启动器，输出 `release/TypeWords.exe`（约 11 MB，双击即用，运行时不需要 Node.js，详见 [desktop/README.md](desktop/README.md)）。
3. **词库大幅扩充**：在保留原程序 CET-4 词库的基础上，新增初中、高中、六级、考研、托福、雅思、GRE 七本词库，全部本地离线可用。

### 内置词库（8 本，合计 17,861 条）

| 词典 | 词条数 | 说明 |
|---|---:|---|
| 大学英语四级（CET-4） | 2607 | 原程序自带，字段整条保留 |
| 高中英语 | 2366 | 新增，人教版必修 + 选修课文词表 |
| 初中英语 | 2368 | 新增，人教版 7–9 年级六册课文词表（含课文词组） |
| 六级英语（CET-6） | 1521 | 新增，ECDICT 考纲标签筛出的四级以上增量 |
| 考研英语 | 967 | 新增，同上口径，剔除四级及以下 |
| TOEFL 词汇 | 3253 | 新增，托福增量（不含四级/六级） |
| 雅思词汇 | 1325 | 新增，雅思增量（不含四级/六级） |
| GRE 词汇 | 3454 | 新增，GRE 增量（不含四/六/托/雅） |

每本词库统一字段：音标、词性与中文释义、双语例句、短语、同近义词、同根词、词形变化、英英释义、词源、单元/册次标签（初中、高中）。

字段来源与生成流程：`CET4_T.json` 与高中词库整条复用 → 有道词典在线补全例句/短语/同义 → ECDICT 兜底音标/释义/词形/英释 → 本地《牛津高阶》补词源。生成脚本：`scripts/build-gaozhong-dict.py`、`scripts/build-graded-dicts.py`、`scripts/build-chuzhong-dict.py`、`scripts/fill-sentences.py`，各库生成报告位于 `dict_resource/*生成报告.md`。

### 构建命令速查

```powershell
pnpm install                 # 安装依赖
pnpm dev                     # 网页开发调试 http://localhost:5567
node apk\build-web.mjs       # 生成 Android 用的精简静态站点
node desktop\build-exe.mjs   # 生成 release\TypeWords.exe（约 3~5 分钟）
node desktop\build-exe.mjs --reuse   # 复用已有站点文件，只重编译 exe，约 10 秒
```

> 词典数据的商业来源（有道、ECDICT、牛津高阶）建议仅用于本地个人学习，不要二次分发。

## Project Introduction

<img width="1920" height="1440" alt="practice words" src="/public/imgs/words.png" />
<img width="1920" height="1440" alt="practice articles" src="/public/imgs/articles.png" />

## Features

### Word Practice

- Practice modes: Follow-along / Dictation / Self-test / Spelling from memory
- Smart mode: Automatically calculates learning words based on memory curves, deepening memory through dictation
- Free mode: No restrictions, plan your own learning
- Provides phonetics, pronunciation (American/British), example sentences, phrases, synonyms, root words, etymology, error statistics, and more

### Article Memorization

- Built-in classic textbooks; you can also add or import articles with one-click translation and bilingual comparison
- Follow-along + dictation dual modes, sentence-by-sentence input with automatic pronunciation for more efficient memorization
- Supports listening while writing from memory to reinforce learning

### Favorites, Wrong Words, Mastered

- Words typed incorrectly while learning are automatically added to your wrong word book for later review
- Actively add words to mastered to automatically skip them in future sessions
- Add words to favorites for consolidation and review

### Highly Customizable

- Rich keyboard sound effects
- Customizable shortcuts
- Highly configurable settings

### Clean and Efficient

- Clean design, modern UI, ad-free
- Refreshing interface, simple operation
- No forced subscription to any platform

### Vocabulary Library

This fork ships **8 offline vocabularies** (17,861 entries total): CET-4 (2607, original config), Senior High (2366), Junior High (2368), CET-6 (1521), Graduate Entrance Exam (967), TOEFL (3253), IELTS (1325), GRE (3454). Each entry carries phonetics, translations, bilingual example sentences, phrases, synonyms, word family, inflections, English-English definitions and etymology.
The upstream project additionally offers GMAT, SAT, TEM-4/8 vocabularies on its official website; community contributions of additional vocabulary are welcome.

## Running the Project

#### Note: This project can run standalone with data saved locally. Manual backup is required when switching devices; this does not affect normal usage.

This project is built with `Nuxt` and requires a Node.js environment.

1. Install NodeJS, refer to the [official documentation](https://nodejs.org/en/download)
2. The project is large. It's recommended to use `git clone --depth 1 https://github.com/zyronon/TypeWords.git` to clone only the latest commit. GitHub's Download ZIP feature will not work properly.
3. In the project root directory, open a terminal and run `pnpm install` to download dependencies.
4. Run `pnpm run dev` to start the project. The default address is [`http://localhost:5567`](http://localhost:5567)
5. Open [`http://localhost:5567`](http://localhost:5567) in your browser to access the project.
6. Run `pnpm run generate` to build the project files.

Platform packaging in this fork: see `desktop/README.md` for the Windows single-file EXE (`release/TypeWords.exe`) and `apk/build-web.mjs` for the trimmed Android static site used by the Capacitor APK.

## Features and Suggestions

The project is currently in early development, with new features being added continuously. If you have any suggestions or feature requests, feel free to open an `Issue`.
If you like the design philosophy of this software, please submit a `PR`. Thank you for your support!

## Contributing Guide

[Contributing Guidelines](/docs/CONTRIBUTING.md)

If you're interested in this project, we welcome your contributions and will provide as much help as possible.

Before contributing, please communicate with the developers to avoid code conflicts.

Thank you again for your contributions!


## ❤️ Support TypeWords
If TypeWords has been helpful to you, feel free to sponsor the project to support server operation and future development.  
Of course, sponsorship is not required for use—sharing the project, submitting feedback, or contributing code are also highly valuable forms of support.

