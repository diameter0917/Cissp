#!/usr/bin/env python3
"""
fetch_transcripts.py — SC-200 官方影片字幕抓取
=================================================
在「能連 YouTube 的環境」執行一次（GitHub Actions runner 或本機皆可），
產生 SC-200 教材產製所需的影片衍生檔案，之後 commit 進 repo ——
教材撰寫階段就不必再連 YouTube。（模式沿用根目錄 prepare_youtube.py）

對 EP1–EP10 每支影片抓取：
  - sc200/transcripts/ep-NN.info.json        標題/頻道/長度/章節/可用字幕語言
  - sc200/transcripts/ep-NN.<lang>.txt       清理後純文字字幕（原文 + 自動翻譯繁中）
  - sc200/transcripts/_timed/ep-NN.<lang>.vtt 帶時間碼字幕（教材時間軸定位用）
  - sc200/transcripts/index.json             總覽（各 EP 抓取狀態）

需求：python -m pip install -U yt-dlp
用法：python sc200/scripts/fetch_transcripts.py [--force]
      已抓過的 EP 會略過（--force 重抓）；中斷可重跑續抓。
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

YTDLP = [sys.executable, "-m", "yt_dlp"]

# EP1–EP10 官方影片（使用者提供）
EPISODES = {
    "EP1": "8gCUtYEpTe8",
    "EP2": "QmvVYOG4uWI",
    "EP3": "5ln3fMECedU",
    "EP4": "e7UxqMgb1zk",
    "EP5": "Nt7f2Bog89c",
    "EP6": "3DHcnk9obfk",
    "EP7": "0ydVILka3eg",
    "EP8": "hOYpji940yw",
    "EP9": "qlyEmMLif_M",
    "EP10": "z6QbN4rpAvA",
}

# 想要的字幕語言，**逐一**下載（一次要求多語會連發請求，容易觸發 429 限流）。
# zh-Hant 是 YouTube 的自動翻譯軌；en 是原文自動字幕。兩者取到任一支即可用。
SUB_LANGS = ["zh-Hant", "en"]

# player client 輪替**只用於 metadata**：bot 偵測擋 metadata 時換 client 有效。
# 字幕不可輪替——web_embedded／tv 這些 client 不供應字幕軌，換過去只會得到
# 「Requested format is not available」「This video is DRM protected」等誤導訊息。
CLIENT_ATTEMPTS = [
    None,
    "youtube:player_client=android,web",
    "youtube:player_client=web_embedded,web",
    "youtube:player_client=tv",
]

# 429（Too Many Requests）退避秒數：限流要等，換 client 沒用。
BACKOFF_429 = [0, 60, 180, 420]

TRANSCRIPTS = Path(__file__).resolve().parents[1] / "transcripts"
TIMED = TRANSCRIPTS / "_timed"


def run_with_retry(args, what):
    """yt-dlp 呼叫加三段式重試（每次換 player client、指數退避）。"""
    last = None
    for i, client in enumerate(CLIENT_ATTEMPTS, 1):
        cmd = YTDLP + ["--retries", "5", "--sleep-requests", "0.75"]
        if client:
            cmd += ["--extractor-args", client]
        cmd += args
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            return r
        last = r
        msg = (r.stderr or "").strip().splitlines()
        print(f"    ⚠️ {what} 第 {i} 次失敗：{msg[-1][:120] if msg else '未知錯誤'}")
        time.sleep(5 * i)
    return last


def fetch_info(ep, vid):
    """抓 metadata（標題/章節/可用字幕語言），瘦身後存 info.json。"""
    r = run_with_retry(["-J", "--skip-download", f"https://youtu.be/{vid}"], f"{ep} metadata")
    if r is None or r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None
    info = {
        "ep": ep,
        "id": data.get("id"),
        "url": f"https://youtu.be/{vid}",
        "title": data.get("title"),
        "channel": data.get("channel") or data.get("uploader"),
        "duration_sec": data.get("duration"),
        "duration_string": data.get("duration_string"),
        "upload_date": data.get("upload_date"),
        "language": data.get("language"),
        "chapters": [
            {"start": int(c.get("start_time", 0)), "title": c.get("title", "")}
            for c in (data.get("chapters") or [])
        ],
        "manual_sub_langs": sorted((data.get("subtitles") or {}).keys()),
        "auto_sub_has_zh_hant": "zh-Hant" in (data.get("automatic_captions") or {}),
        "description_head": (data.get("description") or "")[:2000],
    }
    (TRANSCRIPTS / f"{ep_slug(ep)}.info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


def ep_slug(ep):
    """EP1 → ep-01（排序友善）。"""
    return f"ep-{int(ep[2:]):02d}"


def fetch_title_oembed(ep, vid):
    """yt-dlp 被 bot 偵測擋下時的退路：oEmbed 端點通常不設 bot 檢查，可拿到標題/頻道。"""
    url = f"https://www.youtube.com/oembed?url=https://youtu.be/{vid}&format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001 - 任何失敗都視為拿不到
        print(f"    ⚠️ oEmbed 也失敗：{e}")
        return None
    info = {
        "ep": ep, "id": vid, "url": f"https://youtu.be/{vid}",
        "title": data.get("title"), "channel": data.get("author_name"),
        "duration_sec": None, "duration_string": None, "upload_date": None,
        "language": None, "chapters": [], "manual_sub_langs": [],
        "auto_sub_has_zh_hant": None, "description_head": "",
        "source": "oembed_fallback",
    }
    (TRANSCRIPTS / f"{ep_slug(ep)}.info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


def sub_to_text(path):
    """VTT/SRT → 去時間碼、去標籤、去連續重複的純文字（同 prepare_youtube.py）。"""
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


def fetch_one_lang(ep, vid, lang, slug, cookies=None, slow=False):
    """抓單一語言字幕。遇 429 限流就等待重試（**不**換 player client）。"""
    for i, wait in enumerate(BACKOFF_429, 1):
        if wait:
            print(f"    ⏳ {ep} {lang} 被限流，等 {wait} 秒再試（第 {i}/{len(BACKOFF_429)} 次）…")
            time.sleep(wait)
        cmd = YTDLP + [
            "--skip-download", "--write-subs", "--write-auto-subs",
            "--sub-langs", lang, "--sub-format", "vtt",
            "--sleep-requests", "8" if slow else "3",
            "--retry-sleep", "http:exp=10:300",
            "--extractor-retries", "5",
            "-o", str(TRANSCRIPTS / f"{slug}.%(ext)s"),
        ]
        if cookies:
            cmd += ["--cookies-from-browser", cookies]
        cmd.append(f"https://youtu.be/{vid}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and list(TRANSCRIPTS.glob(f"{slug}.{lang}*.vtt")):
            return True
        err = (r.stderr or "").strip().splitlines()
        last = err[-1][:130] if err else "未知錯誤"
        if "429" in last or "Too Many Requests" in last:
            continue                       # 限流 → 退避後重試
        if "no subtitles" in last.lower() or "requested format" in last.lower():
            print(f"    ℹ️ {ep} 沒有 {lang} 字幕軌")
            return False                   # 這個語言真的沒有 → 不必再試
        print(f"    ⚠️ {ep} {lang} 失敗：{last}")
        return False
    print(f"    ✗ {ep} {lang} 持續被限流，稍後再跑一次即可續抓")
    return False


def fetch_subs(ep, vid, cookies=None, slow=False):
    """逐語言抓字幕（zh-Hant 自動翻譯軌 + en 原文）→ 清理存 txt、保留帶時間碼 vtt。"""
    slug = ep_slug(ep)
    for lang in SUB_LANGS:
        if (TRANSCRIPTS / f"{slug}.{lang}.txt").exists():
            continue                       # 這語言已抓過（支援中斷續跑）
        fetch_one_lang(ep, vid, lang, slug, cookies=cookies, slow=slow)
        time.sleep(5 if slow else 2)       # 語言之間也留間隔，別連發
    got = {}
    for vtt in sorted(TRANSCRIPTS.glob(f"{slug}.*.vtt")):
        lang = vtt.name[len(slug) + 1:-4]  # ep-01.<lang>.vtt → <lang>
        txt = sub_to_text(vtt)
        if txt:
            (TRANSCRIPTS / f"{slug}.{lang}.txt").write_text(txt, encoding="utf-8")
            TIMED.mkdir(exist_ok=True)
            vtt.replace(TIMED / vtt.name)
            got[lang] = len(txt)
        else:
            vtt.unlink()
    return got


def already_done(ep):
    """兩種語言都到手才算完成——只抓到一種時重跑會續抓另一種。"""
    slug = ep_slug(ep)
    if not (TRANSCRIPTS / f"{slug}.info.json").exists():
        return False
    return all((TRANSCRIPTS / f"{slug}.{lang}.txt").exists() for lang in SUB_LANGS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="忽略已存在檔案全部重抓")
    ap.add_argument("--slow", action="store_true",
                    help="放慢請求（被 429 限流時用；每支影片間也多等一會）")
    ap.add_argument("--cookies-from-browser", dest="cookies", metavar="BROWSER",
                    help="用瀏覽器 cookies（chrome/edge/firefox…）；先在該瀏覽器登入 YouTube")
    ap.add_argument("--only", nargs="*", metavar="EP",
                    help="只抓指定影片，如 --only EP1 EP2")
    args = ap.parse_args()

    r = subprocess.run(YTDLP + ["--version"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("✗ 找不到 yt-dlp。請先：python -m pip install -U yt-dlp")
    print("yt-dlp 版本:", r.stdout.strip())

    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    targets = {k: v for k, v in EPISODES.items()
               if not args.only or k.upper() in {s.upper() for s in args.only}}
    if not targets:
        sys.exit(f"✗ --only 沒有對到任何影片。可用：{', '.join(EPISODES)}")

    index = []
    for n, (ep, vid) in enumerate(targets.items()):
        if n:
            time.sleep(15 if args.slow else 5)   # 影片之間留間隔，降低被限流機率
        print(f"\n[{ep}] https://youtu.be/{vid}")
        if not args.force and already_done(ep):
            info = json.loads((TRANSCRIPTS / f"{ep_slug(ep)}.info.json").read_text(encoding="utf-8"))
            langs = {p.name[len(ep_slug(ep)) + 1:-4]: p.stat().st_size
                     for p in TRANSCRIPTS.glob(f"{ep_slug(ep)}.*.txt")}
            index.append({"ep": ep, "id": vid, "title": info.get("title"),
                          "status": "cached", "langs": langs})
            print(f"    略過（已存在）：{info.get('title') or ''}")
            continue
        info = fetch_info(ep, vid)
        if info is None:
            info = fetch_title_oembed(ep, vid)
            if info is not None:
                index.append({"ep": ep, "id": vid, "title": info["title"],
                              "status": "title_only", "langs": {}})
                print(f"    △ 僅取得標題（oEmbed）：{info['title']}")
            else:
                index.append({"ep": ep, "id": vid, "title": None,
                              "status": "metadata_failed", "langs": {}})
                print("    ✗ metadata 抓取失敗（可能被 bot 偵測擋下）")
            continue
        print(f"    《{info['title']}》 {info['duration_string']}，章節 {len(info['chapters'])} 個")
        langs = fetch_subs(ep, vid, cookies=args.cookies, slow=args.slow)
        status = "ok" if langs else "no_subs"
        index.append({"ep": ep, "id": vid, "title": info["title"],
                      "status": status, "langs": langs})
        if langs:
            print("    字幕：", "、".join(f"{k} {v:,} 字" for k, v in langs.items()))
        else:
            print("    ⚠️ 無可用字幕")

    (TRANSCRIPTS / "index.json").write_text(
        json.dumps({"episodes": index}, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for e in index if e["status"] in ("ok", "cached"))
    print(f"\n{'✅' if ok == len(EPISODES) else '⚠️'} 完成：{ok}/{len(EPISODES)} 支有字幕。"
          f"結果見 sc200/transcripts/index.json")


if __name__ == "__main__":
    main()
