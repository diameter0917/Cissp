#!/usr/bin/env python3
"""
prepare_youtube.py
==================
在「能連 YouTube 的本機電腦」執行一次，產生 CISSP 電子報系統需要的 YouTube 衍生檔案，
之後 commit 進 cissp repo —— Claude Code 就不必再連 YouTube。

重點：影片用「內容」分類，不看它在哪個 playlist（playlist 是混的，同一支可同時出現在多個清單）。

產出：
  - video_index.json              全部影片(去重) + 內容分類(category) + 出現的 playlists + 字幕長度 + Domain 章節
  - transcripts/<video_id>.txt    每支影片英文字幕純文字（供各階段教材對齊）
  - transcripts/_timed/<id>.vtt   8 支 Domain 課程影片的帶時間碼字幕（影片時間軸近似定位用）

需求：python -m pip install -U yt-dlp （ffmpeg 非必要）
用法：python prepare_youtube.py     可重跑：已抓過的 <id>.txt 會略過，中斷可再跑續抓。
"""

import json
import subprocess
import sys
import re
import shutil
from pathlib import Path

YTDLP = [sys.executable, "-m", "yt_dlp"]

# 這些是「來源 playlist」，只用來蒐集影片清單，不代表分類
PLAYLISTS = {
    "course_2026": "https://youtube.com/playlist?list=PLZKdGEfEyJhLd-pJhAD7dNbJyUgpqI4pu",
    "mindmap":     "https://youtube.com/playlist?list=PLZKdGEfEyJhKWyryIvx_jm1jn6ZMTi7gW",
    "practice":    "https://youtube.com/playlist?list=PLNoUpEKd6YvAYFgJOoSGr5yNJBMOQCkh8",
}

# 8 支 Domain 完整課程影片（內容分類為 course；額外留時間碼字幕）
DOMAIN_VIDEOS = {
    "D1": "J-su239XmCE", "D2": "dNIcfKYeJI8", "D3": "P5So8_NKxz4", "D4": "tQCgAteRyIo",
    "D5": "VknzQFVUfIc", "D6": "lt_-KqplT5o", "D7": "8zM89KMRniM", "D8": "vg-o5lKcwsA",
}
DOMAIN_IDS = set(DOMAIN_VIDEOS.values())
ID2DOMAIN = {v: k for k, v in DOMAIN_VIDEOS.items()}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def check_ytdlp():
    r = run(YTDLP + ["--version"])
    if r.returncode != 0:
        sys.exit("✗ 找不到 yt-dlp。請先安裝：python -m pip install -U yt-dlp")
    print("yt-dlp 版本:", r.stdout.strip())


def flat_playlist(url):
    r = run(YTDLP + ["--flat-playlist", "-J", url])
    if r.returncode != 0:
        print("  ⚠️ playlist 解析失敗:", r.stderr[:200])
        return []
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return []
    return [{"id": e["id"], "title": e.get("title") or ""}
            for e in (data.get("entries", []) or []) if e.get("id")]


def guess_domain(title):
    m = re.search(r"Domain\s*([1-8])", title or "", re.I)
    return f"D{m.group(1)}" if m else None


def classify(video_id, title):
    """用內容分類，回傳 (category, domain)。"""
    if video_id in DOMAIN_IDS:
        return "course", ID2DOMAIN[video_id]
    t = title or ""
    if re.search(r"mind\s*map", t, re.I):
        return "mindmap", guess_domain(t)
    if re.search(r"full\s*course", t, re.I) and guess_domain(t):
        return "course", guess_domain(t)
    if re.search(r"question|practice|quiz|\bexam\b", t, re.I):
        return "practice", guess_domain(t)
    return "other", guess_domain(t)


def get_chapters(video_id):
    r = run(YTDLP + ["-J", "--skip-download", f"https://youtu.be/{video_id}"])
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return []
    return [{"start": int(c.get("start_time", 0)), "title": c.get("title", "")}
            for c in (data.get("chapters") or [])]


def sub_to_text(path):
    raw = Path(path).read_text(encoding="utf-8", errors="ignore")
    out = []
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln or "-->" in ln or ln.isdigit():
            continue
        if ln.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        ln = re.sub(r"<[^>]+>", "", ln).strip()
        if ln:
            out.append(ln)
    dedup = []
    for t in out:
        if not dedup or dedup[-1] != t:
            dedup.append(t)
    return " ".join(dedup)


def get_transcript(video_id, tdir, keep_timed=False):
    final = tdir / f"{video_id}.txt"
    if final.exists():
        return -1
    run(YTDLP + ["--write-auto-subs", "--sub-langs", "en.*", "--skip-download",
                 "-o", str(tdir / "%(id)s.%(ext)s"), f"https://youtu.be/{video_id}"])
    cand = list(tdir.glob(f"{video_id}*.vtt")) + list(tdir.glob(f"{video_id}*.srt"))
    if not cand:
        return None
    txt = sub_to_text(cand[0])
    if keep_timed:
        (tdir / "_timed").mkdir(exist_ok=True)
        shutil.copy(str(cand[0]), str(tdir / "_timed" / f"{video_id}.vtt"))
    for c in cand:
        try:
            c.unlink()
        except OSError:
            pass
    if not txt:
        return None
    final.write_text(txt, encoding="utf-8")
    return len(txt)


def main():
    check_ytdlp()
    tdir = Path("transcripts")
    tdir.mkdir(exist_ok=True)

    print("\n[1/3] 解析三個 playlist，依『內容』分類（去重、記錄出現在哪些清單）…")
    videos = {}  # id -> dict
    for plname, url in PLAYLISTS.items():
        for e in flat_playlist(url):
            vid = e["id"]
            if vid not in videos:
                cat, dom = classify(vid, e["title"])
                videos[vid] = {"id": vid, "title": e["title"],
                               "url": f"https://youtu.be/{vid}",
                               "playlists": [], "category": cat, "domain": dom}
            if plname not in videos[vid]["playlists"]:
                videos[vid]["playlists"].append(plname)
    # 分類統計
    from collections import Counter
    cats = Counter(v["category"] for v in videos.values())
    print(f"   共 {len(videos)} 支（去重後）：", dict(cats))

    print(f"\n[2/3] 下載全部 {len(videos)} 支影片字幕（數分鐘；可中斷後重跑續抓）…")
    done = skipped = nosub = 0
    for i, (vid, v) in enumerate(videos.items(), 1):
        n = get_transcript(vid, tdir, keep_timed=(vid in DOMAIN_IDS))
        if n == -1:
            v["transcript_chars"] = None; skipped += 1; tag = "略過(已存在)"
        elif n is None:
            v["transcript_chars"] = 0; nosub += 1; tag = "⚠️ 無字幕"
        else:
            v["transcript_chars"] = n; done += 1; tag = f"{n:,} 字"
        print(f"   [{i}/{len(videos)}] {vid} [{v['category']}{('/'+v['domain']) if v['domain'] else ''}] {tag} | {(v['title'] or '')[:40]}")
    print(f"   → 新抓 {done}、略過 {skipped}、無字幕 {nosub}")

    print("\n[3/3] 抓 8 支 Domain 課程影片章節 …")
    domain_chapters = {}
    for dom, vid in DOMAIN_VIDEOS.items():
        chs = get_chapters(vid)
        domain_chapters[dom] = {"video_id": vid, "chapters": chs}
        print(f"   {dom} ({vid}): {len(chs)} 個章節")

    by_cat = {}
    for v in videos.values():
        by_cat.setdefault(v["category"], []).append(v["id"])

    video_index = {
        "videos": list(videos.values()),
        "by_category": by_cat,
        "domain_chapters": domain_chapters,
        "note": "category 由影片內容判定，與 playlists（來源清單）無關；transcripts/<id>.txt 為各影片字幕。",
    }
    Path("video_index.json").write_text(
        json.dumps(video_index, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n✅ 完成。category 分類已修正（看內容、非看清單）。")
    print("   commit： git add video_index.json transcripts && git commit -m \"youtube artifacts [skip ci]\" && git push")


if __name__ == "__main__":
    main()
