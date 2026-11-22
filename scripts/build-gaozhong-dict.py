#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成高中英语词汇字典（TypeWords 格式）。

数据优先级：
  1) public/dicts/en/word/CET4_T.json  命中即整条复用（含音标/释义/例句/短语/同义词/同根词/词源）
  2) dict_resource/ecdict.db           补 词形变化(exchange)、考试来源(tag)、英英释义(definition)、释义兜底
  3) 有道词典 jsonapi                   补 音标/释义/双语例句/短语/同近义词/词源/同根词/英英释义
  4) 本地 Oxford 解析版 Word Origin      etymonline 不可达时兜底英文词源；仍缺则引用派生基础词的词源\n  5) etymonline / tatoeba               仅在有道缺失时兜底（词源 / 例句，本机 etymonline 常熔断）
输出：
  public/dicts/en/word/GAOZHONG.json
  public/list/word.json 追加/更新一条词典索引

用法：
  python scripts/build-gaozhong-dict.py --limit 20     # 试跑
  python scripts/build-gaozhong-dict.py                # 全量（带缓存，可重复运行）
"""
import argparse
import json
import os
import random
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
SRC_TXT = ROOT / "dict_resource" / "高中词汇课文列表"
EC_DB = ROOT / "dict_resource" / "ecdict.db"
SYN_JSON = ROOT / "dict_resource" / "synonym.json"
CET4 = ROOT / "public" / "dicts" / "en" / "word" / "CET4_T.json"
OX_JSON = ROOT / "dict_resource" / "En-En_Oxford_Advanced_Learners_parsed.json"
OUT_WORDS = ROOT / "public" / "dicts" / "en" / "word" / "GAOZHONG.json"
OUT_LIST = ROOT / "public" / "list" / "word.json"
OUT_RECOMMEND = ROOT / "public" / "list" / "recommend_word.json"
CACHE = ROOT / "dict_resource" / ".cache_gaozhong"
REPORT = ROOT / "dict_resource" / "高中词汇生成报告.md"

DICT_ID = 2
DICT_EN = "gaozhong"
DICT_NAME = "高中英语"
DICT_URL = "GAOZHONG.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

TAG_CN = {"zk": "中考", "gk": "高考", "cet4": "四级", "cet6": "六级", "ky": "考研",
          "toefl": "托福", "ielts": "雅思", "gre": "GRE"}

# 7 个 txt 的教材顺序
FILES = ["高中必修1.txt", "高中必修2.txt", "高中必修3.txt",
         "高中选修1.txt", "高中选修2.txt", "高中选修3.txt", "高中选修4.txt"]

_lock = threading.RLock()
_ALIVE = {"etymonline": True, "tatoeba": True}
_fails = {"etymonline": 0, "tatoeba": 0}
DROPPED = []   # 源文件里的坏词条（编码损坏，无法当词条使用）


def is_corrupted(token):
    return bool(re.search(r"[\u0400-\u04ff\ufffd]", token))


def _fail(name, limit=3):
    """连续失败到阈值就熔断，避免每个词都白等超时。"""
    with _lock:
        _fails[name] += 1
        if _fails[name] >= limit and _ALIVE[name]:
            _ALIVE[name] = False
            log(f"[circuit] {name} 连续 {limit} 次失败，本批次停用")


def log(msg):
    with _lock:
        print(msg, flush=True)


# ---------------- 词表解析 ----------------

def parse_tokens():
    """返回 [(token, [单元标签...]), ...]，按教材顺序、首次出现去重。"""
    order, units = [], {}
    for fn in FILES:
        path = SRC_TXT / fn
        if not path.exists():
            log(f"[warn] 缺少文件 {fn}")
            continue
        book = fn.replace(".txt", "")
        cur_unit = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                cur_unit = line.lstrip("#").strip().rstrip(":").strip()
                continue
            parts = [t.strip() for t in re.split(r"[,，]", line) if t.strip()]
            for tok in parts:
                if is_corrupted(tok):
                    if (book, tok, cur_unit) not in DROPPED:
                        DROPPED.append((book, tok, cur_unit))
                    continue
                key = tok.lower()
                if key not in units:
                    order.append(tok)
                    units[key] = [f"{book}-{cur_unit}" if cur_unit else book]
                else:
                    label = f"{book}-{cur_unit}" if cur_unit else book
                    if label not in units[key]:
                        units[key].append(label)
    return order, units


# ---------------- CET4 ----------------

def load_cet4():
    data = json.loads(CET4.read_text(encoding="utf-8"))
    index = {}
    for w in data:
        index.setdefault(w["word"].lower(), w)
        index.setdefault(w["word"].lower().replace("-", " "), w)
    return index


# ---------------- ecdict ----------------

class EcDict:
    """每线程一条只读连接：多线程共用同一 cursor 会互相踩结果，导致字段时有时无。"""

    SQL = ("select phonetic,definition,translation,tag,exchange from ecdict "
           "where word=? collate nocase limit 1")

    def __init__(self, db):
        self.db = str(db)
        self._local = threading.local()

    def _conn(self):
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(f"file:{self.db}?mode=ro", uri=True,
                                   check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return conn

    def get(self, word):
        try:
            row = self._conn().execute(self.SQL, (word,)).fetchone()
            if row is None and " " in word:
                row = self._conn().execute(self.SQL, (word.replace(" ", ""),)).fetchone()
            return dict(row) if row else None
        except sqlite3.Error:
            return None


def parse_ecdict_translation(text):
    out = []
    for line in (text or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^([a-zA-Z]+\.)\s*(.+)$", line)
        if m:
            out.append({"pos": m.group(1), "cn": m.group(2).strip()})
        else:
            out.append({"pos": "", "cn": line})
    return out


def parse_exchange(text):
    forms = {}
    for item in (text or "").split("/"):
        if ":" not in item:
            continue
        k, v = item.split(":", 1)
        k, v = k.strip(), v.strip()
        if k and v and v != "0":
            forms[k] = v
    return forms


# ---------------- 有道 ----------------

class Youdao:
    """带缓存 + 限速 + 退避 的有道 jsonapi 客户端。"""

    def __init__(self, cache_dir: Path, min_delay=1.3, max_delay=2.2):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://dict.youdao.com/",
        })
        self.blocked = 0

    def _cache_path(self, word):
        slug = re.sub(r"[^a-z0-9]+", "_", word.lower())[:80]
        return self.cache_dir / f"{slug}.json"

    def fetch(self, word):
        path = self._cache_path(word)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        payload = None
        for attempt in range(3):
            try:
                time.sleep(random.uniform(self.min_delay, self.max_delay))
                r = self.session.get("https://dict.youdao.com/jsonapi",
                                     params={"q": word}, timeout=25)
                if r.status_code in (403, 429) or "captcha" in r.text.lower():
                    self.blocked += 1
                    log(f"[throttle] {word} -> {r.status_code}，退避 {10 * (attempt + 1)}s")
                    time.sleep(10 * (attempt + 1))
                    continue
                if r.status_code == 200 and r.text.strip().startswith("{"):
                    payload = r.json()
                    break
            except (requests.RequestException, ValueError):
                time.sleep(3 * (attempt + 1))
        if payload:
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return payload


TAG_RE = re.compile(r"<[^>]+>")


def clean(text):
    return TAG_RE.sub("", str(text or "")).strip()


def from_youdao(word, j):
    """有道 jsonapi -> 项目 Word 字段。缺省值保持空结构。"""
    res = {"word": word, "phonetic0": "", "phonetic1": "",
           "trans": [], "sentences": [], "phrases": [], "synos": [],
           "relWords": {"root": "", "rels": []}, "etymology": [],
           "e2e": [], "examsSrc": [], "inflections": {}}
    if not j:
        return res

    # 音标 + 释义（ec）
    ec = j.get("ec") or {}
    ec_words = ec.get("word") or []
    if ec_words:
        w0 = ec_words[0]
        res["phonetic0"] = clean(w0.get("ukphone"))
        res["phonetic1"] = clean(w0.get("usphone"))
        for tr in w0.get("trs") or []:
            for node in tr.get("tr") or []:
                items = (node.get("l") or {}).get("i") or []
                if isinstance(items, str):
                    items = [items]
                for line in items:
                    line = clean(line)
                    if not line:
                        continue
                    m = re.match(r"^(（[^）]*）|[a-zA-Z]+\.)\s*(.+)$", line)
                    if m:
                        res["trans"].append({"pos": m.group(1), "cn": m.group(2).strip()})
                    else:
                        res["trans"].append({"pos": "", "cn": line})
    if ec.get("exam_type"):
        res["examsSrc"] = [t for t in ec["exam_type"] if t]

    # simple 兜底音标（词组仅有 simple）
    if not res["phonetic0"] and not res["phonetic1"]:
        simple = (j.get("simple") or {}).get("word") or []
        if simple:
            res["phonetic0"] = clean(simple[0].get("ukphone"))
            res["phonetic1"] = clean(simple[0].get("usphone"))

    # 双语例句（最多 3 条）
    pairs = ((j.get("blng_sents_part") or {}).get("sentence-pair")) or []
    for p in pairs:
        en = clean(p.get("sentence") or p.get("sentence-eng"))
        cn = clean(p.get("sentence-translation"))
        if en and cn:
            res["sentences"].append({"c": en, "cn": cn})
        if len(res["sentences"]) >= 3:
            break

    # 词组（最多 5 条）
    for item in ((j.get("phrs") or {}).get("phrs")) or []:
        phr = item.get("phr") or {}
        head = (((phr.get("headword") or {}).get("l") or {}).get("i"))
        trs = phr.get("trs") or []
        cn = ""
        if trs:
            cn = clean((((trs[0].get("tr") or {}).get("l") or {}).get("i")))
        if head and cn:
            res["phrases"].append({"c": clean(head), "cn": cn})
        if len(res["phrases"]) >= 5:
            break

    # 同近义词
    for item in ((j.get("syno") or {}).get("synos")) or []:
        s = item.get("syno") or {}
        ws = [x.get("w") for x in (s.get("ws") or []) if x.get("w")]
        if s.get("pos") or s.get("tran") or ws:
            res["synos"].append({"pos": s.get("pos") or "", "cn": s.get("tran") or "",
                                 "ws": ws[:6]})
        if len(res["synos"]) >= 4:
            break

    # 词源
    zh = (((j.get("etym") or {}).get("etyms") or {}).get("zh")) or []
    for e in zh:
        value, desc = clean(e.get("value")), clean(e.get("desc"))
        if value:
            res["etymology"].append({"t": f"{word}:{desc}" if desc else f"{word}",
                                     "d": value})
        if len(res["etymology"]) >= 3:
            break

    # 同根词
    rw = j.get("rel_word") or {}
    if rw:
        res["relWords"]["root"] = rw.get("stem") or word
        rels = []
        for item in rw.get("rels") or []:
            rel = item.get("rel") or {}
            words = [{"c": w.get("word"), "cn": clean(w.get("tran"))}
                     for w in (rel.get("words") or []) if w.get("word")]
            if words:
                rels.append({"pos": rel.get("pos") or "", "words": words})
        res["relWords"]["rels"] = rels

    # 英英释义（WordNet，写入 e2e 扩展字段）
    for tr in (((j.get("ee") or {}).get("word") or {}).get("trs")) or []:
        for node in tr.get("tr") or []:
            d = clean(((node.get("l") or {}).get("i")))
            if d:
                res["e2e"].append({"pos": tr.get("pos") or "", "d": d})
    return res


# ---------------- etymonline / tatoeba 兜底 ----------------

def etymonline(word):
    """etymonline 网页词源。本机网络常被超时，连续失败后自动熔断。"""
    if not _ALIVE["etymonline"]:
        return []
    slug = word.lower().replace(" ", "-")
    try:
        from bs4 import BeautifulSoup
        r = requests.get(f"https://www.etymonline.com/word/{slug}", timeout=8,
                         headers={"User-Agent": UA})
        if r.status_code != 200:
            _fail("etymonline")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        sec = soup.find("section", class_=re.compile("word__etymology"))
        if not sec:
            return []
        out = []
        for block in sec.find_all("p"):
            txt = clean(block.get_text(" ", strip=True))
            if len(txt) > 30:
                out.append({"t": word, "d": txt})
        if out:
            _fails["etymonline"] = 0
        return out
    except Exception:
        _fail("etymonline")
        return []


TATOEBA_UA = "TypeWordsDictBot/1.0 (personal offline vocabulary study; non-commercial)"


def tatoeba(word):
    """Tatoeba API（语料 CC BY 2.0 FR）。按其 robots 要求使用明确的 bot UA。"""
    if not _ALIVE["tatoeba"]:
        return []
    try:
        r = requests.get("https://tatoeba.org/en/api_v0/search",
                         params={"query": word, "from": "eng", "to": "cmn",
                                 "orphans": "no", "unapproved": "no"}, timeout=15,
                         headers={"User-Agent": TATOEBA_UA, "Accept": "application/json"})
        if r.status_code != 200:
            _fail("tatoeba")
            return []
        data = r.json() or {}
        out = []
        for item in (data.get("results") or []):
            en = clean(item.get("text"))
            cn = ""
            for group in item.get("translations") or []:
                for tr in group or []:
                    if isinstance(tr, dict) and tr.get("lang") == "cmn":
                        cn = clean(tr.get("text"))
                        break
                if cn:
                    break
            if en and cn:
                out.append({"c": en, "cn": cn})
            if len(out) >= 3:
                break
        if out:
            _fails["tatoeba"] = 0
        return out
    except Exception:
        _fail("tatoeba")
        return []


# ---------------- 主流程 ----------------

def variant_queries(token):
    """占位词组（sb/sth/one's 或 off/on 并列）的降级查询候选。"""
    out = []
    s = token.strip()
    for pat in (r"\s+(sth|sb)\.?$", r"\s+one's$", r"\s+to do sth$", r"\s+to sth$"):
        t = re.sub(pat, "", s, flags=re.I).strip()
        if t and t != s:
            out.append(t)
    if "/" in s:
        head = s.split("/")[0].strip()
        if head and head != s:
            out.append(head)
    t = re.sub(r"\b(sb|sth)\b", "", s, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    if t and t != s and len(t.split()) >= 2:
        out.append(t)
    seen, uniq = set(), []
    for q in out:
        if q and q not in seen:
            seen.add(q)
            uniq.append(q)
    return uniq


def web_trans_fallback(j, token):
    """有道网络释义兜底（仅当常规释义为空时）。"""
    items = ((j or {}).get("web_trans") or {}).get("web-translation") or []
    for e in items:
        key = clean(e.get("key"))
        vals = [clean(t.get("value")) for t in (e.get("trans") or []) if t.get("value")]
        if vals and key and key.lower().replace(" ", "") == token.lower().replace(" ", ""):
            return [{"pos": "网络释义", "cn": f"{key}：{vals[0]}"}]
    for e in items[:1]:
        key = clean(e.get("key"))
        vals = [clean(t.get("value")) for t in (e.get("trans") or []) if t.get("value")]
        if vals:
            return [{"pos": "网络释义", "cn": f"{key}：{vals[0]}"}]
    return []


def normalize_item(it):
    """把 CET4 里的 null 字段统一成程序期望的空结构，避免前端取 length/forEach 报错。"""
    defaults = {"phonetic0": "", "phonetic1": "", "trans": [], "sentences": [],
                "phrases": [], "synos": [], "etymology": [], "e2e": [],
                "examsSrc": [], "inflections": {}}
    for k, dv in defaults.items():
        if it.get(k) is None:
            it[k] = dv.copy() if isinstance(dv, (list, dict)) else dv
    rw = it.get("relWords")
    if not isinstance(rw, dict) or not isinstance(rw.get("rels"), list):
        it["relWords"] = {"root": "", "rels": []}
    if not it["relWords"].get("root"):
        it["relWords"]["root"] = it.get("word", "")
    it["etymology"] = [e for e in (it.get("etymology") or [])
                       if (e.get("d") or "").strip()]
    if not isinstance(it.get("unit"), list):
        it["unit"] = []
    if not isinstance(it.get("id"), int):
        it["id"] = 0
    return it


class OxfordOrigin:
    """本地牛津高阶（解析版）的 Word Origin 段，用作 etymonline 不可达时的英文词源兜底。

    解析版里词源不是独立字段，而是拼在 definitions 末尾的
    `{{Word Origin}}Word Origin: ... {{/etymology}}`，后面可能紧跟
    Example Bank / Language Bank / II. 等版块，需要截断。
    """

    def __init__(self, path):
        self.path = Path(path)
        self.idx = {}
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        self._loaded = True
        if not self.path.exists():
            log(f"[oald] 未找到 {self.path}，跳过英文词源兜底")
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as exc:
            log(f"[oald] 读取失败: {exc}")
            return
        n = 0
        for e in data:
            w = (e.get("word") or "").strip().lower()
            if not w:
                continue
            self.idx.setdefault(w, []).append(e)
            n += 1
        log(f"[oald] 载入 {n} 条，唯一词 {len(self.idx)}")

    def lookup(self, word):
        self._load()
        for e in self.idx.get((word or "").strip().lower(), []):
            o = self._origin_of(e)
            if o:
                return o
        return None

    STOPS = ("{{Example Bank}}", "Example Bank:", "{{Language Bank}}", "Language Bank:",
             "{{Word Builder}}", "Word Builder", "Collocations", "Grammar Point",
             "Verb Forms", "British/American", "II. ", "Thesaurus", " • ", "▪",
             "Culture:", "Extra Examples", "More Like This", "Synonyms",
             "Which Word?", "Idioms", "Phrasal Verbs", "Grammar", "Nouns", "Adjectives",
             "Example")

    @classmethod
    def _origin_of(cls, e):
        for d in e.get("definitions") or []:
            m = re.search(r"\{\{Word Origin\}\}\s*Word Origin\s*:?", d)
            if not m:
                m = re.search(r"Word Origin\s*:", d)
            if not m:
                continue
            seg = d[m.end():]
            seg = re.sub(r"\{\{[^}]*\}\}", "", seg)          # 去双花括号标记
            seg = re.sub(r"<<([^>]*)>>", r"\1", seg)            # 去 <<词>> 链接
            seg = seg.replace("↑", "").replace("\\[", "").replace("\\]", "")
            for stop in cls.STOPS:                              # 截掉后续版块
                k = seg.find(stop)
                if k > 0:
                    seg = seg[:k]
            seg = re.sub(r"\s+", " ", seg).strip()
            seg = re.sub(r"^[\\\[\]\s]+", "", seg)
            hw = (e.get("word") or "").strip()
            if hw:                                              # 去掉开头的词头
                seg = re.sub(r"^" + re.escape(hw) + r"\s*\]?\s*", "", seg, flags=re.I)
            m2 = re.search(r"[.!?]\s+(?=[a-z])", seg)           # 句号后接小写 = 下一条释义
            if m2 and m2.start() > 30:
                seg = seg[: m2.start() + 1]
            parts = seg.split(". ")
            if len(parts) > 2:
                seg = ". ".join(parts[:2])
            seg = seg.strip()
            for _ in range(2):                                  # 丢掉被截断的残词
                t = seg.rsplit(" ", 1)
                if len(t) == 2 and len(t[1]) <= 2 and seg[-1] not in ".!?;":
                    seg = t[0].rstrip(" .")
            if len(seg) >= 12:
                return seg
        return None


SUFFIXES = ("ally", "ily", "ly", "ness", "ment", "ation", "ition", "tion", "sion",
            "er", "or", "ist", "ism", "ing", "ed", "able", "ible", "less", "ful",
            "ous", "ive", "al", "ic", "y", "es", "s")


def derive_bases(word, ec):
    """给出‘可能的词元/基础词’候选：先读 ecdict 的 0: 词元，再按常见词尾回退。"""
    lw = (word or "").strip().lower().rstrip(".")
    if not lw or " " in lw:
        return
    ex = ec.get(word) or ec.get(lw) or {}
    for part in str(ex.get("exchange") or "").split("/"):
        if part.startswith("0:"):
            b = part[2:].strip().lower()
            if b and b != lw:
                yield b
    for suf in SUFFIXES:
        if lw.endswith(suf) and len(lw) - len(suf) >= 3:
            stem = lw[: -len(suf)]
            if suf == "ally":
                yield stem + "al"
            elif suf == "ily":
                yield stem + "y"
            elif suf in ("ies", "es") and lw.endswith("ies"):
                yield lw[:-3] + "y"
            else:
                yield stem


def build_ety_index(cet4):
    """把已有中文词源的单词收成索引，供派生词引用。"""
    idx = {}
    items = cet4.values() if isinstance(cet4, dict) else cet4
    for w in items:
        name = (w.get("word") or "").strip().lower()
        if not name or " " in name:
            continue
        etys = w.get("etymology") or []
        if not etys:
            continue
        txt = "；".join(x.get("d", "") for x in etys if x.get("d"))
        if txt:
            idx.setdefault(name, txt)
    return idx


def fill_etymology(item, token, ec, oald, ety_index, report):
    """词源兜底顺序：OALD Word Origin（英文原文）→ 派生词引用基础词词源。"""
    ety = item.get("etymology") or []
    # CET4_T.json 里有 877 个只带标签、正文为空的词源条目，先清掉空壳再判是否存在
    if any((e.get("d") or "").strip() for e in ety):
        return
    if ety:
        item["etymology"] = [e for e in ety if (e.get("d") or "").strip()]
    if oald is not None:
        o = oald.lookup(token)
        if o:
            item["etymology"] = [{"t": f"{token}: Oxford Word Origin", "d": o}]
            report["oald"] += 1
            return
    if " " in token:
        return
    for base in derive_bases(token, ec):
        txt = ety_index.get(base)
        if txt:
            item["etymology"] = [{
                "t": f"{token}: 由 {base} 派生",
                "d": f"由 {base} 派生或变形，词源见 {base}：{txt}",
            }]
            report["derived"] += 1
            return


def build_one(token, cet4_index, ec, youdao, oald, ety_index, report):
    key = token.lower()
    hit = cet4_index.get(key) or cet4_index.get(key.replace("-", " "))
    if hit:
        item = {k: json.loads(json.dumps(v)) for k, v in hit.items()}
        item["id"] = None            # 稍后统一编号
        item["word"] = token
        item["source"] = "cet4"
        # CET4 里 inflections/e2e/examsSrc 全为 null，用 ecdict 补齐（不改动已有内容）
        ed = ec.get(token) or ec.get(key) or {}
        if ed:
            if not item.get("inflections"):
                item["inflections"] = parse_exchange(ed.get("exchange"))
            if not item.get("e2e") and ed.get("definition"):
                item["e2e"] = [{"pos": "", "d": clean(line)}
                               for line in ed["definition"].split("\n") if clean(line)][:4]
            if not item.get("examsSrc"):
                tags = [TAG_CN.get(t, t) for t in (ed.get("tag") or "").split() if t]
                if tags:
                    item["examsSrc"] = tags
        item.setdefault("inflections", {})
        item.setdefault("e2e", [])
        item.setdefault("examsSrc", [])
        report["from_cet4"] += 1
        fill_etymology(item, token, ec, oald, ety_index, report)
        return item

    j = youdao.fetch(token)
    item = from_youdao(token, j)
    item["source"] = "youdao" if j else "empty"
    if j:
        report["from_online"] += 1

    ed = ec.get(token) or ec.get(key) or {}
    if ed:
        report["ecdict_rows"] += 1
        if not item["trans"]:
            item["trans"] = parse_ecdict_translation(ed.get("translation"))
        if not item["phonetic0"] and not item["phonetic1"]:
            ph = (ed.get("phonetic") or "").strip()
            if ph:
                item["phonetic1"] = ph.replace("ә", "ə").replace("'", "ˈ").replace(":", "ː")
        ex = parse_exchange(ed.get("exchange"))
        if ex:
            item["inflections"] = ex
        tags = [TAG_CN.get(t, t) for t in (ed.get("tag") or "").split() if t]
        if tags and not item["examsSrc"]:
            item["examsSrc"] = tags
        if not item["e2e"] and ed.get("definition"):
            item["e2e"] = [{"pos": "", "d": clean(line)}
                           for line in (ed["definition"] or "").split("\n") if clean(line)][:4]

    if not item["trans"]:
        # 1) 换用去占位的词组再查一次
        for q in variant_queries(token):
            j2 = youdao.fetch(q)
            alt = from_youdao(q, j2)
            if alt["trans"]:
                item["trans"] = alt["trans"]
                report["variant_query"] += 1
                if j2 and not item["sentences"]:
                    item["sentences"] = alt["sentences"]
                break
    if not item["trans"]:
        # 2) 有道网络释义
        item["trans"] = web_trans_fallback(j, token)
        if item["trans"]:
            report["web_trans"] += 1
    if not item["sentences"]:
        s = tatoeba(token)
        if s:
            item["sentences"] = s
            report["tatoeba"] += 1
    if not item["etymology"] and " " not in token:
        e = etymonline(token)
        if e:
            item["etymology"] = e
            report["etymonline"] += 1
    fill_etymology(item, token, ec, oald, ety_index, report)
    if not item["phonetic0"] and not item["phonetic1"]:
        report["no_phonetic"] += 1
    if not item["trans"]:
        report["no_trans"] += 1
        log(f"[miss] 无释义: {token}")
    if not item["sentences"]:
        report["no_sentence"] += 1
    return item


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--fresh", action="store_true", help="清空有道缓存")
    ap.add_argument("--out", type=str, default="", help="输出路径（试跑用）")
    ap.add_argument("--no-list", action="store_true", help="不更新词典索引")
    args = ap.parse_args()

    trial = bool(args.limit)
    out_path = Path(args.out) if args.out else (
        Path(os.environ.get("TEMP", ".")) / "gaozhong_trial.json" if trial else OUT_WORDS)
    write_list = not args.no_list and not trial

    if args.fresh and CACHE.exists():
        for f in CACHE.glob("*.json"):
            f.unlink()
        log("[cache] cleared")

    order, units = parse_tokens()
    log(f"[input] 文件 {len(FILES)} 个，词条 {len(order)}")

    cet4 = load_cet4()
    ec = EcDict(EC_DB)
    youdao = Youdao(CACHE)

    oald = OxfordOrigin(OX_JSON)
    ety_index = build_ety_index(cet4)
    report = {"from_cet4": 0, "from_online": 0, "ecdict_rows": 0, "tatoeba": 0,
              "etymonline": 0, "oald": 0, "derived": 0,
              "no_phonetic": 0, "no_trans": 0, "no_sentence": 0,
              "variant_query": 0, "web_trans": 0}

    todo = order[args.offset: args.offset + args.limit] if args.limit else order[args.offset:]
    results = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(build_one, tok, cet4, ec, youdao, oald,
                               ety_index, report): tok
                   for tok in todo}
        done = 0
        for fut in as_completed(futures):
            tok = futures[fut]
            try:
                results[tok] = fut.result()
            except Exception as exc:            # 单条失败不拖垮整批
                log(f"[fail] {tok}: {exc}")
            done += 1
            if done % 100 == 0:
                el = time.time() - t0
                log(f"[progress] {done}/{len(todo)}  {el:.0f}s  "
                    f"eta {el / done * (len(todo) - done):.0f}s  blocked={youdao.blocked}")

    items = []
    for idx, tok in enumerate(todo, start=1):
        it = results.get(tok)
        if it is None:
            continue
        it["id"] = idx
        it["langType"] = "en"
        it["unit"] = units.get(tok.lower(), [])
        items.append(normalize_item(it))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=0), encoding="utf-8")

    # 更新索引（幂等）
    if not write_list:
        log(f"[trial] 仅写出 {out_path}，未改动 public/list/word.json")
        log("[done] " + json.dumps(
            {"条数": len(items),
             "有音标": sum(1 for i in items if i["phonetic0"] or i["phonetic1"]),
             "有释义": sum(1 for i in items if i["trans"]),
             "有例句": sum(1 for i in items if i["sentences"]),
             "有短语": sum(1 for i in items if i["phrases"]),
             "有同义词": sum(1 for i in items if i["synos"]),
             "有同根词": sum(1 for i in items if i["relWords"]["rels"]),
             "有词源": sum(1 for i in items if i["etymology"])}, ensure_ascii=False))
        return 0

    lst = json.loads(OUT_LIST.read_text(encoding="utf-8"))
    entry = {
        "id": DICT_ID, "enName": DICT_EN, "name": DICT_NAME,
        "description": "高中英语必修+选修词汇（人教版教材词表，含课文词组）",
        "categoryId": 1, "url": DICT_URL, "length": len(items), "language": "en",
        "translateLanguage": "zh_CN", "version": 1, "type": "word",
        "isDefault": False, "recommended": True, "hidden": False,
        "category": "中国考试", "tags": ["高中英语", "高考"],
        "createdAt": "2026-11-16 00:00:00", "updatedAt": "2026-11-16 00:00:00",
        "userId": "00000000-0000-0000-0000-000000000001", "cover": None,
    }
    lst = [d for d in lst if d.get("enName") != DICT_EN]
    lst.append(entry)
    OUT_LIST.write_text(json.dumps(lst, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 首页「推荐」区读的是 recommend_word.json，需同步一份（幂等）
    if OUT_RECOMMEND.exists():
        rec = json.loads(OUT_RECOMMEND.read_text(encoding="utf-8"))
        rec = [d for d in rec if d.get("enName") != DICT_EN]
        rec.append(entry)
        OUT_RECOMMEND.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 统计 + 报告
    n = len(items)
    stat = {
        "词条总数": n,
        "音标": sum(1 for i in items if i["phonetic0"] or i["phonetic1"]),
        "释义": sum(1 for i in items if i["trans"]),
        "例句": sum(1 for i in items if i["sentences"]),
        "短语": sum(1 for i in items if i["phrases"]),
        "同近义词": sum(1 for i in items if i["synos"]),
        "同根词": sum(1 for i in items if i["relWords"]["rels"]),
        "词源": sum(1 for i in items if i["etymology"]),
        "词形变化": sum(1 for i in items if i["inflections"]),
        "英英释义": sum(1 for i in items if i["e2e"]),
        "复用CET4": report["from_cet4"],
        "在线补全": report["from_online"],
        "ecdict命中": report["ecdict_rows"],
        "tatoeba例句": report["tatoeba"],
        "etymonline词源": report["etymonline"],
        "OALD词源": report["oald"],
        "派生词源": report["derived"],
        "无释义": report["no_trans"],
        "无例句": report["no_sentence"],
        "占位词组降级命中": report["variant_query"],
        "网络释义兜底": report["web_trans"],
        "源文件坏词条(已排除)": len(DROPPED),
    }
    raw = {"词条总数", "复用CET4", "在线补全", "ecdict命中", "tatoeba例句",
           "etymonline词源", "OALD词源", "派生词源",
           "无释义", "无例句", "占位词组降级命中",
           "网络释义兜底", "源文件坏词条(已排除)"}
    lines = ["# 高中英语词汇字典生成报告", "",
             f"- 输出：`public/dicts/en/word/{DICT_URL}`（{OUT_WORDS.stat().st_size / 1024:.0f} KB）",
             f"- 索引：`public/list/word.json`（词典列表）+ `public/list/recommend_word.json`（首页推荐）各追加 `{DICT_NAME}`（id={DICT_ID}，length={n}）",
             "- 字段优先级：CET4_T.json 整条复用 → 有道词典在线 → ecdict.db → 有道网络释义 → Tatoeba；词源：有道(优词) → etymonline → 本地 OALD Word Origin → 派生词引用基础词词源",
             "", "| 指标 | 数量 | 覆盖率 |", "|---|---:|---:|"]
    for k, v in stat.items():
        cov = f"{v / n * 100:.1f}%" if k not in raw else "-"
        lines.append(f"| {k} | {v} | {cov} |")
    thin = [i["word"] for i in items if not i["trans"] or not i["sentences"]]
    if thin:
        lines += ["", "## 数据偏薄词条（无释义或无例句）", "",
                  "、".join(f"`{w}`" for w in thin[:80])]
    if DROPPED:
        lines += ["", "## 源文件坏词条（编码损坏，未收录）", ""]
        for book_, tok_, unit_ in DROPPED:
            lines.append(f"- `{tok_}`（{book_} / {unit_}）")
    lines += ["", "## 数据来源与授权说明", "",
              "- 释义/例句/短语/同近义词/同根词/词源来自有道词典在线数据与项目内 CET4_T.json；"
              "这部分内容受商业词典版权保护，建议仅本地个人学习使用，公开发布前替换来源。",
              "- 词形变化、考试来源、英英释义兜底来自 ECDICT（本地 ecdict.db）。",
              f"- 词源来自有道 etym（优词/童理民）与本地《牛津高阶》解析版 Word Origin 段"
              f"（OALD 命中 {report['oald']} 条，另有 {report['derived']} 条由派生词引用基础词词源）；"
              f"etymonline 本机网络不可达，命中 {report['etymonline']} 条。\n"
              f"- Tatoeba 例句 CC BY 2.0 FR（本批命中 {report['tatoeba']} 条）；"
              "OALD 词源版权属牛津大学出版社、有道 etym 属商业词典内容，二者均建议仅本地个人学习使用。",
              "- 脚本 `scripts/build-gaozhong-dict.py`，缓存 `dict_resource/.cache_gaozhong`，可重复运行。"]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    log("[done] " + json.dumps(stat, ensure_ascii=False))
    log(f"[done] 耗时 {time.time() - t0:.0f}s，写入 {OUT_WORDS}")


if __name__ == "__main__":
    sys.exit(main())
