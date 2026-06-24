#!/usr/bin/env python3
"""
build_video_index.py
====================
從已 commit 的 transcripts/ 與 cissp_curriculum.json 建立 video_index.json。

背景：原本應由本機的 prepare_youtube.py 產生並 commit video_index.json，但本 repo 只
commit 了 transcripts/*.txt，沒有 video_index.json（也沒有逐片 YouTube 標題可靠地分類
mindmap/practice）。本腳本因此只「確定地」登記 8 支 Domain 課程影片（course，ID 已知、
有字幕），其餘 mindmap/practice 影片在生成信件與排程時退回對應 playlist URL（符合大綱的
備援路徑）。

不連 YouTube；只讀本地檔案。可重跑。
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS = ROOT / "transcripts"
CURRICULUM = ROOT / "cissp_curriculum.json"

# 8 支 Domain 完整課程影片（內容分類 course，ID 已知）
DOMAIN_VIDEOS = {
    "D1": "J-su239XmCE", "D2": "dNIcfKYeJI8", "D3": "P5So8_NKxz4", "D4": "tQCgAteRyIo",
    "D5": "VknzQFVUfIc", "D6": "lt_-KqplT5o", "D7": "8zM89KMRniM", "D8": "vg-o5lKcwsA",
}


def main():
    curriculum = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    domains = {d["id"]: d for d in curriculum["domains"]}

    videos = []
    for dom, vid in DOMAIN_VIDEOS.items():
        txt = TRANSCRIPTS / f"{vid}.txt"
        chars = len(txt.read_text(encoding="utf-8", errors="ignore")) if txt.exists() else 0
        videos.append({
            "id": vid,
            "title": f"CISSP Full Course 2026 – {dom} {domains[dom]['name_en']}",
            "url": f"https://youtu.be/{vid}",
            "playlists": ["course_2026"],
            "category": "course",
            "domain": dom,
            "transcript_chars": chars,
            "transcript_file": f"transcripts/{vid}.txt",
        })

    by_category = {"course": [v["id"] for v in videos], "mindmap": [], "practice": [], "other": []}
    domain_chapters = {dom: {"video_id": vid, "chapters": []} for dom, vid in DOMAIN_VIDEOS.items()}

    vr = curriculum["video_resources"]
    index = {
        "videos": videos,
        "by_category": by_category,
        "domain_chapters": domain_chapters,
        "playlists": {
            "course_2026": vr["course_2026_series"]["playlist"],
            "mindmap": vr["mindmap_review_series"]["playlist"],
            "practice": vr["practice_questions_series"]["playlist"],
        },
        "note": ("course 8 支已確定登記（ID 已知、有字幕）；mindmap/practice 缺逐片標題，"
                 "生成時退回對應 playlist URL（大綱備援路徑）。category 依影片內容判定。"),
    }
    out = ROOT / "video_index.json"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已產生 video_index.json（course {len(videos)} 支）")
    for v in videos:
        print(f"   {v['domain']} {v['id']} — {v['transcript_chars']:,} 字")


if __name__ == "__main__":
    main()
