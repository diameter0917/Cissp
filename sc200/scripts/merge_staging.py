#!/usr/bin/env python3
"""
merge_staging.py — 把 bank/_staging/*.json 併入正式題庫檔（stdlib only）
=======================================================================
內容代理批次會把各單元題目寫到 sc200/bank/_staging/unit-*.json，
本腳本依 id 前綴（D1-/D2-/D3-/M1-/M2-/M3-）把題目併入
d1.json / d2.json / d3.json / mock-0N.json，同 id 以 staging 版為準，
成功併入後刪除 staging 檔。

用法：python sc200/scripts/merge_staging.py
"""

import json
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1] / "bank"
STAGING = BANK / "_staging"
PREFIX_FILE = {"D1": "d1.json", "D2": "d2.json", "D3": "d3.json",
               "M1": "mock-01.json", "M2": "mock-02.json", "M3": "mock-03.json"}


def main():
    if not STAGING.exists():
        print("ℹ️ 無 _staging 目錄，跳過。")
        return
    staged = sorted(STAGING.glob("*.json"))
    if not staged:
        print("ℹ️ _staging 為空，跳過。")
        return

    buckets = {}
    bad = []
    for sp in staged:
        try:
            qs = json.loads(sp.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            bad.append(f"{sp.name}: JSON 解析失敗 {e}")
            continue
        for q in qs:
            prefix = str(q.get("id", ""))[:2]
            fname = PREFIX_FILE.get(prefix)
            if not fname:
                bad.append(f"{sp.name}: 未知 id 前綴 {q.get('id')}")
                continue
            buckets.setdefault(fname, {})[q["id"]] = q

    if bad:
        for b in bad:
            print(f"✗ {b}")
        sys.exit(1)

    for fname, new_qs in sorted(buckets.items()):
        target = BANK / fname
        existing = {}
        if target.exists():
            for q in json.loads(target.read_text(encoding="utf-8")):
                existing[q["id"]] = q
        replaced = sum(1 for k in new_qs if k in existing)
        existing.update(new_qs)
        merged = sorted(existing.values(), key=lambda q: q["id"])
        target.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ {fname}: +{len(new_qs) - replaced} 新題、{replaced} 覆蓋 → 共 {len(merged)} 題")

    for sp in staged:
        sp.unlink()
    print(f"已清空 _staging（{len(staged)} 檔）")


if __name__ == "__main__":
    main()
