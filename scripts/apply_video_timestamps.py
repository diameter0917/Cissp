#!/usr/bin/env python3
"""
apply_video_timestamps.py
=========================
為「初期 P1」的教材信補上影片深連結時間碼。

大綱規定：P1 課程影片沒有章節，改用 transcripts/_timed/<id>.vtt，搜尋當天主題英文關鍵字
首次出現的時間碼，做成深連結 https://youtu.be/<id>?t=<秒數>，文案標「從約 mm:ss 開始」；
定位不到（或沒有 _timed 檔）就連影片開頭、不標時間。中期/後期是單一主題短片，不需時間軸。

本腳本掃 emails/day-XXX.html（只處理 P1），對每封：
  1. 找出該封的 course 影片 id（由 schedule.json 的 video_url）。
  2. 若 transcripts/_timed/<id>.vtt 存在，搜該單元關鍵字最早出現的 cue 起始秒數。
  3. 命中 → 把影片 anchor 的 href 加上 ?t=<秒>，並把占位 <span class="ts-note"></span>
     換成「（從約 mm:ss 開始）」。
  4. 沒命中 / 沒 _timed → 還原成連開頭、占位留空（優雅降級）。

依賴標準化的影片區塊：anchor href="https://youtu.be/<id>"（可帶 ?t=），及占位
<span class="ts-note">...</span>。emails 由本系統生成，皆含此占位。

不連 YouTube；只讀本地檔。可重跑（idempotent）。
用法：python scripts/apply_video_timestamps.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMAILS = ROOT / "emails"
TIMED = ROOT / "transcripts" / "_timed"
CURRICULUM = ROOT / "cissp_curriculum.json"
SCHEDULE = ROOT / "schedule.json"

# 噪音詞：標題中不適合當搜尋關鍵字者
STOP = {
    "domain", "big", "picture", "overview", "the", "and", "of", "in", "to", "a",
    "&", "deep", "dive", "exam", "amp", "vs", "or", "for", "with",
}

# 可選的精選關鍵字覆蓋（命中率較高的主題詞，依 unit code）
CURATED = {
    "P1-D1-1": ["CIA triad", "confidentiality", "integrity", "availability"],
    "P1-D1-2": ["security governance", "governance", "due care", "due diligence"],
    "P1-D1-3": ["risk management", "threat", "vulnerability", "risk assessment"],
    "P1-D1-4": ["intellectual property", "compliance", "privacy", "ethics", "GDPR"],
    "P1-D1-5": ["business continuity", "BCP", "supply chain", "personnel"],
}


def parse_vtt(path: Path):
    """回傳 [(start_seconds, lowercased_text), ...]，依時間排序。"""
    cues = []
    cur_start = None
    buf = []
    ts_re = re.compile(r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->")
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = ts_re.search(line)
        if m:
            if cur_start is not None and buf:
                cues.append((cur_start, " ".join(buf).lower()))
            h, mn, s, _ = m.groups()
            cur_start = int(h) * 3600 + int(mn) * 60 + int(s)
            buf = []
        elif "-->" in line or line.strip().upper().startswith(("WEBVTT", "KIND:", "LANGUAGE:")):
            continue
        elif line.strip() and not line.strip().isdigit():
            buf.append(re.sub(r"<[^>]+>", "", line).strip())
    if cur_start is not None and buf:
        cues.append((cur_start, " ".join(buf).lower()))
    cues.sort(key=lambda c: c[0])
    return cues


def keywords_for(code, title_en):
    if code in CURATED:
        return CURATED[code]
    # 從 title_en 萃取：去噪、保留有意義詞；先試雙詞片語再單詞
    toks = [t for t in re.split(r"[\s,/]+", title_en) if t and t.lower() not in STOP]
    phrases = []
    for i in range(len(toks) - 1):
        phrases.append(f"{toks[i]} {toks[i+1]}")
    phrases += toks
    # 去重保序
    seen, out = set(), []
    for p in phrases:
        k = p.lower()
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


INTRO_SKIP = 120     # 跳過開場前 120 秒的議程/名詞 name-drop
WINDOW = 120         # 密度視窗（秒）：找關鍵字最密集的時段＝主題真正開講處


def _cue_score(text, keywords):
    """該 cue 命中的關鍵字加權分數：多詞片語權重高於單字（精準＞泛詞）。"""
    score = 0
    for kw in keywords:
        if kw.lower() in text:
            score += len(kw.split())   # "risk management"=2、"risk"=1
    return score


def find_timestamp(cues, keywords):
    """密度定位：跳過 intro，找關鍵字最密集的視窗，回傳該段最早命中的秒數。

    步驟：
      1. 算每個 cue 的關鍵字加權分數（多詞片語權重較高）。
      2. 以每個「有分數且過了 intro」的 cue 為視窗起點，加總 [t, t+WINDOW] 內分數。
      3. 取總分最高的視窗（同分取較早），回傳該視窗內第一個有分數 cue 的起始秒數。
      4. 全部落在 intro / 完全沒命中時，退回「首次出現」(含 intro)；再無則回 None。
    """
    scored = [(start, _cue_score(text, keywords)) for start, text in cues]
    hits = [(s, sc) for s, sc in scored if sc > 0]
    if not hits:
        return None

    main_hits = [(s, sc) for s, sc in hits if s >= INTRO_SKIP]
    pool = main_hits if main_hits else hits   # 全在 intro 就退回全體

    best_total, best_start = -1, None
    for i, (t0, _) in enumerate(pool):
        total = sum(sc for s, sc in pool if t0 <= s <= t0 + WINDOW)
        if total > best_total:
            best_total, best_start = total, t0
    return best_start



def mmss(sec):
    return f"{sec // 60:02d}:{sec % 60:02d}"


def video_id(url):
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url or "")
    return m.group(1) if m else None


def apply_to_email(path: Path, vid: str, t_sec):
    html = path.read_text(encoding="utf-8")
    original = html

    # 1) href：先還原成不帶 t，再視情況加上
    html = re.sub(rf'href="https://youtu\.be/{re.escape(vid)}(?:\?t=\d+)?"',
                  f'href="https://youtu.be/{vid}"', html)
    if t_sec is not None:
        html = html.replace(f'href="https://youtu.be/{vid}"',
                            f'href="https://youtu.be/{vid}?t={t_sec}"')

    # 2) 占位 span：填入或清空
    note = f"（從約 {mmss(t_sec)} 開始）" if t_sec is not None else ""
    html = re.sub(r'<span class="ts-note">.*?</span>',
                  f'<span class="ts-note">{note}</span>', html)

    if html != original:
        path.write_text(html, encoding="utf-8")
        return True
    return False


def main():
    if not SCHEDULE.exists():
        print("找不到 schedule.json，先跑 build_schedule.py。")
        return
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    curr = {u["code"]: u for u in json.loads(CURRICULUM.read_text(encoding="utf-8"))["units"]}

    has_timed = TIMED.exists() and any(TIMED.glob("*.vtt"))
    if not has_timed:
        print("ℹ️ 無 transcripts/_timed/*.vtt：所有完整課程影片連開頭、時間碼留空（優雅降級）。")

    vtt_cache = {}
    hit = miss = 0
    for item in schedule["items"]:
        email = ROOT / item["email_file"]
        if not email.exists():
            continue
        # 時間碼套在「② 完整課程」連結（course 影片）；重點短片不需時間軸
        course = item.get("video_course") or {}
        vid = video_id(course.get("url") or item.get("video_url"))
        if not vid:
            continue

        t_sec = None
        vtt = TIMED / f"{vid}.vtt"
        if vtt.exists():
            if vid not in vtt_cache:
                vtt_cache[vid] = parse_vtt(vtt)
            u = curr.get(item["code"], {})
            kws = keywords_for(item["code"], u.get("title_en", item["title_en"]))
            t_sec = find_timestamp(vtt_cache[vid], kws)

        changed = apply_to_email(email, vid, t_sec)
        if t_sec is not None:
            hit += 1
            print(f"   {item['code']} {email.name} → ?t={t_sec}（{mmss(t_sec)}）{'✏️' if changed else ''}")
        else:
            miss += 1

    print(f"✅ P1 影片時間碼套用完成：命中 {hit}、連開頭 {miss}。")
    if not has_timed:
        print("   👉 要啟用時間碼：本機跑 prepare_youtube.py 產生 transcripts/_timed/<id>.vtt 並 commit，再跑本腳本。")


if __name__ == "__main__":
    main()
