#!/usr/bin/env python3
"""
build_quiz_site.py — 把 CISSP 題庫同步到發佈站（stdlib only）
=============================================================
cissp/bank/d1..d8.json → docs/cissp/bank/，並產生 quiz.js 需要的 index.json。
（題庫本身由 extract_questions.py 從 126 封電子報抽出。）

用法：python3 cissp/scripts/build_quiz_site.py
"""

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "cissp" / "bank"
OUT = ROOT / "docs" / "cissp" / "bank"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    practice, mocks, total = [], {}, 0
    for f in sorted(BANK.glob("*.json")):
        shutil.copy(str(f), str(OUT / f.name))
        qs = json.loads(f.read_text(encoding="utf-8"))
        total += len(qs)
        m = re.match(r"mock-(\d+)\.json", f.name)
        if m:
            mocks[str(int(m.group(1)))] = f.name
        else:
            practice.append(f.name)
    (OUT / "index.json").write_text(json.dumps(
        {"practice_files": practice, "mock_files": mocks},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已同步 {len(practice)} 個練習題庫檔（共 {total} 題）"
          f"{'、' + str(len(mocks)) + ' 份模擬考' if mocks else ''} → docs/cissp/bank/")


if __name__ == "__main__":
    main()
