#!/usr/bin/env python3
"""
extract_questions.py — 從 126 封 CISSP 電子報抽出考題成結構化題庫（stdlib only）
================================================================================
CISSP 專案的 475 道考題原本以 HTML 卡片內嵌在 emails/day-NNN.html 裡，
只能「讀」不能「練」。本腳本把它們解析成與 SC-200 相同的題庫 schema，
讓刷題 App 可以直接使用（篩選、隨機、計時模考、錯題本、統計）。

每張題卡的可解析特徵（126 封信格式一致）：
  - `QUESTION N` 眼眉
  - 英文題幹：font-weight:600 的 <p>
  - 中文翻譯：color:#5B6675 的 <p>，外包全形括號
  - 四個選項 <div>，**正解那個的背景色是 #FBF4E8**（另有 border-color:#64748B）
  - <details> 內：`正解：X` 與「為何其他選項錯」的 <li>A：…</li>

輸出 cissp/bank/d1.json … d8.json（依該封信所屬 Domain 歸檔）。

用法：python3 cissp/scripts/extract_questions.py [--dry-run]
"""

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMAILS = ROOT / "emails"
BANK = ROOT / "cissp" / "bank"

CORRECT_BG = "#FBF4E8"          # 正解選項的底色
OPTION_RE = re.compile(
    r'<div style="([^"]*?)"[^>]*>\s*<strong>([A-E])\.</strong>\s*(.*?)</div>', re.S)


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).replace(" ", " ").strip()


def split_bilingual(text):
    """『Due care 應盡注意』→ ('Due care', '應盡注意')；拆不開就整串當英文。"""
    m = re.match(r"^([^一-鿿]+?)\s*([一-鿿][\s\S]*)$", text)
    if m and len(m.group(1).strip()) >= 2:
        return m.group(1).strip(" ,;:"), m.group(2).strip()
    return text, ""


def parse_question(block, seq_in_email):
    """解析單張題卡；缺任何必要欄位就回 None（呼叫端會計為 skipped）。"""
    paras = re.findall(r'<p style="([^"]*)"[^>]*>(.*?)</p>', block, re.S)
    stem_en = stem_zh = ""
    for style, body in paras:
        txt = strip_tags(body)
        if not txt:
            continue
        if not stem_en and "font-weight:600" in style:
            stem_en = txt
        elif stem_en and not stem_zh and "#5B6675" in style:
            stem_zh = txt.strip("（）()")
    if not stem_en:
        return None

    options, correct_by_color = [], None
    for style, key, body in OPTION_RE.findall(block):
        txt = strip_tags(body)
        if not txt:
            continue
        en, zh = split_bilingual(txt)
        options.append({"key": key, "text_en": en, "text_zh": zh})
        if CORRECT_BG.lower() in style.lower():
            correct_by_color = key
    if len(options) < 4:
        return None

    m = re.search(r"正解[：:]\s*([A-E])", block)
    correct = m.group(1) if m else correct_by_color
    if not correct:
        return None
    # 底色與文字標示不一致時，以文字的「正解：X」為準（人寫的那個較可信）
    mismatch = bool(correct_by_color and m and correct_by_color != correct)

    expl = ""
    me = re.search(r"正解[：:]\s*[A-E]\s*</strong>(.*?)</p>", block, re.S)
    if me:
        expl = strip_tags(me.group(1)).lstrip("。.  ")
    if not expl:
        expl = f"正解為 {correct}。"

    why = {}
    for key, body in re.findall(r"<li[^>]*>\s*([A-E])[：:]\s*(.*?)</li>", block, re.S):
        if key != correct:
            why[key] = strip_tags(body)

    return {
        "stem_en": stem_en, "stem_zh": stem_zh, "options": options,
        "answer": [correct], "explanation_zh": expl, "why_wrong_zh": why,
        "_mismatch": mismatch, "_n": seq_in_email,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    curriculum = json.loads((ROOT / "cissp_curriculum.json").read_text(encoding="utf-8"))
    unit_by_seq = {u["seq"]: u for u in curriculum["units"]}

    buckets, stats = {}, Counter()
    mismatches, skipped = [], []

    for path in sorted(EMAILS.glob("day-*.html")):
        seq = int(path.stem.split("-")[1])
        unit = unit_by_seq.get(seq)
        if not unit:
            continue
        dom = unit["domain"]
        raw = path.read_text(encoding="utf-8")
        # 以 QUESTION 眼眉切開每張題卡
        parts = re.split(r'(?=<div[^>]*>\s*QUESTION\s+\d+[^<]*</div>)', raw)
        n_in_email = 0
        for part in parts:
            eyebrow = re.search(r">\s*QUESTION\s+(\d+)([^<]*)<", part)
            if not eyebrow:
                continue
            n_in_email += 1
            q = parse_question(part, n_in_email)
            if q is None:
                skipped.append(f"day-{seq:03d} Q{n_in_email}")
                continue
            if q.pop("_mismatch"):
                mismatches.append(f"day-{seq:03d} Q{q['_n']}")
            q.pop("_n")
            # 跨領域總複習的眼眉會標明該題屬於哪個 Domain，優先採用
            dm = re.search(r"D([1-8])", eyebrow.group(2) or "")
            dom = f"D{dm.group(1)}" if dm else unit["domain"]
            idx = len(buckets.setdefault(dom, [])) + 1
            q.update({
                "id": f"{dom}-{idx:04d}", "domain": dom,
                "topic": f"{dom.lower()}-{unit['phase'].lower()}",
                "unit": unit["code"], "set": "A",
                "difficulty": {"P1": 1, "P2": 2, "P3": 3}.get(unit["phase"], 2),
                "type": "single", "tags": [unit["phase"]],
                "source": f"emails/day-{seq:03d}.html",
                "unit_title_zh": unit["title_zh"],
            })
            buckets[dom].append(q)
            stats[dom] += 1

    total = sum(stats.values())
    print(f"抽出 {total} 題｜各領域 {dict(sorted(stats.items()))}")
    if mismatches:
        print(f"⚠️ 底色與『正解：X』不一致 {len(mismatches)} 題（採用文字標示）："
              f"{'、'.join(mismatches[:8])}{' …' if len(mismatches) > 8 else ''}")
    if skipped:
        print(f"⚠️ 無法解析 {len(skipped)} 題：{'、'.join(skipped[:8])}"
              f"{' …' if len(skipped) > 8 else ''}")

    if args.dry_run:
        print("（--dry-run，未寫檔）")
        return
    BANK.mkdir(parents=True, exist_ok=True)
    for dom, qs in sorted(buckets.items()):
        out = BANK / f"{dom.lower()}.json"
        out.write_text(json.dumps(qs, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ {out.relative_to(ROOT)}：{len(qs)} 題")
    if skipped:
        sys.exit(0)  # 有跳過的題目不算失敗，但上面已列出來供人工檢查


if __name__ == "__main__":
    main()
