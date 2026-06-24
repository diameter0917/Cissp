#!/usr/bin/env python3
"""
match_videos.py
===============
為每個課綱單元配對「最相符的影片」，產出 video_map.json：
  - primary : 與本單元主題最相符的 mindmap 短片（信中第一個連結、用於對齊）
  - course  : 該 Domain 的完整課程影片（第二連結，apply_video_timestamps 會補 ?t=）
  - practice: 該 Domain 的考題影片（僅 P3 使用，刷題）

配對方法（不連 YouTube，只用 video_index.json 標題 + transcripts 內容）：
  - 由 unit.title_en + 課程主題詞典萃取英文關鍵字。
  - 候選＝同 Domain 的 mindmap；計分：關鍵字命中「標題」權重高、命中「字幕內容」權重低。
  - 取最高分；低於門檻則退回該 Domain 的「Review / Mind Map」綜述短片，再退回 course。
  - course 一律為該 Domain 完整影片；practice 取該 Domain 考題片中與主題最相符者。

用法：python scripts/match_videos.py  → 產生 video_map.json（供 build_schedule.py 讀）
可重跑。
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CUR = json.loads((ROOT / "cissp_curriculum.json").read_text(encoding="utf-8"))
VIDX = json.loads((ROOT / "video_index.json").read_text(encoding="utf-8"))
TRANS = ROOT / "transcripts"

STOP = {"domain", "big", "picture", "overview", "the", "and", "of", "in", "to", "a", "an",
        "deep", "dive", "exam", "amp", "vs", "or", "for", "with", "review", "mindmap",
        "mind", "map", "cissp", "1", "2", "3", "4", "5", "6", "7", "8", "9"}

# 每單元的補充主題關鍵字（讓配對更精準；key=code）。只填需要加強者。
TOPIC = {
    "P1-D1-1": ["cia", "triad"],
    "P1-D1-5": ["business continuity", "supply chain"],
    "P2-D1-1": ["alignment", "governance", "frameworks"],
    "P2-D1-2": ["risk management", "risk"],
    "P2-D1-3": ["risk management", "controls"],
    "P2-D1-4": ["privacy", "intellectual property"],
    "P2-D1-5": ["risk management", "business continuity"],
    "P3-D1-1": ["alignment", "ethics"],
    "P3-D1-2": ["risk management"],
    "P3-D1-3": ["risk management", "controls"],
    "P3-D1-4": ["privacy", "intellectual property"],
    "P3-D1-5": ["risk management", "business continuity"],
    # D2 — 只有 3 支 mindmap，角色/隱私相關導向 Privacy 那支
    "P1-D2-2": ["privacy"],
    "P1-D2-5": ["privacy"],
    "P3-D2-4": ["privacy"],
    # D5
    "P1-D5-3": ["single sign", "federated", "federation"],
    "P1-D5-4": ["single sign", "federated", "federation"],
    "P2-D5-3": ["single sign", "federated"],
    "P2-D5-4": ["single sign", "federated", "kerberos"],
    "P3-D5-3": ["single sign", "federated"],
    # D7 BCP/DR/IR
    "P1-D7-5": ["incident response", "recovery strategies", "business continuity"],
    "P2-D7-5": ["recovery strategies", "business continuity"],
    "P3-D7-1": ["incident response"],
    "P3-D7-3": ["recovery strategies", "business continuity"],
}

# 一些中文焦點 → 英文關鍵字補強（用 focus_zh 偵測）
ZH_HINT = [
    ("CIA", ["cia", "triad"]), ("治理", ["alignment", "governance"]),
    ("風險", ["risk management", "risk"]), ("智財", ["intellectual property"]),
    ("隱私", ["privacy"]), ("倫理", ["ethics"]), ("BCP", ["business continuity"]),
    ("供應鏈", ["supply chain"]), ("分類", ["classification"]), ("生命週期", ["lifecycle"]),
    ("密碼學", ["cryptography"]), ("簽章", ["digital signatures", "certificates"]),
    ("模型", ["models", "frameworks"]), ("雲", ["cloud"]), ("實體", ["physical security"]),
    ("OSI", ["osi model"]), ("協定", ["networking", "protocols"]), ("防火牆", ["network defense"]),
    ("無線", ["remote access", "wireless"]), ("郵件", ["network"]),
    ("存取控制", ["access control"]), ("鑑別", ["access control", "authentication"]),
    ("聯合", ["single sign", "federated"]), ("SSO", ["single sign", "federated"]),
    ("評估", ["security assessment", "testing"]), ("弱點", ["vulnerability assessment"]),
    ("滲透", ["vulnerability assessment", "penetration"]), ("日誌", ["log review", "logging"]),
    ("稽核", ["security assessment"]), ("調查", ["investigations"]), ("鑑識", ["investigations"]),
    ("事件", ["incident response"]), ("惡意", ["malware"]), ("修補", ["patching", "change management"]),
    ("變更", ["patching", "change management"]), ("復原", ["recovery strategies"]),
    ("災難", ["recovery strategies", "business continuity"]),
    ("SDLC", ["secure software development"]), ("開發", ["secure software development"]),
    ("OWASP", ["secure software development"]), ("注入", ["secure software development"]),
    ("DevSecOps", ["secure software development"]), ("CI/CD", ["secure software development"]),
    ("軟體", ["secure software development"]), ("外購", ["secure software development"]),
    ("測試與開源", ["secure software development"]),
    ("SAST", ["secure software development"]), ("DAST", ["secure software development"]),
    ("資料庫", ["databases"]), ("惡意程式", ["malware"]),
    ("SIEM", ["incident response", "investigations"]),
    ("監控", ["investigations", "incident response"]),
    ("威脅情報", ["investigations", "incident response"]),
    ("數位鑑識", ["investigations"]), ("證據", ["investigations"]),
    ("特權", ["incident response"]), ("偵測", ["incident response", "malware"]),
]


def kw_from_title(title):
    toks = [t for t in re.split(r"[\s,/&()|]+", title.lower()) if t and t not in STOP and len(t) > 1]
    return toks


def unit_keywords(u):
    """回傳 {keyword: weight}。標題（當日主題）權重高，focus 列舉的子主題權重低。"""
    kws = {}
    def add(k, w):
        kws[k] = max(kws.get(k, 0), w)
    for k in kw_from_title(u["title_en"]):   # 英文標題＝當日主題
        add(k, 20)
    for k in TOPIC.get(u["code"], []):       # 精選覆蓋
        add(k, 20)
    tz = u.get("title_zh", "")
    fz = u.get("focus_zh", "")
    for hint, ks in ZH_HINT:
        if hint in tz:                       # 中文標題命中＝主題，高權重
            for k in ks:
                add(k, 20)
        elif hint in fz:                     # 只在 focus 出現＝子主題，低權重
            for k in ks:
                add(k, 8)
    return kws


def transcript_text(vid):
    f = TRANS / f"{vid}.txt"
    return f.read_text(encoding="utf-8", errors="ignore").lower() if f.exists() else ""


def is_review_overview(title):
    # 「Domain N Review / Mind Map」綜述（無特定子主題）當作 fallback
    return bool(re.search(r"review\s*[/|]\s*mind\s*map", title.lower())) and "|" not in title.split("Map")[-1]


def score_candidate(kws, cand):
    """標題為主訊號（命中關鍵字依權重加分），字幕只當微弱 tiebreak（上限 < 1）。"""
    title = cand["title"].lower()
    tscore = sum(w for k, w in kws.items() if k in title)
    txt = transcript_text(cand["id"])
    cscore = 0.0
    if txt:
        L = max(len(txt), 1)
        for k in kws:
            c = txt.count(k)
            if c:
                cscore += min(c, 5) * (300.0 / L)
        cscore = min(cscore, 0.9)   # 永遠不超過一個標題命中，避免長片用內容洗版
    return tscore + cscore


def pick_primary(u, mindmaps):
    cands = [m for m in mindmaps if m["domain"] == u["domain"]]
    if not cands:
        return None
    kws = unit_keywords(u)
    scored = sorted(cands, key=lambda c: -score_candidate(kws, c))
    best = scored[0]
    if score_candidate(kws, best) < 2:
        # 太低 → 退回該 Domain 綜述短片
        ov = [c for c in cands if "review" in c["title"].lower()]
        return ov[0] if ov else best
    return best


def pick_practice(u, practices):
    cands = [p for p in practices if p["domain"] == u["domain"]]
    if not cands:
        return None
    kws = unit_keywords(u)
    return sorted(cands, key=lambda c: -score_candidate(kws, c))[0]


def main():
    videos = VIDX["videos"]
    mindmaps = [v for v in videos if v["category"] == "mindmap"]
    practices = [v for v in videos if v["category"] == "practice"]
    course_by_dom = {v["domain"]: v for v in videos if v["category"] == "course"}

    out = {}
    for u in sorted(CUR["units"], key=lambda x: x["seq"]):
        prim = pick_primary(u, mindmaps)
        course = course_by_dom.get(u["domain"])
        entry = {
            "primary": _slim(prim),
            "course": _slim(course),
        }
        if u["phase"] == "P3":
            entry["practice"] = _slim(pick_practice(u, practices))
        out[u["code"]] = entry

    (ROOT / "video_map.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已產生 video_map.json（{len(out)} 單元）")


def _slim(v):
    if not v:
        return None
    return {"id": v["id"], "title": v["title"], "url": v["url"], "category": v["category"]}


if __name__ == "__main__":
    main()
