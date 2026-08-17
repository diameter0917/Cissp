#!/usr/bin/env python3
"""
build_video_segments.py — 由帶時間碼字幕算出各單元的影片段落（stdlib only）
==========================================================================
每支 EP 是一整條學習路徑（約 50 分鐘、橫跨數個單元），讀者需要知道
「今天這課對應影片的哪幾段」。本腳本用**關鍵詞密度定位**找出那些段落，
寫進 sc200_curriculum.json 的 units[].video_segments：

    {"ep": "EP8", "start": 735, "title": "DCR、擷取時轉換"}

build_site.py 會把它渲染成電子報「影片伴讀」章節的可點時間碼（12:35 → 跳看）。

定位方法（沿用 CISSP 專案 apply_video_timestamps.py 的密度思路）：
  - 用 check_coverage.py 的 SC-200 術語詞典當關鍵詞來源，取「該單元電子報
    有寫、且影片字幕也提到」的術語——這正是兩邊的交集主題。
  - 以滑動視窗掃過字幕，計分用「視窗內出現的**相異**術語加權和」，
    避免單一高頻詞洗版；多詞片語權重高於單詞。
  - 跳過開場 60 秒（片頭與議程 name-drop），取分數最高且不重疊的前 N 段。

用法：
  python3 sc200/scripts/build_video_segments.py            # 全部單元，寫回 curriculum
  python3 sc200/scripts/build_video_segments.py --dry-run  # 只印結果不寫檔
  python3 sc200/scripts/build_video_segments.py --top 2    # 每單元最多幾段（預設 3）
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_coverage import TERMS, ep_slug, strip_html  # noqa: E402  共用術語詞典

SC200 = Path(__file__).resolve().parents[1]
TIMED = SC200 / "transcripts" / "_timed"
CONTENT = SC200 / "content"
CURRICULUM = SC200 / "sc200_curriculum.json"

WINDOW = 150      # 視窗長度（秒）
STEP = 30         # 滑動步長（秒）
INTRO_SKIP = 60   # 跳過開場（秒）
MIN_GAP = 150     # 選出的段落彼此至少間隔（秒）


def parse_vtt(path):
    """VTT → [(start_sec, text)]。"""
    cues = []
    start = None
    buf = []
    for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = ln.strip()
        m = re.match(r"(\d+):(\d{2}):(\d{2})[.,](\d+)\s+-->", ln)
        if m:
            if start is not None and buf:
                cues.append((start, " ".join(buf)))
            h, mi, s, _ = m.groups()
            start = int(h) * 3600 + int(mi) * 60 + int(s)
            buf = []
            continue
        if not ln or ln.startswith(("WEBVTT", "Kind:", "Language:")) or ln.isdigit():
            continue
        buf.append(re.sub(r"<[^>]+>", "", ln))
    if start is not None and buf:
        cues.append((start, " ".join(buf)))
    return cues


def vtt_for(ep):
    """優先用英文軌（術語是英文，定位較準），沒有才退回其他語言。"""
    slug = ep_slug(ep)
    en = TIMED / f"{slug}.en.vtt"
    if en.exists():
        return en
    others = sorted(TIMED.glob(f"{slug}.*.vtt"))
    return others[0] if others else None


def newsletter_terms(unit):
    """該單元電子報提到的術語 → {canonical: (次數, [英文別名])}。"""
    path = CONTENT / f"day-{unit['seq']:03d}.html"
    if not path.exists():
        return {}
    text = strip_html(path.read_text(encoding="utf-8")).lower()
    out = {}
    for canonical, aliases in TERMS.items():
        # 只留英文別名——中文詞在英文字幕裡找不到
        en = [a for a in aliases if not re.search(r"[一-鿿]", a)]
        n = sum(text.count(a) for a in aliases)
        if n and en:
            out[canonical] = (n, en)
    return out


def unit_keywords(unit, doc_freq):
    """
    定位用關鍵詞與權重。用 TF-IDF 式加權：某術語在**這一課**講得越多、
    而在**其他課**出現得越少，權重越高——否則兩門相鄰的課（例如 KQL I/II）
    會因為共用詞彙而定位到同一段影片。
    """
    kws = {}
    for canonical, (n, aliases) in newsletter_terms(unit).items():
        weight = n / (1 + doc_freq.get(canonical, 0))
        kws[canonical] = (weight, aliases)
    return kws


def score_windows(cues, keywords, duration):
    """回傳 [(score, start, [命中的術語])]。相異術語才計分，權重取自 TF-IDF。"""
    out = []
    t = INTRO_SKIP
    while t < duration:
        lo, hi = t, t + WINDOW
        text = " ".join(c for s, c in cues if lo <= s < hi).lower()
        hits, score = [], 0.0
        for canonical, (weight, aliases) in keywords.items():
            best = 0.0
            for a in aliases:
                if a in text:
                    # 多詞片語比單詞可信（"live response" 勝過 "alert"）
                    best = max(best, weight * (2.0 if " " in a.strip() else 1.0))
            if best:
                hits.append((best, canonical))
                score += best
        if score:
            hits.sort(reverse=True)
            out.append((score, lo, [c for _, c in hits]))
        t += STEP
    return sorted(out, key=lambda x: (-x[0], x[1]))


def pick_segments(scored, top):
    """取分數最高且彼此不重疊的前 top 段，最後依時間排序。"""
    chosen = []
    for score, start, hits in scored:
        if all(abs(start - c[1]) >= MIN_GAP for c in chosen):
            chosen.append((score, start, hits))
        if len(chosen) >= top:
            break
    return sorted(chosen, key=lambda x: x[1])


def fmt(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只印結果、不寫回 curriculum")
    ap.add_argument("--top", type=int, default=3, help="每單元最多幾段（預設 3）")
    args = ap.parse_args()

    curriculum = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    units = [u for u in curriculum["units"] if u["type"] == "study"]

    # 每個術語被幾個單元提到（IDF 的分母）
    doc_freq = {}
    for u in units:
        for canonical in newsletter_terms(u):
            doc_freq[canonical] = doc_freq.get(canonical, 0) + 1

    vtt_cache, dur_cache = {}, {}
    filled = skipped = 0

    for u in units:
        segs = []
        kws = unit_keywords(u, doc_freq)
        for ep in (u.get("video_eps") or []):
            path = vtt_for(ep)
            if path is None:
                continue
            if ep not in vtt_cache:
                vtt_cache[ep] = parse_vtt(path)
                dur_cache[ep] = vtt_cache[ep][-1][0] if vtt_cache[ep] else 0
            cues = vtt_cache[ep]
            if not cues or not kws:
                continue
            scored = score_windows(cues, kws, dur_cache[ep])
            for score, start, hits in pick_segments(scored, args.top):
                segs.append({"ep": ep, "start": start,
                             "title": "、".join(hits[:3]), "score": round(score, 1)})
        if segs:
            segs.sort(key=lambda s: (s["ep"], s["start"]))
            u["video_segments"] = segs
            filled += 1
            print(f"Day {u['seq']:03d} {u['title_zh'][:24]}")
            for s in segs:
                print(f"    {s['ep']} {fmt(s['start']):>7}  {s['title']}")
        else:
            skipped += 1

    if args.dry_run:
        print(f"\n（--dry-run，未寫檔）已定位 {filled} 個單元、{skipped} 個無法定位")
        return
    CURRICULUM.write_text(json.dumps(curriculum, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 已寫回 sc200_curriculum.json：{filled} 個單元有時間碼、{skipped} 個略過"
          f"（該 EP 無字幕或該課未撰寫）")


if __name__ == "__main__":
    main()
