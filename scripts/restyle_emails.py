#!/usr/bin/env python3
"""
restyle_emails.py
=================
把既有電子報 HTML 重新套用「CISSP Swiss」統一設計系統（重整設計樣板用）。

設計依據：匯入的 ui-ux-pro-max skill（Swiss Modernism / Minimalism）建議——
單一強調色、嚴謹 8px 間距、清楚模組化字級、WCAG 對比。
本腳本把過往逐步漂移出來的「金/棕考綱副色盤」與「靛藍副強調色」收斂回
單一 teal 強調色 + slate 中性灰 + 語意化警示色（amber 考點），並加深墨色與
強調色以符合對比標準。

特性：
  - 純 token 取代（顏色、字級、間距、圓角），不更動任何教材文字或結構。
  - 每個舊 hex 在全語料中只有單一語意角色，故全域取代安全。
  - 可逆（git 追蹤）。冪等：新值不會再被任何規則命中。

用法：
  python3 scripts/restyle_emails.py <file...>          # 指定檔案就地改寫
  python3 scripts/restyle_emails.py --emails           # 全部 emails/day-*.html
  python3 scripts/restyle_emails.py --all              # emails + docs/archive + sample
  python3 scripts/restyle_emails.py --out DIR <file>   # 輸出到 DIR（不就地改，預覽用）
  python3 scripts/restyle_emails.py --check <file...>  # 只報告會改幾處，不寫入
"""

import re
import sys
import glob
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── 色彩 token 映射（舊 → 新）；key 一律大寫，比對時不分大小寫 ──────────────
HEX_MAP = {
    # 墨色 / 內文（加深以提升對比）
    "#15233B": "#0F1B2D",   # ink：報頭底、h1、表頭、強調
    "#2A3340": "#1E293B",   # 內文 → slate-800（對比更高）
    # 頁面 / 表面 / 邊框（收斂為單一灰階系統）
    "#ECEFF3": "#EEF2F6",   # 頁面底
    "#F6F8FA": "#F8FAFC",   # 淺表面
    "#FAFBFC": "#F8FAFC",   # 淺表面
    "#F0F4F8": "#F1F5F9",   # 資訊框底
    "#E9F3F2": "#EAF4F3",   # 案例框（teal 淡底）
    "#EEF0F3": "#E2E8F0",   # 髮絲線
    "#E6E9ED": "#E2E8F0",   # 邊框
    "#E2E5EA": "#E2E8F0",   # 邊框
    # 單一強調色 teal（統一並加深 → AA 對比）
    "#0E7C7B": "#0A6160",   # 主強調：連結、序號、CIA 柱、border-left、進度
    "#0A5A59": "#0A6160",   # 解答/案例標題 → 併入主強調
    # ── 金/棕「考綱」副色盤 → slate「參考文件」中性灰（最大統一動作）──
    "#FFFBF2": "#F8FAFC",
    "#FFFDF8": "#F8FAFC",
    "#EFE2C4": "#E2E8F0",
    "#E2D2A8": "#CBD5E1",
    "#C9962E": "#0A6160",   # 考綱左框 → 強調 teal（綁回品牌）
    "#8A6D1E": "#0A6160",   # 考綱標題 → 強調 teal
    "#7A6E4E": "#334155",   # 考綱內文（最大宗）→ slate-700
    "#5A4F33": "#475569",   # 深金 → slate-600
    "#3A3220": "#1E293B",   # 最深金 → slate-800
    "#A0895A": "#64748B",   # 出處標註 → slate-500
    "#9A8456": "#64748B",   # 註記 → slate-500
    "#E8C089": "#64748B",   # 淺金文字 → slate-500
    # ── 靛藍副強調 → 統一回 teal ──
    "#3D52A0": "#0A6160",
    "#EEF1F8": "#F1F5F9",
    "#B7C0DF": "#CBD5E1",
    "#5A6CB0": "#0A6160",
    "#8A97C8": "#CBD5E1",
    # 保留（語意/已和諧）：#FFFFFF #5B6675 #8FA0B6 #C7D2E0 #9AA6B4
    #                    #B45309 #FBF4E8 #4A3A1C（amber 考點，語意警示）
    #                    #9CCFCE #6FB8B7 #3E9A99（teal 淡階，已同系）
    #                    #C7741F #D89A55（各 1 次的暖色斑點，避免對比風險不動）
}

# ── 字級：消除半階、snap 回模組化字級 ──────────────────────────────────
SIZE_MAP = {
    "10.5": "11", "12.5": "13", "13.5": "14", "14.5": "15", "15.5": "16",
}

# ── 圓角：卡片外框柔化 ────────────────────────────────────────────────
RADIUS_MAP = {"14px": "16px"}

# ── 外觀刷新（--refresh）：依 skill「Editorial / Exaggerated Minimalism」建議 ──
#   更大內文（16px，符合 UX High-severity「mobile 內文最小 16px」）、更大標題、
#   更寬鬆的區段留白。單次掃描對應，避免級聯（15→16 與 16→17 不互相疊加）。
REFRESH_FONT = {"15": "16", "16": "17", "22": "26"}          # 內文 / 導讀 / h1
REFRESH_MARGIN_TOP = {"24px": "28px"}                         # 區段間距更寬鬆


def editorial_refresh(text: str):
    n = 0
    def _fs(m):
        nonlocal n
        v = m.group(1)
        if v in REFRESH_FONT:
            n += 1
            return f"font-size:{REFRESH_FONT[v]}px"
        return m.group(0)
    text = re.sub(r"font-size:(\d+)px", _fs, text)            # 單次掃描，無級聯
    for old, new in REFRESH_MARGIN_TOP.items():
        text, c = re.subn(rf"margin-top:{old}", f"margin-top:{new}", text)
        n += c
    return text, n


def restyle(text: str):
    n = 0
    # 顏色（不分大小寫）
    for old, new in HEX_MAP.items():
        pat = re.compile(re.escape(old), re.IGNORECASE)
        text, c = pat.subn(new, text)
        n += c
    # 字級半階 → 整階（僅限 font-size，避免動到其他數字）
    for old, new in SIZE_MAP.items():
        text, c = re.subn(rf"font-size:{old}px", f"font-size:{new}px", text)
        n += c
    # 區段間距 snap 到 8 格（僅 margin-top，避免動到 font-size:22px）
    text, c = re.subn(r"margin-top:22px", "margin-top:24px", text)
    n += c
    # 卡片圓角
    for old, new in RADIUS_MAP.items():
        text, c = re.subn(rf"border-radius:{old}", f"border-radius:{new}", text)
        n += c
    return text, n


def collect(args):
    files = []
    if "--emails" in args:
        files += sorted(glob.glob(str(ROOT / "emails" / "day-*.html")))
    if "--all" in args:
        files += sorted(glob.glob(str(ROOT / "emails" / "day-*.html")))
        files += sorted(glob.glob(str(ROOT / "docs" / "archive" / "day-*.html")))
        sample = ROOT / "templates" / "sample_day-001.html"
        if sample.exists():
            files.append(str(sample))
    files += [a for a in args if not a.startswith("--") and a != (outdir or "")]
    # de-dup preserve order
    seen, uniq = set(), []
    for f in files:
        if f not in seen:
            seen.add(f); uniq.append(f)
    return uniq


if __name__ == "__main__":
    args = sys.argv[1:]
    check = "--check" in args
    refresh = "--refresh" in args      # 套用外觀刷新（型號/留白），而非色盤收斂
    transform = editorial_refresh if refresh else restyle
    outdir = None
    if "--out" in args:
        i = args.index("--out")
        outdir = args[i + 1]
        Path(outdir).mkdir(parents=True, exist_ok=True)
        del args[i:i + 2]

    files = collect(args)
    if not files:
        print("用法：restyle_emails.py [--emails|--all|--check|--out DIR] <file...>")
        sys.exit(1)

    total = 0
    for f in files:
        src = Path(f)
        text = src.read_text(encoding="utf-8")
        new, n = transform(text)
        total += n
        if check:
            print(f"  {src.name}: {n} 處可改")
            continue
        if outdir:
            dest = Path(outdir) / src.name
            dest.write_text(new, encoding="utf-8")
        else:
            src.write_text(new, encoding="utf-8")
    label = "可改" if check else "已套用"
    print(f"完成：{len(files)} 檔，共 {total} 處 token {label}。")
