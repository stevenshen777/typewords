"""给 5 本分级词库（CET6/KAOYAN/TOEFL/IELTS/GRE）补例句与短语。

数据来源：有道 jsonapi（https://dict.youdao.com/jsonapi?q=<词>）
  - 例句 ← blng_sents_part.sentence-pair[] 的 sentence / sentence-translation
  - 短语 ← phrs.phrs[].phr.headword.l.i / trs[].tr.l.i

要点（都是前面踩坑换来的）：
  - 只能带 q 参数，带 dicts 会退化成 384 字节的空响应
  - 每个词落盘缓存到 dict_resource/.cache_sent/，重跑直接命中，不会重复请求
  - 全局令牌桶限速（默认 2.6 请求/秒），403/429 退避，连续失败自动熔断
  - 只写 sentences / phrases 两个字段，其它字段与词数保持不变

用法：
  python scripts\fill-sentences.py                # 全量补（约 40~60 分钟）
  python scripts\fill-sentences.py --limit 30     # 抽 30 个词试跑
  python scripts\fill-sentences.py --write-only   # 只用已有缓存回写，不联网
"""
import argparse
import json
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "public" / "dicts" / "en" / "word"
CACHE = ROOT / "dict_resource" / ".cache_sent"
URL = "https://dict.youdao.com/jsonapi"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
FILES = ["CET6.json", "KAOYAN.json", "TOEFL.json", "IELTS.json", "GRE.json"]


def log(msg):
    print(msg, flush=True)


def safe_name(word):
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", word).strip("_") or "blank"


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "")


def extract(raw):
    """从有道原始响应里取 3 条例句、3 条短语。"""
    sents = []
    for sp in ((raw.get("blng_sents_part") or {}).get("sentence-pair") or []):
        en = (sp.get("sentence") or strip_tags(sp.get("sentence-eng")) or "").strip()
        zh = (sp.get("sentence-translation") or "").strip()
        en = re.sub(r"\s{2,}", " ", en)
        if en and zh and len(sents) < 3:
            sents.append({"c": en, "cn": zh})

    phrs = []
    for it in ((raw.get("phrs") or {}).get("phrs") or []):
        phr = it.get("phr") or {}
        hw = (((phr.get("headword") or {}).get("l") or {}).get("i") or "").strip()
        zh = ""
        for t in (phr.get("trs") or []):
            zh = (((t.get("tr") or {}).get("l") or {}).get("i") or "").strip()
            if zh:
                break
        if hw and zh and len(phrs) < 3:
            phrs.append({"c": hw, "cn": zh})
    return sents, phrs


class Fetcher:
    def __init__(self, rate=2.6):
        self.rate = rate
        self.lock = threading.Lock()
        self.next_at = 0.0
        self.consec_fail = 0
        self.stopped = False
        self.count_ok = 0
        self.count_fail = 0
        self.local = threading.local()

    def _session(self):
        if not hasattr(self.local, "s"):
            self.local.s = requests.Session()
        return self.local.s

    def _pace(self):
        with self.lock:
            now = time.monotonic()
            wait = self.next_at - now
            self.next_at = max(now, self.next_at) + 1.0 / self.rate
        if wait > 0:
            time.sleep(wait + random.uniform(0.02, 0.15))

    def fetch(self, word):
        path = CACHE / f"{safe_name(word.lower())}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                path.unlink(missing_ok=True)

        for attempt in range(3):
            if self.stopped:
                return None
            self._pace()
            try:
                r = self._session().get(
                    URL, params={"q": word}, timeout=15,
                    headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
            except Exception:
                time.sleep(2 + attempt * 3)
                continue
            if r.status_code == 200 and len(r.content) > 400:
                try:
                    data = r.json()
                except Exception:
                    time.sleep(1.5)
                    continue
                path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                with self.lock:
                    self.consec_fail = 0
                    self.count_ok += 1
                    if self.count_ok % 200 == 0:
                        log(f"  ...已抓 {self.count_ok}，失败 {self.count_fail}")
                return data
            if r.status_code in (403, 429):
                time.sleep(5 + attempt * 8)
                continue
            time.sleep(1.5 + attempt * 2)

        with self.lock:
            self.consec_fail += 1
            self.count_fail += 1
            if self.consec_fail >= 10 and not self.stopped:
                self.stopped = True
                log(f"[熔断] 连续 {self.consec_fail} 次失败，停止联网（已完成部分仍会写回）")
        return None


def collect_words():
    words = {}
    for f in FILES:
        for w in json.loads((OUT_DIR / f).read_text(encoding="utf-8")):
            words.setdefault(w["word"], None)
    return list(words)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--rate", type=float, default=2.6)
    ap.add_argument("--write-only", action="store_true")
    args = ap.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    todo = collect_words()
    if args.limit:
        todo = todo[: args.limit]
    log(f"[start] 待处理 {len(todo)} 词，并发 {args.workers}，限速 {args.rate}/s")

    result = {}
    fetcher = Fetcher(rate=args.rate)
    if not args.write_only:
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {pool.submit(fetcher.fetch, w): w for w in todo}
            done = 0
            for fu in as_completed(futs):
                w = futs[fu]
                try:
                    raw = fu.result()
                except Exception:
                    raw = None
                done += 1
                if raw:
                    result[w] = extract(raw)
                if done % 500 == 0:
                    el = time.time() - t0
                    log(f"[progress] {done}/{len(todo)} 用时 {el/60:.1f} 分钟 "
                        f"预计还需 {el/done*(len(todo)-done)/60:.0f} 分钟")

    # --write-only 或熔断后：全部走缓存回填
    for w in todo:
        if w in result:
            continue
        path = CACHE / f"{safe_name(w.lower())}.json"
        if path.exists():
            try:
                result[w] = extract(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                pass

    # 回写到 5 本词典
    total_s = total_p = 0
    for f in FILES:
        path = OUT_DIR / f
        items = json.loads(path.read_text(encoding="utf-8"))
        s_cnt = p_cnt = 0
        for it in items:
            got = result.get(it["word"])
            if not got:
                continue
            sents, phrs = got
            if sents:
                it["sentences"] = sents
                s_cnt += 1
            if phrs:
                it["phrases"] = phrs
                p_cnt += 1
        path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        total_s += s_cnt
        total_p += p_cnt
        log(f"[{f}] 例句 {s_cnt}/{len(items)}，短语 {p_cnt}/{len(items)}，"
            f"{path.stat().st_size/1024/1024:.2f} MB")
    log(f"[done] 例句覆盖 {total_s}，短语覆盖 {total_p}，缓存 {len(list(CACHE.glob('*.json')))} 个")


if __name__ == "__main__":
    main()
