#!/usr/bin/env python3
"""
build_site.py — SC-200 站台組建（stdlib only）
===============================================
sc200/content/day-NNN.html（電子報本文片段）＋ sc200/drill/day-NNN.html（刷題日片段）
→ 套用 sc200/templates/*.html → 輸出 docs/sc200/newsletter|drill/day-NNN.html

同時：
  - 自我檢測 5 題由 sc200/bank/ 以 unit 標籤注入（單一事實來源）
  - 影片框由 curriculum 的 video_eps ＋ transcripts/index.json（標題）生成
  - Podcast 框：音檔存在 → <audio>；不存在 → 「生成中」占位
  - 複製 bank/*.json → docs/sc200/bank/ 並產生 index.json（quiz.js 讀取）

用法：python sc200/scripts/build_site.py [--check] [--strict]
      --check：組建後執行內容驗證（章節數、KQL、字數、自測題覆蓋、placeholder 殘留）
      --strict：內容分批產製期間的「尚未補齊」類警告（自測題 <5）升級為錯誤，
                供 M9 收尾全量驗證使用；CI 平時只跑 --check。
"""

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

SC200 = Path(__file__).resolve().parents[1]
ROOT = SC200.parent
DOCS = ROOT / "docs" / "sc200"

DOMAIN_CLASS = {"D1": "d1", "D2": "d2", "D3": "d3", "MIX": "mix"}

problems = []
notes = []


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def zh_char_count(html):
    text = re.sub(r"<[^>]+>", "", html)
    return len(re.findall(r"[一-鿿]", text))


def ep_titles():
    """EP → 標題（優先 transcripts/index.json，其次 curriculum）。"""
    titles = {}
    idx_path = SC200 / "transcripts" / "index.json"
    if idx_path.exists():
        for e in load(idx_path).get("episodes", []):
            if e.get("title"):
                titles[e["ep"]] = e["title"]
    return titles


def fmt_ts(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def video_block(unit, curriculum, titles):
    eps = unit.get("video_eps") or []
    if not eps:
        return ""
    series = curriculum["video_resources"]["ep_series"]
    rows = []
    for ep in eps:
        info = series.get(ep, {})
        title = titles.get(ep) or info.get("title") or "官方影片（標題待補）"
        url = info.get("url", "#")
        segs = [s for s in (unit.get("video_segments") or []) if s.get("ep") == ep]
        seg_html = ""
        if segs:
            seg_html = "<div class='vm'>本日對應段落：" + "、".join(
                # youtu.be 短網址沒有既有查詢字串，時間碼要用 ?t= 起頭（&t= 會壞掉）
                f"<a href='{url}?t={int(s['start'])}' target='_blank' rel='noopener'>"
                f"<span class='timestamp'>{fmt_ts(s['start'])}</span></a> {s.get('title','')}"
                for s in segs) + "</div>"
        rows.append(
            f"<div class='video-box'><div class='vicon'>📺</div><div>"
            f"<div class='vt'>{ep}｜{title}</div>"
            f"<div class='vm'>本單元以這支官方影片為主軸，建議先看影片再讀伴讀整理。</div>"
            f"{seg_html}"
            f"<a class='vbtn' href='{url}' target='_blank' rel='noopener'>觀看影片 ↗</a>"
            f"</div></div>")
    return "\n".join(rows)


def selftest_block(code, bank_by_unit):
    qs = bank_by_unit.get(code, [])[:5]
    if not qs:
        return ("<div class='info-box'>本單元自測題建置中——先到"
                "<a href='../quiz.html'>刷題頁</a>練其他題組。</div>")
    cards = []
    for i, q in enumerate(qs, 1):
        opts = "".join(
            f"<div class='q-opt'><strong>{o['key']}.</strong> {o['text_en']}"
            f"<div style='font-size:12.5px;color:var(--muted)'>{o['text_zh']}</div></div>"
            for o in q["options"])
        why = "".join(f"<li><strong>{k}</strong>：{v}</li>"
                      for k, v in (q.get("why_wrong_zh") or {}).items())
        cards.append(
            f"<div class='q-card'><div class='q-eyebrow'>QUESTION {i} · {q['id']}</div>"
            f"<div class='q-stem'>{q['stem_en']}</div>"
            f"<div class='q-zh'>（{q['stem_zh']}）</div>"
            f"{opts}"
            f"<details><summary>看正解與解析</summary><div class='q-ans'>"
            f"<span class='correct'>正解：{'、'.join(q['answer'])}</span>"
            f"<p>{q['explanation_zh']}</p><ul>{why}</ul>"
            f"<p style='font-size:12.5px'><a href='{q['ms_learn_ref']}' target='_blank' rel='noopener'>📚 MS Learn 參考 ↗</a></p>"
            f"</div></details></div>")
    return "\n".join(cards)


def podcast_block(episode):
    mp3 = DOCS / "podcast" / f"ep-{episode:03d}.mp3"
    inner = (f"<audio controls preload='none' src='../podcast/ep-{episode:03d}.mp3'></audio>"
             if mp3.exists() else
             "<div class='p-hint'>🎧 本集音檔生成中（push 腳本後由 GitHub Actions 自動合成）。</div>")
    return (f"<div class='podcast-box'><div class='p-label'>SC-200 速成電台 · EP{episode}</div>"
            f"<div class='p-title'>用聽的複習今天的內容（雙主持人對談）</div>"
            f"{inner}"
            f"<div class='p-hint'>逐字稿與全部集數：<a href='../podcast/index.html#ep-{episode:03d}'>Podcast 節目頁 ↗</a>"
            f"｜可用 Podcast App 訂閱 <a href='../podcast.xml'>RSS</a></div></div>")


def cta_block(unit):
    spec = unit.get("quiz_spec")
    if not spec:
        return ""
    label = {"domain": "開始題組", "random": "開始混合測驗", "mock": "進入模擬考",
             "wrong": "打開錯題本", "stats": "看學習統計"}.get(spec.get("mode"), "開始練習")
    params = {k: v for k, v in spec.items() if k != "then"}
    url = f"../quiz.html?{urlencode(params)}"
    html = (f"<div class='card-block' style='text-align:center'>"
            f"<a class='vbtn' style='font-size:15px;padding:10px 26px;display:inline-block;"
            f"background:var(--accent);color:#fff;text-decoration:none;border-radius:10px;font-weight:700' "
            f"href='{url}'>✏️ {label} →</a></div>")
    if spec.get("then") == "wrong":
        html += ("<div class='card-block' style='text-align:center'>"
                 "<a class='vbtn' style='display:inline-block;background:var(--warning);color:#fff;"
                 "text-decoration:none;padding:8px 20px;border-radius:10px;font-weight:700' "
                 "href='../quiz.html?mode=wrong'>📕 接著清錯題本 →</a></div>")
    return html


def pager_link(item, direction):
    if item is None:
        return f"<a class='disabled'>{'← 沒有上一天' if direction == 'prev' else '沒有下一天 →'}</a>"
    sub = "newsletter" if item["type"] == "study" else "drill"
    label = f"← Day {item['seq']}" if direction == "prev" else f"Day {item['seq']} →"
    return f"<a href='../{sub}/day-{item['seq']:03d}.html'>{label}</a>"


def render(template, mapping):
    out = template
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def check_fragment(name, body, unit, bank_by_unit, strict=False):
    tocs = len(re.findall(r"<h2[^>]*data-toc", body))
    if tocs < 3:
        problems.append(f"{name}: data-toc 章節僅 {tocs} 個（需 ≥3）")
    if unit.get("kql_focus") and "pre class=\"kql\"" not in body and "pre class='kql'" not in body:
        problems.append(f"{name}: kql_focus 單元缺 KQL 程式碼區塊")
    n = zh_char_count(body)
    if not (2600 <= n <= 4600):
        notes.append(f"{name}: 繁中字數 {n}（目標 3000-4000）")
    got = len(bank_by_unit.get(unit["code"], []))
    if got < 5:
        msg = f"{name}: 單元自測題 {got}/5（bank 中 unit={unit['code']}）"
        (problems if strict else notes).append(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="「尚未補齊」類警告升級為錯誤（收尾全量驗證用）")
    args = ap.parse_args()
    if args.strict:
        args.check = True

    curriculum = load(SC200 / "sc200_curriculum.json")
    schedule = load(SC200 / "schedule.json")
    config = load(SC200 / "site_config.json")
    sched_by_seq = {it["seq"]: it for it in schedule["items"]}
    domains = {d["id"]: d for d in curriculum["domains"]}
    exam = date.fromisoformat(config["exam_date"])
    titles = ep_titles()

    # ---- bank → docs/sc200/bank/ ＋ index.json ----
    bank_dir = SC200 / "bank"
    out_bank = DOCS / "bank"
    out_bank.mkdir(parents=True, exist_ok=True)
    practice_files, mock_files = [], {}
    bank_by_unit = {}
    if bank_dir.exists():
        for f in sorted(bank_dir.glob("*.json")):
            shutil.copy(str(f), str(out_bank / f.name))
            m = re.match(r"mock-(\d+)\.json", f.name)
            if m:
                mock_files[str(int(m.group(1)))] = f.name
            else:
                practice_files.append(f.name)
                for q in load(f):
                    if q.get("unit"):
                        bank_by_unit.setdefault(q["unit"], []).append(q)
    (out_bank / "index.json").write_text(json.dumps(
        {"practice_files": practice_files, "mock_files": mock_files},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- 逐單元組頁 ----
    tpl_news = (SC200 / "templates" / "newsletter.html").read_text(encoding="utf-8")
    tpl_drill = (SC200 / "templates" / "drill.html").read_text(encoding="utf-8")
    units = sorted(curriculum["units"], key=lambda u: u["seq"])
    built = skipped = 0

    for i, unit in enumerate(units):
        seq = unit["seq"]
        it = sched_by_seq[seq]
        is_study = unit["type"] == "study"
        src = SC200 / ("content" if is_study else "drill") / f"day-{seq:03d}.html"
        if not src.exists():
            skipped += 1
            continue
        body = src.read_text(encoding="utf-8")

        prev_it = sched_by_seq.get(seq - 1)
        next_it = sched_by_seq.get(seq + 1)
        # 只連到已有片段的頁
        def has_page(x):
            if x is None:
                return False
            sub = "content" if x["type"] == "study" else "drill"
            return (SC200 / sub / f"day-{x['seq']:03d}.html").exists()
        prev_link = pager_link(prev_it if has_page(prev_it) else None, "prev")
        next_link = pager_link(next_it if has_page(next_it) else None, "next")

        days_to_exam = (exam - date.fromisoformat(it["date"])).days
        dom = domains[unit["domain"]]
        common = {
            "SEQ": seq, "CODE": unit["code"], "DATE": it["date"],
            "TITLE_ZH": unit["title_zh"], "TITLE_EN": unit.get("title_en", ""),
            "DOMAIN": unit["domain"], "DOMAIN_NAME_ZH": dom["name_zh"],
            "DOMAIN_CLASS": DOMAIN_CLASS[unit["domain"]],
            "DOMAIN_LABEL": (unit["domain"] + " " + dom["name_zh"]) if unit["domain"] != "MIX" else "跨領域綜合",
            "WEIGHT": dom["weight"], "EXAM_DATE": config["exam_date"],
            "DAYS_TO_EXAM": days_to_exam,
            "PROGRESS_PCT": round(seq / len(units) * 100),
            "PREV_LINK": prev_link, "NEXT_LINK": next_link,
            "BODY": body,
        }

        if is_study:
            common["PROGRESS_PCT"] = round(seq / 25 * 100)
            eyebrows = len(re.findall(r"class=[\"']eyebrow[\"']", body))
            common.update({
                "SELFTEST_NO": f"{eyebrows + 1:02d}",
                "VIDEO_BLOCK": video_block(unit, curriculum, titles),
                "SELFTEST_BLOCK": selftest_block(unit["code"], bank_by_unit),
                "PODCAST_BLOCK": podcast_block(it["episode"]),
            })
            out = DOCS / "newsletter" / f"day-{seq:03d}.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(tpl_news, common), encoding="utf-8")
        else:
            common["CTA_BLOCK"] = cta_block(unit)
            out = DOCS / "drill" / f"day-{seq:03d}.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(tpl_drill, common), encoding="utf-8")
        built += 1

        if args.check:
            leftovers = re.findall(r"\{\{[A-Z_]+\}\}", (out.read_text(encoding="utf-8")))
            if leftovers:
                problems.append(f"{out.name}: 未替換的 placeholder {sorted(set(leftovers))}")
            if is_study:
                check_fragment(f"content/day-{seq:03d}.html", body, unit,
                               bank_by_unit, strict=args.strict)

    print(f"✅ 組建完成：{built} 頁（尚無片段 {skipped} 天）")
    if args.check:
        for n in notes:
            print(f"⚠️  {n}")
        for p in problems:
            print(f"✗ {p}")
        if problems:
            print(f"\n✗ --check 失敗：{len(problems)} 個問題")
            sys.exit(1)
        print("✅ --check 通過")


if __name__ == "__main__":
    main()
