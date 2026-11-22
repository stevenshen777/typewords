"""初中英语词汇字典（人教版 7~9 年级六册词表）。

源：`dict_resource/初中词汇课文列表/*.txt`（七册上/下、八册上/下、九册上/下）
字段优先级：
  1) 项目内 CET4_T.json 命中 → 整条复用（含例句/短语/词源）
  2) 项目内 GAOZHONG.json 命中 → 整条复用
  3) 有道 jsonapi 在线补全（音标/释义/例句/短语/同近义词/词形变化）
  4) ecdict.db 兜底（音标/释义/英英释义/词形/考纲标签）
  5) 本地《牛津高阶》Word Origin 补词源

用法：
  python scripts\build-chuzhong-dict.py --limit 40     # 试跑，不写索引
  python scripts\build-chuzhong-dict.py                # 全量并安装
  python scripts\build-chuzhong-dict.py --fetch-only    # 只抓有道，不生成
"""
import argparse
import importlib.util
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "dict_resource" / "初中词汇课文列表"
EC_DB = ROOT / "dict_resource" / "ecdict.db"
OX_JSON = ROOT / "dict_resource" / "En-En_Oxford_Advanced_Learners_parsed.json"
DICT_DIR = ROOT / "public" / "dicts" / "en" / "word"
CET4 = DICT_DIR / "CET4_T.json"
GAOZHONG = DICT_DIR / "GAOZHONG.json"
OUT_WORDS = DICT_DIR / "CHUZHONG.json"
OUT_LIST = ROOT / "public" / "list" / "word.json"
REPORT = ROOT / "dict_resource" / "初中词汇生成报告.md"
CACHE = ROOT / "dict_resource" / ".cache_chuzhong"

DICT_ID = 8
DICT_EN = "chuzhong"
DICT_NAME = "初中英语"
DICT_URL = "CHUZHONG.json"

FILES = ["七册上词汇列表.txt", "七册下词汇列表.txt", "八册上词汇列表.txt",
         "八册下词汇列表.txt", "九册上词汇列表.txt", "九册下词汇列表.txt"]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# 教材词表里带注解/占位符的写法，逐个映射成可查词的干净词条；值为 None 表示丢弃
TOKEN_MAP = {
    "AI (= artificial intelligence)": "AI",
    "April Fool’s Day": "April Fool's Day",
    "Congratulations(on ...)!": "Congratulations",
    "Dr(= doctor)": "Dr",
    "What about …?": "What about",
    "along with sb / sth": "along with",
    "app(= application)": "app",
    "as… as …": None,
    "at the back(of)": "at the back of",
    "be connected with/ to": "be connected with",
    "be home to sb/ sth": "be home to",
    "be/ get used to": "be used to",
    "cut sth in/ into sth": "cut into",    "depend on/ upon": "depend on",
    "drop out (of sth)": "drop out",
    "exam (= examination)": "exam",
    "feel free (to do sth)": "feel free",
    "fight against sb/ sth": "fight against",
    "from the (bottom of one’s) heart": "from the bottom of one's heart",
    "get to one’s feet": "get to one's feet",
    "grey (AmE gray)": "grey",
    "hats off (to sb)": "hats off",
    "have(…) to do with sb/ sth": "have to do with",
    "honour(= honor)": "honour",
    "humour(= humor)": "humour",
    "keep (...) in mind": "keep in mind",
    "keep(…) away from …": "keep away from",
    "kg(= kilogram)": None,
    "km(= kilometre;kilometer)": None,
    "lend (sb) a hand": "lend a hand",
    "make sb's/ the bed": "make the bed",
    "make up (with sb)": "make up with",
    "make up ground on sb/sth": None,
    "metre(= meter)": "metre",
    "millions (of ...)": "millions of",
    "mm(= millimetre;millimeter)": None,
    "move on (to sth)": "move on",
    "not only … but also …": None,
    "organized(= organised)": "organized",
    "outer space (= space)": "outer space",
    "pay attention (to ...)": "pay attention to",
    "per cent (= percent)": "per cent",
    "play a part(in sth)": "play a part in",
    "play a role (in)": "play a role",
    "put oneself in sb's shoes": None,
    "realize (= realise)": "realize",
    "refrigerator (= fridge)": "refrigerator",
    "run out (of sth)": "run out",
    "sci-fi (= science fiction)": "sci-fi",
    "take one’s temperature": "take one's temperature",
    "take sb’ s breath away": "take one's breath away",
    "too ... to": None,
    "namaster": "namaste",
    "vs(= versus)": None,
    "would(d)like to": "would like to",
}

# 全大写缩写按小写查会被词典混入其它义项（IT 会捞到代词 it），这里人工覆盖正文
SPECIAL_ENTRIES = {
    "IT": {
        "trans": [{"pos": "abbr.", "cn": "信息技术（information technology）"}],
        "sentences": [], "phrases": [], "synos": [], "etymology": [],
    },
    "in forties": {"trans": [{"pos": "phr.", "cn": "在四十多岁时；四十多岁"}]},
    "ping pong bat": {"trans": [{"pos": "n.", "cn": "乒乓球拍"}]},
    "mini-goal": {"trans": [{"pos": "n.", "cn": "小目标；微型目标"}]},
}


def log(msg):
    print(msg, flush=True)


def load_bg():
    spec = importlib.util.spec_from_file_location(
        "bg_dict", ROOT / "scripts" / "build-gaozhong-dict.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def normalize_token(raw):
    t = raw.strip()
    if t in TOKEN_MAP:
        return TOKEN_MAP[t]        # 手工映射已是干净词头，不再二次清洗
    t = t.replace("’", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"\(\s*=\s*[^)]*\)", "", t)
    t = re.sub(r"\((?:\s*AmE\s*[^)]*|\s*BrE\s*[^)]*)\)", "", t)
    t = re.sub(r"\([^)]*\)", " ", t)
    t = t.replace("/", " ")
    t = re.sub(r"[!?…]|\.\.\.", " ", t)
    # 教材习惯用 sb/sth/one's/… 当占位符，去掉后留可用词头：stick to sth → stick to
    t = re.sub(r"\b(?:sb's|one's|oneself)\b", "", t, flags=re.I)
    t = re.sub(r"\b(?:sb|sth)\b", "", t, flags=re.I)
    t = re.sub(r"\s*[….\.]{3,}\s*", " ", t)
    t = re.sub(r"\b(?:do|doing|done)\s*$", "", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t).strip(" .,;:'-/")
    if t in ("a m", "a.m", "p m", "p.m"):
        t = t.replace(" ", "") + "."
    if not t:
        return None
    if "=" in t:
        return None
    return t


def parse_tokens():
    order, units, dropped = [], {}, []
    for fn in FILES:
        path = SRC / fn
        if not path.exists():
            log(f"[warn] 缺少 {fn}")
            continue
        book = fn.replace("词汇列表.txt", "")
        cur = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                cur = line.lstrip("#").strip().rstrip(":").strip()
                continue
            for raw in re.split(r"[,，]", line):
                raw = raw.strip()
                if not raw:
                    continue
                tok = normalize_token(raw)
                if not tok or len(tok) < 2:
                    dropped.append((book, raw))
                    continue
                key = tok.lower()
                label = f"{book} {cur}".strip()
                if key not in units:
                    order.append(tok)
                    units[key] = [label]
                elif label not in units[key]:
                    units[key].append(label)
    return order, units, dropped


class Fetcher:
    """有道 jsonapi：缓存 + 全局令牌桶限速 + 失败退避。"""

    def __init__(self, rate=2.6):
        CACHE.mkdir(parents=True, exist_ok=True)
        self.rate = rate
        self.lock = threading.Lock()
        self.next_at = 0.0
        self.ok = 0
        self.fail = 0
        self.local = threading.local()

    def _session(self):
        if not hasattr(self.local, "s"):
            self.local.s = requests.Session()
            self.local.s.headers.update({
                "User-Agent": UA,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://dict.youdao.com/",
            })
        return self.local.s

    def _path(self, word):
        return CACHE / (re.sub(r"[^a-z0-9]+", "_", word.lower())[:80] + ".json")

    def _pace(self):
        with self.lock:
            now = time.monotonic()
            wait = self.next_at - now
            self.next_at = max(now, self.next_at) + 1.0 / self.rate
        if wait > 0:
            time.sleep(wait + random_delay())

    def fetch(self, word):
        p = self._path(word)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                p.unlink(missing_ok=True)
        for attempt in range(3):
            self._pace()
            try:
                r = self._session().get("https://dict.youdao.com/jsonapi",
                                        params={"q": word}, timeout=20)
            except Exception:
                time.sleep(3 + attempt * 3)
                continue
            if r.status_code in (403, 429):
                time.sleep(8 + attempt * 10)
                continue
            if r.status_code == 200 and r.text.strip().startswith("{"):
                data = r.json()
                p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                with self.lock:
                    self.ok += 1
                    if self.ok % 200 == 0:
                        log(f"  ...已抓 {self.ok}，失败 {self.fail}")
                return data
            time.sleep(2 + attempt * 2)
        with self.lock:
            self.fail += 1
        return None


def random_delay():
    import random
    return random.uniform(0.02, 0.15)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--rate", type=float, default=2.6)
    ap.add_argument("--fetch-only", action="store_true")
    ap.add_argument("--no-list", action="store_true")
    args = ap.parse_args()

    bg = load_bg()
    order, units, dropped = parse_tokens()
    log(f"[input] 六册词表，去重词条 {len(order)}，丢弃注解/占位项 {len(dropped)}")
    if args.limit:
        order = order[: args.limit]

    cet4 = {w["word"].lower(): w for w in
            json.loads(CET4.read_text(encoding="utf-8"))}
    gz = {w["word"].lower(): w for w in
          json.loads(GAOZHONG.read_text(encoding="utf-8"))}

    need = [t for t in order if t.lower() not in cet4 and t.lower() not in gz]
    log(f"[plan] 复用四级 {sum(1 for t in order if t.lower() in cet4)}"
        f" / 复用高中 {sum(1 for t in order if t.lower() not in cet4 and t.lower() in gz)}"
        f" / 需在线 {len(need)}")

    fetcher = Fetcher(rate=args.rate)
    if need:
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = [pool.submit(fetcher.fetch, t) for t in need]
            for done, _ in enumerate(as_completed(futs), 1):
                if done % 300 == 0:
                    log(f"[fetch] {done}/{len(need)} 用时 {(time.time()-t0)/60:.1f} 分钟")
        log(f"[fetch] 完成，成功 {fetcher.ok}，失败 {fetcher.fail}")
    if args.fetch_only:
        return 0

    ec = bg.EcDict(EC_DB)
    oald = bg.OxfordOrigin(OX_JSON)
    ety_index = bg.build_ety_index(cet4)
    report = {"cet4": 0, "gaozhong": 0, "online": 0, "ecdict": 0,
              "oald": 0, "no_trans": 0, "no_sent": 0, "no_phon": 0}

    def from_ecdict(item, tok):
        ed = ec.get(tok) or ec.get(tok.lower()) or {}
        if not ed:
            return
        report["ecdict"] += 1
        if not item.get("trans"):
            item["trans"] = bg.parse_ecdict_translation(ed.get("translation"))
        if not item.get("phonetic0") and not item.get("phonetic1"):
            ph = bg.clean(ed.get("phonetic"))
            if ph:
                item["phonetic1"] = (ph.replace("ә", "ə").replace("'", "ˈ")
                                     .replace(":", "ː"))
        if not item.get("inflections"):
            ex = bg.parse_exchange(ed.get("exchange"))
            if ex:
                item["inflections"] = ex
        if not item.get("e2e") and ed.get("definition"):
            lines = (ed["definition"] or "").replace("\\n", "\n").split("\n")
            item["e2e"] = [{"pos": "", "d": bg.clean(x)} for x in lines if bg.clean(x)][:4]
        if not item.get("examsSrc"):
            tags = [bg.TAG_CN.get(t, t) for t in (ed.get("tag") or "").split() if t]
            if tags:
                item["examsSrc"] = tags

    items = []
    unresolved = []
    for tok in order:
        key = tok.lower()
        hit = cet4.get(key) or gz.get(key)
        if hit:
            item = json.loads(json.dumps(hit, ensure_ascii=False))
            item["word"] = tok
            item["source"] = "cet4" if key in cet4 else "gaozhong"
            report[item["source"]] += 1
            from_ecdict(item, tok)
        else:
            raw = fetcher.fetch(tok)  # 只读缓存，不会真的联网
            item = bg.from_youdao(tok, raw)
            item["source"] = "youdao" if raw else "empty"
            if raw:
                report["online"] += 1
            from_ecdict(item, tok)
            if not item.get("etymology"):
                o = oald.lookup(tok)
                if o:
                    item["etymology"] = [{"t": f"{tok}: Oxford Word Origin", "d": o}]
                    report["oald"] += 1
        item["unit"] = units.get(key, [])
        item["langType"] = "en"
        item = bg.normalize_item(item)
        if tok in SPECIAL_ENTRIES:
            item.update(json.loads(json.dumps(SPECIAL_ENTRIES[tok], ensure_ascii=False)))
            item["source"] = "manual"
        if not item.get("trans"):
            if (item["source"] == "empty"
                    or not (item.get("sentences") or item.get("phrases"))):
                unresolved.append(tok)
                continue
            report["no_trans"] += 1
        if not item.get("sentences"):
            report["no_sent"] += 1
        if not (item.get("phonetic0") or item.get("phonetic1")):
            report["no_phon"] += 1
        items.append(item)

    for idx, it in enumerate(items, 1):
        it["id"] = idx

    OUT_WORDS.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")

    n = len(items)
    if not args.no_list and not args.limit:
        lst = json.loads(OUT_LIST.read_text(encoding="utf-8"))
        entry = {
            "id": DICT_ID, "enName": DICT_EN, "name": DICT_NAME,
            "description": "初中英语六册（人教版 7~9 年级）教材词表，含课文词组",
            "categoryId": 1, "url": DICT_URL, "length": n, "language": "en",
            "translateLanguage": "zh_CN", "version": 1, "type": "word",
            "isDefault": False, "recommended": False, "hidden": False,
            "category": "中国考试", "tags": ["初中英语", "中考"],
            "createdAt": "2026-11-20 00:00:00", "updatedAt": "2026-11-20 00:00:00",
            "userId": "00000000-0000-0000-0000-000000000001", "cover": None,
        }
        lst = [d for d in lst if d.get("enName") != DICT_EN]
        lst.append(entry)
        lst.sort(key=lambda d: d.get("id", 0))
        OUT_LIST.write_text(json.dumps(lst, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        log(f"[list] word.json 现有 {len(lst)} 条")

    stats = {
        "词条": n,
        "音标": sum(1 for i in items if i["phonetic0"] or i["phonetic1"]),
        "释义": sum(1 for i in items if i["trans"]),
        "双语例句": sum(1 for i in items if i["sentences"]),
        "短语": sum(1 for i in items if i["phrases"]),
        "英英释义": sum(1 for i in items if i["e2e"]),
        "同近义词": sum(1 for i in items if i["synos"]),
        "同根词": sum(1 for i in items if i["relWords"]["rels"]),
        "词形变化": sum(1 for i in items if i["inflections"]),
        "词源": sum(1 for i in items if i["etymology"]),
        "复用四级": report["cet4"],
        "复用高中": report["gaozhong"],
        "在线补全": report["online"],
        "ecdict命中": report["ecdict"],
        "未解析剔除": len(unresolved),
    }
    lines = ["# 初中英语词汇字典生成报告", "",
             f"- 来源：`dict_resource/初中词汇课文列表/`（七上、七下、八上、八下、九上、九下六册）",
             f"- 输出：`public/dicts/en/word/{DICT_URL}`（{OUT_WORDS.stat().st_size/1024:.0f} KB），"
             f"索引 `public/list/word.json`（id={DICT_ID}，length={n}）",
             "- 字段优先级：CET4_T.json 整条复用 → GAOZHONG.json 整条复用 → 有道在线 → ecdict 兜底 → 本地 OALD 词源",
             "- 词表清洗：去掉 `(= 释义)`、`(AmE/BrE)`、`sb/sth/…` 等教材注解与占位符，"
             f"共丢弃 {len(dropped)} 项（详见文末）",
             f"- 词序：按教材册次与单元顺序（`unit` 字段记录册次+单元）",
             "", "| 指标 | 数量 | 覆盖率 |", "|---|---:|---:|"]
    raw = {"复用四级", "复用高中", "在线补全", "ecdict命中", "未解析剔除"}
    for k, v in stats.items():
        lines.append(f"| {k} | {v} | {'-' if k in raw else f'{v/n*100:.1f}%'} |")
    thin = [i["word"] for i in items if not i["trans"] or not i["sentences"]]
    if thin:
        lines += ["", "## 仍偏薄的词条（缺释义或缺例句）", "",
                  "、".join(f"`{w}`" for w in thin[:60])]
    if unresolved:
        lines += ["", "## 有道与 ecdict 都查不到、未收录的词条", ""]
        lines.append("、".join(f"`{w}`" for w in unresolved[:80]))
    if dropped:
        lines += ["", "## 未收录的教材注解项", ""]
        for book, raw_tok in dropped[:60]:
            lines.append(f"- `{raw_tok}`（{book}）")
    lines += ["", "## 说明", "",
              "- 例句/短语/同近义词来自有道词典，词形变化与英英释义来自 ECDICT；"
              "商业词典内容建议仅本地个人学习使用。",
              "- 重新生成：`python scripts/build-chuzhong-dict.py`（缓存命中时不联网）。"]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    log("[done] " + json.dumps(
        {k: v for k, v in stats.items()}, ensure_ascii=False))
    log(f"[done] 写入 {OUT_WORDS}（{OUT_WORDS.stat().st_size/1024:.0f} KB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
