#!/usr/bin/env python3
"""
build_schedule.py
=================
由 cissp_curriculum.json 產生 schedule.json（日期 → 單元）。

規則：
  - 依 units 的 seq 順序，從 START_DATE 起，只排週一至週五（跳過週六日）。
  - 120 個工作日 ≈ 24 週。
  - 每個單元的 video_url 依其 phase 決定：
      P1（初期）→ 該 Domain 的完整課程影片（course_video_2026），若有 video_index.json
                  則優先用其中的 course 影片連結。
      P2（中期）→ MindMap 主題複習 playlist（找不到精準單片時用 playlist）。
      P3（後期）→ 考題練習 playlist。
  - 跑完複製一份到 docs/schedule.json。

可重跑：改 START_DATE 或之後排「第二輪」時，用 seq 疊代重新生成，不寫死。

用法：python scripts/build_schedule.py [YYYY-MM-DD]
      不給日期時，預設為「執行日之後的下一個工作日」。
"""

import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRICULUM = ROOT / "cissp_curriculum.json"
VIDEO_INDEX = ROOT / "video_index.json"
TIMEZONE = "Asia/Taipei"


def next_weekday(d: date) -> date:
    """回傳 d（不含）之後最近的工作日；若 d 本身是工作日則回 d。"""
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d += timedelta(days=1)
    return d


def resolve_start_date() -> date:
    if len(sys.argv) > 1:
        y, m, dd = map(int, sys.argv[1].split("-"))
        return date(y, m, dd)
    # 預設：今天之後的下一個工作日
    return next_weekday(date.today() + timedelta(days=1))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_video_lookup(curriculum):
    """回傳依 phase + domain 決定 video_url 的函式。"""
    domains = {d["id"]: d for d in curriculum["domains"]}
    vr = curriculum["video_resources"]
    mindmap_playlist = vr["mindmap_review_series"]["playlist"]
    practice_playlist = vr["practice_questions_series"]["playlist"]
    course_by_domain = vr["course_2026_series"]["by_domain"]

    # 若 video_index.json 存在，用它的 course 連結覆蓋（更精準）
    course_index = {}
    if VIDEO_INDEX.exists():
        vidx = load_json(VIDEO_INDEX)
        for v in vidx.get("videos", []):
            if v.get("category") == "course" and v.get("domain"):
                course_index[v["domain"]] = v["url"]

    def pick(phase, domain):
        if phase == "P1":
            return course_index.get(domain) or course_by_domain.get(domain) \
                or domains[domain].get("course_video_2026")
        if phase == "P2":
            return mindmap_playlist
        if phase == "P3":
            return practice_playlist
        return domains[domain].get("course_video_2026")

    return pick


def main():
    curriculum = load_json(CURRICULUM)
    domains = {d["id"]: d for d in curriculum["domains"]}
    pick_video = build_video_lookup(curriculum)

    start = resolve_start_date()
    cur = next_weekday(start)

    items = []
    for unit in sorted(curriculum["units"], key=lambda u: u["seq"]):
        cur = next_weekday(cur)
        seq = unit["seq"]
        dom = domains[unit["domain"]]
        items.append({
            "date": cur.isoformat(),
            "seq": seq,
            "phase": unit["phase"],
            "phase_name_zh": unit["phase_name_zh"],
            "domain": unit["domain"],
            "domain_name_zh": dom["name_zh"],
            "weight": dom["weight"],
            "code": unit["code"],
            "title_zh": unit["title_zh"],
            "title_en": unit["title_en"],
            "email_file": f"emails/day-{seq:03d}.html",
            "archive_url": f"archive/day-{seq:03d}.html",
            "video_url": pick_video(unit["phase"], unit["domain"]),
        })
        cur += timedelta(days=1)  # 推進到隔天，next_weekday 會跳過週末

    schedule = {
        "start_date": start.isoformat(),
        "timezone": TIMEZONE,
        "weekdays_only": True,
        "total": len(items),
        "items": items,
    }

    out = ROOT / "schedule.json"
    out.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")

    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    shutil.copy(str(out), str(docs / "schedule.json"))

    print(f"✅ 已產生 schedule.json（{len(items)} 單元）")
    print(f"   起始日 {start.isoformat()}（{TIMEZONE}），最後一封 {items[-1]['date']}")
    print(f"   已複製到 docs/schedule.json")


if __name__ == "__main__":
    main()
