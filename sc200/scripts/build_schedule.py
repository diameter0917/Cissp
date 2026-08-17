#!/usr/bin/env python3
"""
build_schedule.py（SC-200 版）
==============================
由 sc200_curriculum.json 產生 schedule.json（日期 → 單元），並複製到 docs/sc200/。

規則：
  - 依 units 的 seq 順序，從 start_date 起只排週一至週五（40 個工作日＝8 週）。
  - study 單元 → newsletter/day-NNN.html＋podcast/ep-NN.mp3＋quiz.html?unit=<code>
  - drill 單元 → drill/day-NNN.html＋依 quiz_spec 組出 quiz.html 深連結

用法：python sc200/scripts/build_schedule.py [YYYY-MM-DD]
      不給日期時用 site_config.json 的 start_date。
"""

import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode

SC200 = Path(__file__).resolve().parents[1]
ROOT = SC200.parent
DOCS = ROOT / "docs" / "sc200"
TIMEZONE = "Asia/Taipei"


def next_weekday(d: date) -> date:
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d += timedelta(days=1)
    return d


def quiz_url(unit) -> str | None:
    """依 quiz_spec（drill）或 unit 代碼（study）組出刷題深連結。"""
    if unit["type"] == "study":
        return f"quiz.html?{urlencode({'unit': unit['code']})}"
    spec = unit.get("quiz_spec")
    if not spec:
        return None
    params = {k: v for k, v in spec.items() if k != "then"}
    return f"quiz.html?{urlencode(params)}"


def main():
    curriculum = json.loads((SC200 / "sc200_curriculum.json").read_text(encoding="utf-8"))
    config = json.loads((SC200 / "site_config.json").read_text(encoding="utf-8"))
    domains = {d["id"]: d for d in curriculum["domains"]}

    if len(sys.argv) > 1:
        y, m, dd = map(int, sys.argv[1].split("-"))
        start = date(y, m, dd)
    else:
        start = date.fromisoformat(config["start_date"])

    ep_count = 0
    cur = next_weekday(start)
    items = []
    for unit in sorted(curriculum["units"], key=lambda u: u["seq"]):
        cur = next_weekday(cur)
        seq = unit["seq"]
        dom = domains[unit["domain"]]
        item = {
            "date": cur.isoformat(),
            "seq": seq,
            "phase": unit["phase"],
            "week": unit["week"],
            "type": unit["type"],
            "code": unit["code"],
            "domain": unit["domain"],
            "domain_name_zh": dom["name_zh"],
            "weight": dom["weight"],
            "title_zh": unit["title_zh"],
            "title_en": unit.get("title_en", ""),
            "quiz_url": quiz_url(unit),
        }
        if unit["type"] == "study":
            ep_count += 1
            item["page_url"] = f"newsletter/day-{seq:03d}.html"
            item["podcast_url"] = f"podcast/ep-{ep_count:03d}.mp3"
            item["episode"] = ep_count
            item["video_eps"] = unit.get("video_eps", [])
        else:
            item["page_url"] = f"drill/day-{seq:03d}.html"
        items.append(item)
        cur += timedelta(days=1)

    schedule = {
        "start_date": start.isoformat(),
        "exam_date": config["exam_date"],
        "timezone": TIMEZONE,
        "weekdays_only": True,
        "total": len(items),
        "items": items,
    }

    out = SC200 / "schedule.json"
    out.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")
    DOCS.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(out), str(DOCS / "schedule.json"))

    print(f"✅ 已產生 sc200/schedule.json（{len(items)} 單元）並複製到 docs/sc200/")
    print(f"   起始日 {start.isoformat()}（{TIMEZONE}），最後一天 {items[-1]['date']}，"
          f"考試日 {config['exam_date']}")


if __name__ == "__main__":
    main()
