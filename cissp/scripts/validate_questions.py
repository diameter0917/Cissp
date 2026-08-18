#!/usr/bin/env python3
"""
validate_questions.py — CISSP 題庫檢查（stdlib only）
=====================================================
題庫由 extract_questions.py 從 126 封既有電子報抽出，因此這裡的檢查
重點與 SC-200 不同：SC-200 的題目是新寫的，可以要求它符合規格；
CISSP 的題目是既有教材，驗證器的職責是「確認抽取沒有失真」，
而非改寫作者原本的內容。

錯誤（exit 1）＝抽取失真的徵兆：
  - 缺必要欄位、選項不足 4 個、正解不在選項中、id 重複
  - 中英文題幹皆空

警告（不影響 exit code）＝原始教材本身的性質，不宜靜默修改：
  - 答案字母分布偏斜（改正需重排選項，但解說內文寫著「正解：X」、
    錯項解析也以字母為鍵，重排會讓解說對不上）
  - 部分錯誤選項沒有解析（原信只解釋了其中幾個）

用法：python3 cissp/scripts/validate_questions.py [--strict]
      --strict：把警告一併視為錯誤
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

BANK = Path(__file__).resolve().parents[1] / "bank"
REQUIRED = ["id", "domain", "topic", "unit", "difficulty", "type",
            "stem_en", "options", "answer", "explanation_zh"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    files = sorted(BANK.glob("*.json"))
    if not files:
        print("ℹ️ cissp/bank/ 尚無題庫檔——先跑 extract_questions.py。")
        return

    errors, warnings = [], []
    seen_ids = Counter()
    letters = Counter()
    by_domain = Counter()
    by_phase = Counter()
    total = 0
    partial_why = 0

    for path in files:
        try:
            qs = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}: JSON 解析失敗 {e}")
            continue
        file_letters = Counter()
        for q in qs:
            total += 1
            qid = q.get("id", "<no-id>")
            seen_ids[qid] += 1
            for f in REQUIRED:
                if f not in q or q[f] in (None, "", []):
                    errors.append(f"{path.name} {qid}: 缺欄位 {f}")
            if not q.get("stem_en") and not q.get("stem_zh"):
                errors.append(f"{path.name} {qid}: 中英文題幹皆空")
            keys = [o.get("key") for o in q.get("options", [])]
            if len(keys) != 4:
                errors.append(f"{path.name} {qid}: 選項 {len(keys)} 個（應為 4）")
            if len(keys) != len(set(keys)):
                errors.append(f"{path.name} {qid}: 選項鍵重複")
            for a in q.get("answer", []):
                if a not in keys:
                    errors.append(f"{path.name} {qid}: 正解 {a} 不在選項中")
            if q.get("answer"):
                letters[q["answer"][0]] += 1
                file_letters[q["answer"][0]] += 1
            wrong = [k for k in keys if k not in q.get("answer", [])]
            if any(k not in q.get("why_wrong_zh", {}) for k in wrong):
                partial_why += 1
            by_domain[q.get("domain")] += 1
            by_phase[(q.get("tags") or ["?"])[0]] += 1

        n = sum(file_letters.values())
        if n >= 25:
            for letter, cnt in file_letters.items():
                if cnt / n > 0.32:
                    warnings.append(
                        f"{path.name}: 答案字母 {letter} 占 {cnt/n:.0%}（>32%；"
                        f"源自原始教材，改正需重排選項並改寫解說中的字母引用）")

    for qid, n in seen_ids.items():
        if n > 1:
            errors.append(f"id 重複：{qid} 出現 {n} 次")
    if partial_why:
        warnings.append(f"{partial_why} 題的錯誤選項解析不完整（原信只解釋了部分選項）")

    print("── CISSP 題庫統計 ──")
    print(f"總題數 {total}｜各領域 {dict(sorted(by_domain.items()))}")
    print(f"依階段 {dict(sorted(by_phase.items()))}｜"
          f"答案字母 {dict(sorted((k, f'{v/total:.0%}') for k, v in letters.items()))}")

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors[:20]:
        print(f"✗ {e}")
    if len(errors) > 20:
        print(f"✗ …另有 {len(errors)-20} 個錯誤")

    if errors or (args.strict and warnings):
        print(f"\n✗ 驗證失敗：{len(errors)} 個錯誤、{len(warnings)} 個警告")
        sys.exit(1)
    print(f"\n✅ 驗證通過（{len(warnings)} 個警告）")


if __name__ == "__main__":
    main()
