#!/usr/bin/env python3
"""
build_archive.py
================
由 emails/day-XXX.html 產生網頁瀏覽版 docs/archive/day-XXX.html。

差異（與寄信版相比）：
  - 頁尾「← 回索引總表」連回 index.html（相對連結）。
  - 若 news/day-XXX-news.html 存在則合併進 <!-- TODAY_NEWS -->，否則移除占位標記。
  - 其餘版型與內容完全一致（email-safe inline CSS，兩邊視覺一致）。

只處理 emails/ 下實際存在的檔案，方便分批生成。可重跑。
用法：python scripts/build_archive.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMAILS = ROOT / "emails"
ARCHIVE = ROOT / "docs" / "archive"
NEWS = ROOT / "news"
NEWS_MARKER = "<!-- TODAY_NEWS -->"


def main():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    files = sorted(EMAILS.glob("day-*.html"))
    if not files:
        print("emails/ 下沒有 day-*.html，先生成教材。")
        return

    count = 0
    for f in files:
        m = re.search(r"day-(\d+)\.html", f.name)
        if not m:
            continue
        seq = int(m.group(1))
        html = f.read_text(encoding="utf-8")

        # 合併今日時事（有就放，沒有就移除占位）
        news_file = NEWS / f"day-{seq:03d}-news.html"
        if news_file.exists():
            html = html.replace(NEWS_MARKER, news_file.read_text(encoding="utf-8").strip())
        else:
            html = html.replace(NEWS_MARKER, "")

        # 頁尾回索引連結指向 index.html
        html = html.replace(
            '<a href="#" style="font-size:13px; color:#0E7C7B; text-decoration:none; font-weight:600;">← 回索引總表</a>',
            '<a href="index.html" style="font-size:13px; color:#0E7C7B; text-decoration:none; font-weight:600;">← 回索引總表</a>',
        )

        (ARCHIVE / f.name).write_text(html, encoding="utf-8")
        count += 1

    print(f"✅ 已產生 {count} 個 archive 頁面到 docs/archive/")


if __name__ == "__main__":
    main()
