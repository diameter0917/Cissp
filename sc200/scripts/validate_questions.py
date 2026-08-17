#!/usr/bin/env python3
"""
validate_questions.py — SC-200 題庫品質門檻（stdlib only）
==========================================================
檢查 sc200/bank/*.json：

  永遠是錯誤（exit 1）：
    - schema 不完整（缺欄位、選項鍵重複、answer 不在選項中、
      why_wrong_zh 未涵蓋所有錯誤選項、single 題不是恰好 4 個選項）
    - id 重複、id 前綴與檔案/領域不符
    - ms_learn_ref 非 https://learn.microsoft.com/ 開頭
    - 題幹近重複（difflib ratio > 0.85）
    - 單選題答案字母分布：任一字母 > 32%（防 LLM 選項偏誤；該檔 ≥ 25 題才檢查）

  預設為警告、--strict 時升級為錯誤（供收尾階段全量驗證）：
    - 每個學習單元（seq 1-25 的 code）unit 標籤題數 < 5
    - 檔案題數未達標（d1=180、d2=150、d3=90、mock=55）
    - 2026 新考點題數占比 < 10%

用法：python sc200/scripts/validate_questions.py [--strict]
"""

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

SC200 = Path(__file__).resolve().parents[1]
BANK = SC200 / "bank"

TARGETS = {"d1.json": ("D1", 180), "d2.json": ("D2", 150), "d3.json": ("D3", 90),
           "mock-01.json": ("M1", 55), "mock-02.json": ("M2", 55), "mock-03.json": ("M3", 55)}
REQUIRED = ["id", "domain", "topic", "difficulty", "type", "stem_en", "stem_zh",
            "options", "answer", "explanation_zh", "why_wrong_zh", "ms_learn_ref"]

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def norm_stem(s):
    return re.sub(r"[^a-z0-9一-鿿]+", "", (s or "").lower())


def check_question(fname, q, id_prefix):
    qid = q.get("id", "<no-id>")
    ctx = f"{fname} {qid}"
    for f in REQUIRED:
        if f not in q or q[f] in (None, "", []):
            err(f"{ctx}: 缺少欄位 {f}")
            return
    if not str(qid).startswith(id_prefix + "-"):
        err(f"{ctx}: id 前綴應為 {id_prefix}-")
    if q["domain"] not in ("D1", "D2", "D3"):
        err(f"{ctx}: domain 無效 {q['domain']}")
    if q["type"] not in ("single", "multi"):
        err(f"{ctx}: type 應為 single|multi")
    if q["difficulty"] not in (1, 2, 3):
        err(f"{ctx}: difficulty 應為 1-3")

    keys = [o.get("key") for o in q["options"]]
    if len(keys) != len(set(keys)):
        err(f"{ctx}: 選項鍵重複")
    for o in q["options"]:
        if not o.get("text_en") or not o.get("text_zh"):
            err(f"{ctx}: 選項 {o.get('key')} 缺英文或中文")
    if q["type"] == "single" and len(keys) != 4:
        err(f"{ctx}: 單選題應恰好 4 個選項")
    if q["type"] == "multi" and len(q["answer"]) < 2:
        err(f"{ctx}: multi 題 answer 應 ≥ 2")
    if q["type"] == "single" and len(q["answer"]) != 1:
        err(f"{ctx}: single 題 answer 應恰好 1 個")
    for a in q["answer"]:
        if a not in keys:
            err(f"{ctx}: answer {a} 不在選項中")
    wrong_keys = [k for k in keys if k not in q["answer"]]
    for k in wrong_keys:
        if k not in q["why_wrong_zh"] or not q["why_wrong_zh"][k]:
            err(f"{ctx}: why_wrong_zh 缺少選項 {k} 的解析")
    for k in q["why_wrong_zh"]:
        if k in q["answer"]:
            err(f"{ctx}: why_wrong_zh 不應包含正解 {k}")
    if not str(q["ms_learn_ref"]).startswith("https://learn.microsoft.com/"):
        err(f"{ctx}: ms_learn_ref 應為 learn.microsoft.com 連結")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="數量/占比警告升級為錯誤")
    args = ap.parse_args()

    files = sorted(BANK.glob("*.json")) if BANK.exists() else []
    if not files:
        print("ℹ️ sc200/bank/ 尚無題庫檔，略過驗證。")
        return

    all_q = []
    all_ids = Counter()
    for path in files:
        fname = path.name
        try:
            qs = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(f"{fname}: JSON 解析失敗 {e}")
            continue
        if not isinstance(qs, list):
            err(f"{fname}: 應為題目陣列")
            continue
        id_prefix, target = TARGETS.get(fname, (None, None))
        if id_prefix is None:
            warn(f"{fname}: 非預期的題庫檔名")
            id_prefix = ""
        for q in qs:
            check_question(fname, q, id_prefix)
            all_ids[q.get("id")] += 1
            q["_file"] = fname
            all_q.append(q)

        # 答案字母分布（單選、≥25 題才檢查）
        singles = [q for q in qs if q.get("type") == "single" and q.get("answer")]
        if len(singles) >= 25:
            dist = Counter(q["answer"][0] for q in singles)
            for letter, n in dist.items():
                pct = n / len(singles)
                if pct > 0.32:
                    err(f"{fname}: 答案字母 {letter} 占 {pct:.0%}（>32%，防偏誤門檻）")

        if target and len(qs) != target:
            msg = f"{fname}: 題數 {len(qs)}／目標 {target}"
            (err if args.strict else warn)(msg)

    for qid, n in all_ids.items():
        if n > 1:
            err(f"id 重複：{qid} 出現 {n} 次")

    # 近重複題幹（quick_ratio 預篩 + ratio 精查）
    stems = [(q.get("id"), norm_stem(q.get("stem_en", ""))) for q in all_q if q.get("stem_en")]
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            a, b = stems[i][1], stems[j][1]
            if not a or not b or abs(len(a) - len(b)) > max(len(a), len(b)) * 0.2:
                continue
            sm = difflib.SequenceMatcher(None, a, b)
            if sm.quick_ratio() > 0.85 and sm.ratio() > 0.85:
                err(f"題幹近重複：{stems[i][0]} ↔ {stems[j][0]}")

    # 單元自測覆蓋（seq 1-25）
    curriculum = json.loads((SC200 / "sc200_curriculum.json").read_text(encoding="utf-8"))
    study_codes = [u["code"] for u in curriculum["units"] if u["type"] == "study"]
    unit_counts = Counter(q.get("unit") for q in all_q if q.get("unit"))
    for code in study_codes:
        if unit_counts.get(code, 0) < 5:
            msg = f"單元 {code}: unit 標籤題數 {unit_counts.get(code, 0)}／需 ≥5"
            (err if args.strict else warn)(msg)

    # 2026 新考點占比
    practice = [q for q in all_q if q["_file"].startswith("d")]
    if practice:
        n2026 = sum(1 for q in practice if "2026" in (q.get("tags") or []))
        if n2026 / len(practice) < 0.10:
            msg = f"2026 新考點題占比 {n2026}/{len(practice)}（<10%）"
            (err if args.strict else warn)(msg)

    # 統計報告
    print("── 題庫統計 ──")
    by_dom = Counter(q["domain"] for q in all_q if q.get("domain"))
    by_diff = Counter(q.get("difficulty") for q in all_q)
    print(f"總題數 {len(all_q)}｜領域 {dict(sorted(by_dom.items()))}｜難度 {dict(sorted(by_diff.items(), key=lambda x: str(x[0])))}")
    top_topics = Counter(f"{q.get('domain')}/{q.get('topic')}" for q in all_q).most_common(10)
    print("主題前十：", ", ".join(f"{t}×{n}" for t, n in top_topics))

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"✗ {e}")
    if errors:
        print(f"\n✗ 驗證失敗：{len(errors)} 個錯誤、{len(warnings)} 個警告")
        sys.exit(1)
    print(f"\n✅ 驗證通過（{len(warnings)} 個警告）")


if __name__ == "__main__":
    main()
