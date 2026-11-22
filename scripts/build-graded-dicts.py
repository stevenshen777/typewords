"""按 ecdict 的 tag 生成递进分级词库（六级/考研/TOEFL/雅思/GRE）。

层级规则（逐级剔除低级词汇）：
  A 六级   = cet6 - zk - gk - cet4
  B 考研   = ky   - zk - gk - cet4
  C TOEFL  = toefl - zk - gk - cet4 - cet6
  C 雅思   = ielts - zk - gk - cet4 - cet6
  D GRE    = gre   - zk - gk - cet4 - cet6 - toefl - ielts

字段来源（全部本地，不请求有道）：
  音标/中文释义/英英释义/词形变化 ← ecdict.db
  考纲标签 ← ecdict.tag
  近义词 ← dict_resource/synonym.json（Moby，英文同义词，无中文）
  同根词 ← ecdict.exchange 的变形形式
  词源 ← dict_resource/En-En_Oxford_Advanced_Learners_parsed.json 的 Word Origin 段
  例句/短语：本地无来源，留空
"""
import importlib.util
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EC_DB = ROOT / "dict_resource" / "ecdict.db"
SYN_JSON = ROOT / "dict_resource" / "synonym.json"
OX_JSON = ROOT / "dict_resource" / "En-En_Oxford_Advanced_Learners_parsed.json"
OUT_DIR = ROOT / "public" / "dicts" / "en" / "word"
LIST_WORDS = ROOT / "public" / "list" / "word.json"
LIST_RECOMMEND = ROOT / "public" / "list" / "recommend_word.json"
REPORT = ROOT / "dict_resource" / "分级词库生成报告.md"

TAG_CN = {"zk": "中考", "gk": "高考", "cet4": "四级", "cet6": "六级", "ky": "考研",
          "toefl": "托福", "ielts": "雅思", "gre": "GRE"}

SPECS = [
    {"id": 3, "en": "cet6", "name": "六级英语", "file": "CET6.json",
     "desc": "CET-6 词库（已剔除中考/高考/四级词汇）",
     "category": "中国考试", "tags": ["六级", "CET-6"],
     "need": {"cet6"}, "drop": {"zk", "gk", "cet4"}},
    {"id": 4, "en": "kaoyan", "name": "考研英语", "file": "KAOYAN.json",
     "desc": "考研英语词库（已剔除中考/高考/四级词汇）",
     "category": "中国考试", "tags": ["考研", "考研英语"],
     "need": {"ky"}, "drop": {"zk", "gk", "cet4"}},
    {"id": 5, "en": "toefl", "name": "TOEFL 词汇", "file": "TOEFL.json",
     "desc": "TOEFL 词库（已剔除中考/高考/四六级词汇）",
     "category": "出国考试", "tags": ["托福", "TOEFL"],
     "need": {"toefl"}, "drop": {"zk", "gk", "cet4", "cet6"}},
    {"id": 6, "en": "ielts", "name": "雅思词汇", "file": "IELTS.json",
     "desc": "IELTS 词库（已剔除中考/高考/四六级词汇）",
     "category": "出国考试", "tags": ["雅思", "IELTS"],
     "need": {"ielts"}, "drop": {"zk", "gk", "cet4", "cet6"}},
    {"id": 7, "en": "gre", "name": "GRE 词汇", "file": "GRE.json",
     "desc": "GRE 词库（已剔除中考/高考/四六级及托福雅思词汇）",
     "category": "出国考试", "tags": ["GRE"],
     "need": {"gre"}, "drop": {"zk", "gk", "cet4", "cet6", "toefl", "ielts"}},
]


def log(msg):
    print(msg, flush=True)


def load_oxford():
    spec = importlib.util.spec_from_file_location(
        "bg", ROOT / "scripts" / "build-gaozhong-dict.py")
    bg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bg)
    return bg.OxfordOrigin(OX_JSON), bg.parse_ecdict_translation, bg.parse_exchange, bg.clean


POS_RE = re.compile(
    r"^\s*(n|v|s|r|vt|vi|adj|adv|prep|conj|pron|num|art|int|aux|abbr)"
    r"(?:\.|[ \t])", re.I)
# WordNet 的 s./r. 分别是形容词、副词，对学习者显示成常用的 a./adv.
POS_CN = {"s.": "a.", "r.": "adv.", "n": "n.", "v": "v.", "s": "a.", "r": "adv."}
FORM_CN = {"s": "复数", "p": "过去式", "d": "过去分词", "i": "现在分词",
           "3": "第三人称单数", "r": "比较级", "t": "最高级"}


def pos_of(text):
    """从 ecdict 的释义行里取词性标记（"n. ..." → "n."），取不到就留空。"""
    m = POS_RE.match(text or "")
    if not m:
        return "", text
    raw = (text or "")[m.start():m.end()].strip()
    tag = POS_CN.get(raw, raw if raw.endswith(".") else raw + ".")
    return tag, (text or "")[m.end():]


def ipa(text):
    """ecdict 音标是旧式编码：'.' 分音节、',' 表示次重音、'(?@)' 是变体标记、
    'є'/'ε' 实际是 e、':' 是长音。统一成项目里常见的 IPA 写法。"""
    s = (text or "").strip().replace("ә", "ə").replace("'", "ˈ").replace(":", "ː")
    s = s.replace("(?@)", "").replace("\\", "").replace("^", "").replace("@", "")
    if ";" in s:
        s = s.split(";")[0]
    s = s.replace("є", "e").replace("ε", "e")
    s = s.replace(",", "ˌ").replace(".", "")
    return re.sub(r"\s{2,}", " ", s).strip(" ,;")


def bad_word(w):
    if not w or len(w) < 2:
        return True
    if any(ch.isdigit() for ch in w):
        return True
    if any(ord(ch) > 127 for ch in w):
        return True
    return False


def drop_inflections(words, by_word):
    """同一组里同时收了 cringe 和 cringing 时，只留基础词，避免背两遍。"""
    pool = set(words)
    out = []
    for w in words:
        if len(w) <= 4:
            out.append(w)
            continue
        lemma = None
        for suf, back in (("s", ""), ("es", ""), ("ed", ""), ("ed", "e"),
                          ("ing", ""), ("ing", "e"), ("d", "")):
            if w.endswith(suf):
                cand = w[: -len(suf)] + back
                if len(cand) > 2 and cand in pool:
                    lemma = cand
                    break
        if lemma and (by_word.get(lemma, {}).get("exchange") or ""):
            continue
        out.append(w)
    return out


def main():
    ox, parse_trans_bg, parse_exchange, clean = load_oxford()

    def parse_trans(text):
        # ecdict 里部分 translation 用两个字符的 \n 存了两行释义，先还原成真换行
        t = (text or "").replace("\\r\\n", "\n").replace("\\n", "\n")
        return parse_trans_bg(t)
    log("[oxford] 索引就绪")

    syn = json.loads(SYN_JSON.read_text(encoding="utf-8"))
    log(f"[synonym] {len(syn)} 组")

    conn = sqlite3.connect(f"file:{EC_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cols = ["word", "phonetic", "translation", "definition", "exchange", "tag", "frq"]
    rows = [dict(r) for r in conn.execute(
        "select " + ",".join(cols) + " from ecdict")]
    by_word = {(r["word"] or "").lower(): r for r in rows}
    log(f"[ecdict] {len(rows)} 行")

    def tags_of(r):
        return set((r["tag"] or "").split())

    sets = {t: {r["word"] for r in rows if t in tags_of(r)}
            for t in ("zk", "gk", "cet4", "cet6", "ky", "toefl", "ielts", "gre")}

    # program 内的 CET4_T.json 有 83~93 个词在 ecdict 里没打 cet4 tag，
    # 但用户已经在背四级了，按实际词表再剔一遍，避免重复
    cet4_words = {w["word"] for w in json.loads(
        (OUT_DIR / "CET4_T.json").read_text(encoding="utf-8"))}

    stats = {}
    meta = []
    for sp in SPECS:
        picked = set().union(*[sets[t] for t in sp["need"]])
        for t in sp["drop"]:
            picked -= sets[t]
        words = [w for w in picked if not bad_word(w) and w not in cet4_words]
        words = drop_inflections(words, by_word)
        # 常用词优先，便于背诵时先遇到高频词
        words.sort(key=lambda w: (by_word.get(w.lower(), {}).get("frq") or 9999999, w.lower()))

        items = []
        counts = dict(total=0, phonetic=0, trans=0, e2e=0, inflections=0,
                      synos=0, rel=0, etym=0, empty_trans=0)
        for idx, w in enumerate(words, 1):
            r = by_word.get(w.lower()) or {}
            ph = ipa(r.get("phonetic"))
            trans = parse_trans(r.get("translation"))
            ex = parse_exchange(r.get("exchange"))
            item = {
                "id": idx,
                "custom": False,
                "word": w,
                "phonetic0": ph,
                "phonetic1": ph,
                "trans": trans,
                "sentences": [],
                "phrases": [],
                "synos": [],
                "relWords": {"root": (ex.get("0") or w), "rels": []},
                "etymology": [],
                "e2e": [],
                "examsSrc": [TAG_CN.get(t, t) for t in (r.get("tag") or "").split() if t],
                "inflections": ex,
                "unit": [],
                "langType": "en",
                "source": "ecdict",
            }
            # ecdict 的 definition 同样用字面量 "\n" 分隔多行，先还原成真换行再拆条
            raw_def = (r.get("definition") or "").replace("\\r\\n", "\n").replace("\\n", "\n")
            defs = [clean(line) for line in raw_def.split("\n")][:6]
            defs = [d for d in defs if d]
            if defs:
                item["e2e"] = []
                for d in defs:
                    pos, body = pos_of(d)
                    if body.strip():
                        item["e2e"].append({"pos": pos, "d": body.strip()})
            s = syn.get(w) or syn.get(w.lower())
            if s:
                head = trans[0] if trans else {"pos": "", "cn": ""}
                item["synos"] = [{"pos": head["pos"], "cn": (head["cn"] or "")[:60],
                                  "ws": [x for x in s[:12]]}]
            forms, seen = [], set()
            for k, v in ex.items():
                if k in ("0", "") or not v or v == w or v in seen:
                    continue
                seen.add(v)
                forms.append((v, k))
            if forms:
                item["relWords"]["rels"] = [{
                    "pos": trans[0]["pos"] if trans else "",
                    "words": [{"c": f, "cn": FORM_CN.get(code, "变形")}
                              for f, code in forms[:8]]}]
            o = ox.lookup(w)
            if o:
                item["etymology"] = [{"t": f"{w}: Oxford Word Origin", "d": o}]

            counts["total"] += 1
            counts["phonetic"] += 1 if ph else 0
            counts["trans"] += 1 if trans else 0
            counts["empty_trans"] += 0 if trans else 1
            counts["e2e"] += 1 if item["e2e"] else 0
            counts["inflections"] += 1 if ex else 0
            counts["synos"] += 1 if item["synos"] else 0
            counts["rel"] += 1 if item["relWords"]["rels"] else 0
            counts["etym"] += 1 if item["etymology"] else 0
            items.append(item)

        out = OUT_DIR / sp["file"]
        # 重跑时保留上一版用 fill-sentences.py 补的例句/短语，别被覆盖成空数组
        kept = {}
        if out.exists():
            try:
                for o in json.loads(out.read_text(encoding="utf-8")):
                    kept[o.get("word", "")] = (o.get("sentences") or [], o.get("phrases") or [])
            except Exception:
                kept = {}
        for it in items:
            s_keep, p_keep = kept.get(it["word"], ([], []))
            if s_keep:
                it["sentences"] = s_keep
            if p_keep:
                it["phrases"] = p_keep
        counts["sent"] = sum(1 for it in items if it["sentences"])
        counts["phr"] = sum(1 for it in items if it["phrases"])
        out.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        stats[sp["name"]] = counts
        meta.append({**sp, "length": len(items)})
        log(f"[{sp['name']}] {len(items)} 词 → {out.name} "
            f"{out.stat().st_size/1024:.0f} KB | 音标 {counts['phonetic']} "
            f"释义 {counts['trans']} 词形 {counts['inflections']} "
            f"近义 {counts['synos']} 同根 {counts['rel']} 词源 {counts['etym']}")

    # ---- 写入词典索引（幂等：按 enName 覆盖/追加） ----
    for path in (LIST_WORDS, LIST_RECOMMEND):
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        is_reco = path == LIST_RECOMMEND
        now = "2026-11-17 00:00:00"
        for sp in meta:
            entry = {
                "id": sp["id"], "enName": sp["en"], "name": sp["name"],
                "description": sp["desc"], "categoryId": 1, "url": sp["file"],
                "length": sp["length"], "language": "en", "translateLanguage": "zh_CN",
                "version": 1, "type": "word", "isDefault": False,
                "recommended": bool(is_reco),
                "hidden": False, "category": sp["category"], "tags": sp["tags"],
                "createdAt": now, "updatedAt": now,
                "userId": "00000000-0000-0000-0000-000000000001", "cover": None,
            }
            if is_reco:
                # 首页推荐位保持原样（CET-4 / 高中），新增五本不进推荐，避免首页堆叠
                data = [d for d in data if d.get("enName") != sp["en"]]
                continue
            hit = next((i for i, d in enumerate(data) if d.get("enName") == sp["en"]), None)
            if hit is None:
                data.append(entry)
            else:
                data[hit] = entry
        data.sort(key=lambda d: d.get("id") or 0)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        log(f"[list] {path.name} 已更新（{len(data)} 条）")

    # ---- 报告 ----
    lines = ["# 分级词库生成报告", "",
             "- 蓝本：`dict_resource/ecdict.db` 的 `tag` 字段；层级规则逐级剔除低级词汇",
             "- 输出目录：`public/dicts/en/word/`，索引：`public/list/word.json` + `public/list/recommend_word.json`",
             "- 字段来源：ecdict（音标/中文释义/英英释义/词形变化/考纲标签）、synonym.json（英英近义词）、"
             "ecdict.exchange（同根词）、本地《牛津高阶》Word Origin（词源）、有道 jsonapi（双语例句/短语）",
             "- 例句与短语由 `scripts/fill-sentences.py` 逐词补入（缓存 `dict_resource/.cache_sent/`），"
             "重跑本脚本时会按词条保留，不会被清空",
             "- 去重：除按 tag 剔除外，另按项目内 `CET4_T.json` 实际词表再剔一遍（ecdict 有 83~93 词漏打 cet4 tag）；"
             "同组内屈折重复（如 cringe/cringing）只保留基础词", ""]
    rules = ["层级 A 六级 = cet6 − zk − gk − cet4",
             "层级 B 考研 = ky − zk − gk − cet4",
             "层级 C TOEFL = toefl − zk − gk − cet4 − cet6",
             "层级 C 雅思 = ielts − zk − gk − cet4 − cet6",
             "层级 D GRE = gre − zk − gk − cet4 − cet6 − toefl − ielts"]
    lines.append("## 层级规则\n")
    lines += [f"- {r}" for r in rules]
    lines += ["", "## 各库字段覆盖\n",
              "| 词库 | 词条 | 音标 | 中文释义 | 英英释义 | 双语例句 | 短语 | 词形变化 | 近义词 | 同根词 | 词源 |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, c in stats.items():
        n = c["total"] or 1
        lines.append(f"| {name} | {c['total']} | {c['phonetic']} ({c['phonetic']/n*100:.1f}%) "
                     f"| {c['trans']} ({c['trans']/n*100:.1f}%) | {c['e2e']} ({c['e2e']/n*100:.1f}%) "
                     f"| {c.get('sent', 0)} ({c.get('sent', 0)/n*100:.1f}%) "
                     f"| {c.get('phr', 0)} ({c.get('phr', 0)/n*100:.1f}%) "
                     f"| {c['inflections']} | {c['synos']} | {c['rel']} | {c['etym']} |")
    lines += ["", "## 说明", "",
              "- 例句/短语来自有道词典，每词取 3 条双语例句、最多 3 条词组；有道本身没有数据的词留空"
              "（实测约 2% 的词无双语例句，GRE 生僻词的词组覆盖率最低）。",
              "- 近义词为 Moby 英文同义词，中文一栏取其首条释义；同根词来自 ecdict 的词形变化码（p/d/i/3/r/t/s）。",
              "- 词序按 ecdict `frq`（词频）升序排列，高频词在前，便于分级背诵。",
              "- 重新生成：`python scripts/build-graded-dicts.py`（纯本地，秒级，无网络请求）；"
              "补例句：`python scripts/fill-sentences.py`（联网，缓存命中时不重复请求）。"]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"[done] 报告 → {REPORT.name}")
    log("[done] " + json.dumps({k: v["total"] for k, v in stats.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
