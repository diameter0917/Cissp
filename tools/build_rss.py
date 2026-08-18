#!/usr/bin/env python3
"""
build_rss.py — SC-200 Podcast RSS 與節目頁（stdlib only）
=========================================================
sc200/podcast/episodes.json（gen_podcast.py 的 manifest）
→ docs/sc200/podcast.xml（RSS 2.0 + itunes namespace，可用 Podcast App 訂閱）
→ docs/sc200/podcast/index.html（集數列表：播放器＋逐字稿摺疊）

用法：python tools/build_rss.py --project sc200|cissp
"""

import argparse
import email.utils
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
_ap = argparse.ArgumentParser(add_help=False)
_ap.add_argument("--project", default="sc200")
PROJECT = _ap.parse_known_args()[0].project
SC200 = ROOT / PROJECT          # 專案目錄（sc200／cissp），沿用原變數名以免大改
DOCS = ROOT / "docs" / PROJECT
TAIPEI = timezone(timedelta(hours=8))


def load(p, dflt=None):
    if not p.exists():
        return dflt
    return json.loads(p.read_text(encoding="utf-8"))


def fmt_dur(sec):
    m, s = divmod(int(sec or 0), 60)
    return f"{m}:{s:02d}"


def main():
    config = json.loads((SC200 / "site_config.json").read_text(encoding="utf-8"))
    pod = config["podcast"]
    base = config["base_url"].rstrip("/")
    manifest = load(SC200 / "podcast" / "episodes.json", {"episodes": {}})
    schedule = load(SC200 / "schedule.json", {"items": []})
    ep_date = {it.get("episode"): it["date"] for it in schedule["items"] if it.get("episode")}
    ep_title = {it.get("episode"): it["title_zh"] for it in schedule["items"] if it.get("episode")}

    site = f"{base}/{PROJECT}"
    items_xml = []
    episodes = sorted(manifest["episodes"].values(), key=lambda e: e["episode"])
    for e in episodes:
        n = e["episode"]
        title = f"EP{n}｜{e.get('title_zh') or ep_title.get(n, '')}"
        d = ep_date.get(n)
        if d:
            dt = datetime.fromisoformat(d).replace(hour=7, tzinfo=TAIPEI)
        else:
            dt = datetime.now(tz=TAIPEI)
        url = f"{site}/podcast/{e['file']}"
        items_xml.append(f"""    <item>
      <title>{escape(title)}</title>
      <description>{escape(f"對應單元：{e.get('unit') or ''}。雙主持人帶你複習當日考點。")}</description>
      <enclosure url="{escape(url)}" length="{e['bytes']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{PROJECT}-ep-{n:03d}</guid>
      <pubDate>{email.utils.format_datetime(dt)}</pubDate>
      <itunes:duration>{fmt_dur(e.get('duration_sec'))}</itunes:duration>
      <itunes:episode>{n}</itunes:episode>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(pod['title'])}</title>
    <link>{escape(site + '/podcast/index.html')}</link>
    <description>{escape(pod['subtitle'])}</description>
    <language>{pod['language']}</language>
    <atom:link href="{escape(site + '/podcast.xml')}" rel="self" type="application/rss+xml"/>
    <itunes:author>{escape(pod['author'])}</itunes:author>
    <itunes:category text="{pod['category']}"/>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""
    (DOCS / "podcast.xml").write_text(rss, encoding="utf-8")

    # ---- 節目頁 ----
    cards = []
    for e in episodes:
        n = e["episode"]
        key = f"{n:03d}"
        script = load(SC200 / "podcast" / "scripts" / f"ep-{key}.json")
        transcript = ""
        if script:
            spk = {"host_f": "曉臻", "host_m": "雲哲"}
            lines = "".join(
                f"<p><span class='spk'>{spk.get(t['speaker'], t['speaker'])}：</span>{escape(t['text'])}</p>"
                for t in script["dialogue"])
            transcript = (f"<details class='transcript-toggle'><summary>展開逐字稿</summary>"
                          f"<div class='transcript-body'>{lines}</div></details>")
        cards.append(f"""<div class="podcast-box" id="ep-{key}">
  <div class="p-label">EP{n} · {escape(e.get('unit') or '')} · {fmt_dur(e.get('duration_sec'))}</div>
  <div class="p-title">{escape(e.get('title_zh') or '')}</div>
  <audio controls preload="none" src="{e['file']}"></audio>
  {transcript}
</div>""")

    page = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(pod['title'])}</title>
<link rel="stylesheet" href="../../assets/study.css">
<link rel="alternate" type="application/rss+xml" title="{escape(pod['title'])}" href="../podcast.xml">
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <div class="kicker">🎧 {escape(pod['title'])}</div>
    <h1>{escape(pod.get("headline") or pod["title"])}</h1>
    <p class="sub">{escape(pod['subtitle'])}。{escape(pod.get("blurb") or "")}</p>
    <div class="meta-row">
      <span class="pill ghost">共 {len(episodes)} 集</span>
      <span class="pill ghost">AI 生成（edge-tts 曉臻×雲哲）</span>
    </div>
  </header>
  <div class="info-box">📡 <strong>用 Podcast App 訂閱</strong>：複製
    <a href="../podcast.xml">RSS 連結</a>（<code>{escape(site + '/podcast.xml')}</code>）
    貼到 Apple Podcasts／Pocket Casts 的「透過 URL 加入節目」即可。</div>
  {chr(10).join(cards) if cards else "<div class='info-box'>音檔生成中——腳本 push 後由 GitHub Actions 自動合成。</div>"}
  <footer class="colophon">
    <a href="../index.html">學習儀表板</a> · <a href="../quiz.html">刷題</a>
  </footer>
</div>
</body>
</html>
"""
    (DOCS / "podcast").mkdir(parents=True, exist_ok=True)
    (DOCS / "podcast" / "index.html").write_text(page, encoding="utf-8")
    print(f"✅ podcast.xml（{len(episodes)} 集）與 podcast/index.html 已更新")


if __name__ == "__main__":
    main()
