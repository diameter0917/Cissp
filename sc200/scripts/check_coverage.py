#!/usr/bin/env python3
"""
check_coverage.py — 字幕 × 教材覆蓋度比對（stdlib only）
=========================================================
字幕抓回來之後（sc200/transcripts/ep-NN.*.txt），逐單元比對三份材料講了什麼：

    影片字幕  →  電子報（sc200/content/day-NNN.html）
              →  Podcast 腳本（sc200/podcast/scripts/ep-NNN.json）

產出 sc200/coverage_report.md，回答三個問題：
  1. 【要補教材】影片講了、電子報沒寫的主題 → 該寫進核心章節
  2. 【要補音檔】電子報寫了、Podcast 沒講的主題 → 該加進對談
  3. 【自主補強】電子報寫了、影片沒講的主題 → 確認它在「考綱補洞」章節（這是刻意的）

比對方式：
  - 內建 SC-200 術語詞典（產品/功能/KQL 運算子），涵蓋考綱主要名詞；
    英文術語在三份材料中都會出現（電子報是中英並列、Podcast 直接唸英文），故可直接比對。
  - 另外自動挖掘字幕中高頻的「大寫多詞片語」，找出詞典沒收錄、但影片明顯著墨的新主題
    （例如產品改名或新功能），列為待人工判斷項。

用法：
  python3 sc200/scripts/check_coverage.py              # 全部單元
  python3 sc200/scripts/check_coverage.py 7 8 9        # 只看指定 seq
  python3 sc200/scripts/check_coverage.py --min 2      # 只列在字幕中出現 ≥2 次的主題（預設 2）
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

SC200 = Path(__file__).resolve().parents[1]
TRANSCRIPTS = SC200 / "transcripts"
CONTENT = SC200 / "content"
SCRIPTS = SC200 / "podcast" / "scripts"
REPORT = SC200 / "coverage_report.md"

# ── SC-200 術語詞典：canonical → 在文字中可能出現的寫法 ────────────────────
# canonical 用於報告顯示；aliases 全部小寫比對。
TERMS = {
    # D1 環境
    "Log Analytics workspace": ["log analytics workspace", "工作區"],
    "Content Hub": ["content hub"],
    "Data Collection Rule (DCR)": ["data collection rule", "dcr"],
    "ingestion-time transformation": ["ingestion-time transformation", "ingestion time transformation", "transformkql", "擷取時轉換"],
    "Azure Monitor Agent (AMA)": ["azure monitor agent", "ama agent", "azure monitor 代理程式"],
    "Syslog": ["syslog"],
    "CEF": ["common event format", "cef"],
    "custom logs / Logs Ingestion API": ["logs ingestion api", "custom log", "自訂記錄"],
    "ASIM / normalization": ["asim", "advanced security information model", "normalization parser", "正規化"],
    "watchlist": ["watchlist", "監視清單"],
    "threat intelligence (TI)": ["threat intelligence", "威脅情報", "threat indicator"],
    "STIX / TAXII": ["stix", "taxii"],
    "MDTI": ["defender threat intelligence", "mdti"],
    "commitment tier": ["commitment tier", "承諾層級"],
    "data retention / archive": ["retention", "archive", "保留期", "封存"],
    "Basic / Auxiliary logs": ["basic logs", "auxiliary logs", "auxiliary log"],
    "search job": ["search job", "搜尋工作"],
    "Sentinel data lake": ["data lake", "資料湖"],
    "summary rules": ["summary rule", "摘要規則"],
    "KQL jobs": ["kql job"],
    "Sentinel RBAC roles": ["sentinel contributor", "sentinel responder", "sentinel reader", "automation contributor"],
    "unified RBAC": ["unified rbac", "統一 rbac", "unified role-based access"],
    "Azure Lighthouse": ["lighthouse"],
    "multi-tenant / MSSP": ["multi-tenant", "多租用戶", "mssp", "gdap"],
    "Defender XDR portal": ["defender portal", "security.microsoft.com", "defender.microsoft.com", "統一入口"],
    "MDE onboarding": ["onboarding", "上線", "onboard device"],
    "device groups": ["device group", "裝置群組"],
    "automation level": ["automation level", "自動化層級", "full automation", "semi-automation"],
    "ASR rules": ["attack surface reduction", "asr rule", "攻擊面縮小"],
    "tamper protection": ["tamper protection", "竄改防護"],
    "EDR in block mode": ["block mode"],
    "web content filtering": ["web content filtering", "網頁內容篩選"],
    "indicators (IoC allow/block)": ["indicator", "指標"],
    "exclusions": ["exclusion", "排除"],
    "device discovery": ["device discovery", "裝置探索"],
    "Security Copilot": ["security copilot", "copilot"],
    "SCU capacity": ["security compute unit", "scu"],
    "promptbook": ["promptbook", "prompt book"],
    "Copilot agents": ["copilot agent", "agentic"],
    # D2 回應
    "incident vs alert": ["incident", "事件佇列", "alert"],
    "attack story / investigation graph": ["attack story", "investigation graph", "調查圖"],
    "incident classification": ["classification", "determination", "true positive", "false positive", "分類"],
    "device isolation": ["isolate", "isolation", "隔離"],
    "restrict app execution": ["restrict app execution", "限制應用程式"],
    "Live Response": ["live response", "即時回應"],
    "investigation package": ["investigation package", "調查套件"],
    "automated investigation (AIR)": ["automated investigation", "自動調查", "air"],
    "Action center": ["action center", "動作中心"],
    "Threat Explorer": ["threat explorer", "explorer"],
    "email remediation / ZAP": ["soft delete", "hard delete", "zero-hour auto purge", "zap", "郵件修復"],
    "Safe Links / Safe Attachments": ["safe link", "safe attachment"],
    "tenant allow/block list": ["tenant allow", "allow block list", "允許封鎖清單"],
    "Defender for Identity (MDI)": ["defender for identity", "mdi", "身分識別"],
    "lateral movement path": ["lateral movement", "橫向移動"],
    "pass-the-hash / ticket": ["pass-the-hash", "pass the hash", "pass-the-ticket", "golden ticket", "dcsync"],
    "Entra ID Protection": ["identity protection", "entra id protection", "risky user", "risky sign-in", "使用者風險", "登入風險"],
    "risk-based Conditional Access": ["conditional access", "條件式存取"],
    "Defender for Cloud alerts": ["defender for cloud", "工作負載保護", "cwp"],
    "suppression rules": ["suppression rule", "抑制規則"],
    "analytics rules (scheduled)": ["scheduled rule", "scheduled analytics", "排程規則", "analytics rule"],
    "NRT rules": ["near-real-time", "nrt"],
    "Fusion": ["fusion"],
    "UEBA": ["ueba", "user and entity behavior", "實體行為"],
    "anomaly rules": ["anomaly rule", "異常規則"],
    "entity mapping": ["entity mapping", "實體對應"],
    "event grouping": ["event grouping", "事件分組"],
    "MITRE ATT&CK mapping": ["mitre", "att&ck", "attack technique", "戰術"],
    "automation rules": ["automation rule", "自動化規則"],
    "playbooks (Logic Apps)": ["playbook", "logic app", "劇本"],
    "workbooks": ["workbook", "活頁簿"],
    "entity pages": ["entity page", "實體頁面"],
    # D2/D1 Purview
    "Purview Audit": ["purview", "audit log", "稽核記錄"],
    "DLP alerts": ["data loss prevention", "dlp"],
    "insider risk management": ["insider risk", "內部風險"],
    "eDiscovery": ["ediscovery"],
    # D3 搜捕
    "advanced hunting": ["advanced hunting", "進階搜捕"],
    "custom detection rules": ["custom detection", "自訂偵測"],
    "hunting queries": ["hunting query", "搜捕查詢"],
    "bookmarks": ["bookmark", "書籤"],
    "livestream": ["livestream", "live stream"],
    "hunts": ["hunt ", "hunts", "狩獵", "搜捕"],
    "notebooks (Jupyter/MSTICPy)": ["notebook", "jupyter", "msticpy", "筆記本"],
    "Sentinel Graph": ["sentinel graph"],
    "MCP server": ["mcp server", "model context protocol"],
    "go hunt": ["go hunt"],
    # KQL 運算子
    "KQL: where": ["| where", "where 運算子"],
    "KQL: project / extend": ["project", "extend"],
    "KQL: summarize": ["summarize"],
    "KQL: bin()": ["bin(", "bin （", "時間分桶"],
    "KQL: join": ["join"],
    "KQL: union": ["union"],
    "KQL: parse / extract": ["parse", "extract("],
    "KQL: let": ["let "],
    "KQL: arg_max": ["arg_max"],
    "KQL: make_list / make_set": ["make_list", "make_set"],
    "KQL: make-series / anomalies": ["make-series", "series_decompose"],
    "KQL: has vs contains": ["has_any", "has ", "contains"],
    "KQL: mv-expand": ["mv-expand", "mv_expand"],
    "KQL: externaldata": ["externaldata"],
}

STOPWORDS = {
    "The", "This", "That", "These", "Those", "And", "But", "For", "You", "Your", "We", "Our",
    "It", "If", "So", "In", "On", "At", "To", "Of", "As", "Is", "Are", "Was", "Were", "Be",
    "Now", "Then", "Here", "There", "What", "When", "Where", "Which", "How", "Why", "Who",
    "Let", "Let's", "Okay", "Right", "Well", "Also", "Just", "Like", "One", "Two", "First",
    "Second", "Next", "Last", "Module", "Lesson", "Video", "Episode", "Welcome", "Hello",
    "Learn", "Learning", "Path", "Unit", "Exam", "Course",
}


def strip_html(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", html)


def ep_slug(ep):
    return f"ep-{int(ep[2:]):02d}"


def load_transcript(ep):
    """回傳 (合併文字, 使用的語言清單)。原文與繁中翻譯都讀，術語比對用得上兩者。"""
    slug = ep_slug(ep)
    parts, langs = [], []
    for p in sorted(TRANSCRIPTS.glob(f"{slug}.*.txt")):
        lang = p.name[len(slug) + 1:-4]
        parts.append(p.read_text(encoding="utf-8", errors="ignore"))
        langs.append(lang)
    return "\n".join(parts), langs


def present_terms(text):
    low = text.lower()
    hits = {}
    for canonical, aliases in TERMS.items():
        n = sum(low.count(a) for a in aliases)
        if n:
            hits[canonical] = n
    return hits


def mine_phrases(text, min_count=3, top=12):
    """挖掘字幕中高頻的大寫多詞片語（詞典外的可能新主題）。"""
    phrases = re.findall(r"\b(?:[A-Z][a-zA-Z0-9]+(?:\s+(?:for|of|and|in)\s+)?){2,4}", text)
    counter = Counter()
    for ph in phrases:
        ph = ph.strip()
        words = ph.split()
        if len(words) < 2 or words[0] in STOPWORDS:
            continue
        if all(w in STOPWORDS for w in words):
            continue
        counter[ph] += 1
    known = " ".join(a for aliases in TERMS.values() for a in aliases).lower()
    out = []
    for ph, n in counter.most_common(200):
        if n < min_count:
            break
        if ph.lower() in known or any(ph.lower() in a or a in ph.lower()
                                      for aliases in TERMS.values() for a in aliases):
            continue
        out.append((ph, n))
        if len(out) >= top:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seqs", nargs="*", type=int, help="只檢查指定的 unit seq")
    ap.add_argument("--min", type=int, default=2, help="字幕中至少出現幾次才列入（預設 2）")
    args = ap.parse_args()

    curriculum = json.loads((SC200 / "sc200_curriculum.json").read_text(encoding="utf-8"))
    units = [u for u in curriculum["units"] if u["type"] == "study"]
    if args.seqs:
        units = [u for u in units if u["seq"] in args.seqs]

    if not any(TRANSCRIPTS.glob("ep-*.txt")):
        print("ℹ️ sc200/transcripts/ 目前只有影片標題、沒有字幕文字檔。")
        print("   請先在能連 YouTube 的電腦執行 sc200/scripts/fetch_transcripts.py")
        print("   （詳細步驟見 sc200/LOCAL_TRANSCRIPTS_GUIDE.md），commit 後再跑本工具。")
        return

    lines = ["# 字幕 × 教材覆蓋度報告", "",
             "由 `sc200/scripts/check_coverage.py` 產生。三個欄位的意義：", "",
             "- **要補教材**：影片講了、電子報沒寫 → 補進核心章節（或確認刻意略過）",
             "- **要補音檔**：電子報寫了、Podcast 沒講 → 補進對談腳本",
             "- **自主補強**：電子報寫了、影片沒講 → 應落在「考綱補洞」章節（刻意的，確認即可）", ""]
    ep_i = 0
    todo_content, todo_podcast = 0, 0

    for u in units:
        ep_i += 1
        seq, code = u["seq"], u["code"]
        eps = u.get("video_eps") or []
        tr_text, langs = "", []
        for ep in eps:
            t, l = load_transcript(ep)
            tr_text += "\n" + t
            langs += l
        news_path = CONTENT / f"day-{seq:03d}.html"
        pod_path = SCRIPTS / f"ep-{ep_i:03d}.json"
        news_text = strip_html(news_path.read_text(encoding="utf-8")) if news_path.exists() else ""
        pod_text = ""
        if pod_path.exists():
            pod_text = " ".join(t["text"] for t in
                                json.loads(pod_path.read_text(encoding="utf-8"))["dialogue"])

        lines.append(f"## Day {seq:03d} · {code} · {u['title_zh']}")
        lines.append("")
        if not tr_text.strip():
            lines.append(f"> ⚠️ {'／'.join(eps)} 尚無字幕文字，略過比對。")
            lines.append("")
            continue
        lines.append(f"影片 {'／'.join(eps)}（字幕語言：{'、'.join(sorted(set(langs))) or '—'}）"
                     f"｜電子報：{'✅' if news_text else '❌ 未撰寫'}"
                     f"｜Podcast：{'✅' if pod_text else '❌ 未撰寫'}")
        lines.append("")

        vid = {k: v for k, v in present_terms(tr_text).items() if v >= args.min}
        news = present_terms(news_text)
        pod = present_terms(pod_text)

        # 只看「實質著墨」的主題（電子報提及 ≥2 次），避免一筆帶過的名詞洗版報告
        news_core = {k: v for k, v in news.items() if v >= 2}
        gap_content = sorted(k for k in vid if k not in news)
        gap_podcast = sorted(k for k in news_core if k not in pod and k in vid)
        extra = sorted(k for k in news_core if k not in vid)
        todo_content += len(gap_content)
        todo_podcast += len(gap_podcast)

        covered = len(vid) - len(gap_content)
        pct = round(covered / len(vid) * 100) if vid else 100
        lines.append(f"**影片主題覆蓋率：{covered}/{len(vid)}（{pct}%）**")
        lines.append("")
        if gap_content:
            lines.append("### 🔴 要補教材（影片講了、電子報沒寫）")
            lines += [f"- `{k}`（字幕出現 {vid[k]} 次）" for k in gap_content]
            lines.append("")
        if gap_podcast:
            lines.append("### 🟡 要補音檔（電子報寫了、Podcast 沒講）")
            lines += [f"- `{k}`" for k in gap_podcast]
            lines.append("")
        if extra:
            lines.append("### 🔵 自主補強（電子報寫了、影片沒講——應在「考綱補洞」）")
            lines.append("- " + "、".join(f"`{k}`" for k in extra))
            lines.append("")
        mined = mine_phrases(tr_text)
        if mined:
            lines.append("### 🔍 字幕高頻片語（詞典未收錄，人工判斷是否為新主題）")
            lines.append("- " + "、".join(f"{p}×{n}" for p, n in mined))
            lines.append("")

    lines.append("---")
    lines.append(f"合計待補：教材 {todo_content} 項、Podcast {todo_podcast} 項。")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ 已寫出 {REPORT.relative_to(SC200.parent)}")
    print(f"   待補：教材 {todo_content} 項、Podcast {todo_podcast} 項")


if __name__ == "__main__":
    main()
