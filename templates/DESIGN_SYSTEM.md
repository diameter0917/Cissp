# CISSP 電子報設計系統（CISSP Swiss）

> 本系統依匯入的 **ui-ux-pro-max** skill 建議制定（Swiss Modernism / Minimalism：
> 單一強調色、嚴謹 8px 間距、模組化字級、WCAG 對比）。
> 並針對「HTML email」的限制做在地化調整（見最後一節）。
> 既有 120 封信由 `scripts/restyle_emails.py` 收斂到本系統；新信件請用 `templates/master.html` 撰寫。

## 1. 設計目標

過往信件累積出 **兩套副色盤**——核心教學的 navy/teal，與後來「官方考綱對照」帶進來的
金/棕 parchment，外加少數信件漂移出的靛藍。視覺因此不一致。本次「重整」把它們
**收斂成單一系統**：

- **單一強調色**：deep teal `#0A6160`（連結、序號、CIA 柱、border-left、進度）。
- **金/棕考綱副色盤 → slate 中性灰**：考綱對照改為乾淨的「參考文件」灰，強調色用 teal 綁回品牌。
- **靛藍副強調 → teal**：併入單一強調色。
- **加深墨色與內文**：提升對比到 WCAG AA。

## 2. 色彩 token（語意化）

| 角色 | Token | 用途 |
|---|---|---|
| Ink（品牌墨色） | `#0F1B2D` | 報頭底、h1、表頭、強調標題 |
| Body | `#1E293B` | 內文（slate-800，對比佳） |
| Muted | `#5B6675` | 次要說明、圖說、表格副欄 |
| Slate-700 / 600 / 500 | `#334155` / `#475569` / `#64748B` | 考綱內文 / 深 / 出處標註 |
| On-navy muted / sub | `#8FA0B6` / `#C7D2E0` | 報頭上的灰字 / 副標 |
| **Accent（單一強調）** | `#0A6160` | 連結、序號 `01—`、CIA 柱底、border-left、進度條 |
| Accent tint | `#EAF4F3` | 案例 / 重點淡底框 |
| **Warning（考點警示）** | `#B45309` | 考點標題、border-left、`被破壞時`欄 |
| Warning bg / text | `#FBF4E8` / `#4A3A1C` | 考點框底 / 框內文 |
| Surface | `#F8FAFC` | 淺表面、考綱「參考文件」底 |
| Info bg | `#F1F5F9` | 路線 / 一般資訊框底 |
| Page bg | `#EEF2F6` | 信件外圍底色 |
| Card | `#FFFFFF` | 信件本體 |
| Hairline / Border | `#E2E8F0` | 髮絲線、邊框（唯一邊框色） |
| Border-2 | `#CBD5E1` | 虛線框 |

**保留的語意暖色**：考點 amber（`#B45309` / `#FBF4E8` / `#4A3A1C`）刻意保留，作為唯一的
「警示」語意色，與強調 teal 區隔——符合 skill 的 `color-semantic` 原則。

## 3. 字級（模組化，去除半階）

`11 · 12 · 13 · 14 · 15 · 16 · 18 · 22`（px）

| 級 | 用途 |
|---|---|
| 22 | h1 標題 |
| 18 | 區段子標 |
| 16 | 導讀 / 重點段 |
| 15 | 內文 |
| 14 | 次要內文、表格 |
| 13 | 小字、考綱、圖說 |
| 12 | 標註、出處 |
| 11 | eyebrow（`01 —`）、meta、footer |

行高：內文 `1.8`（CJK 易讀）、小字 `1.7`、h1 `1.35`。
字重：標題 `700`、內文 `400`、label/mono `700`。

## 4. 間距與形狀（8px 節奏）

- 區段間距：`margin-top: 24px`
- 框內 padding：`12–16px`
- 頁面 padding：`20px 12px`
- 圓角：卡片 `16`、區塊 `10–12`、pill `5–6`
- 邊框：一律 `1px solid #E2E8F0`（虛線用 `#CBD5E1`）

## 5. 字型堆疊（email 安全）

```
本文/標題  -apple-system,'PingFang TC','Microsoft JhengHei','Noto Sans TC','Hiragino Sans',sans-serif
標籤/代號  'SFMono-Regular',Consolas,Menlo,monospace
```

> email 不可靠載入 web font（Gmail 會剝除 `@import`），故沿用系統字（繁中正確顯示）。

## 6. 元件清單（見 `master.html`）

報頭｜進度條｜區段標題 `NN —`｜段落｜路線/資訊框｜資料表｜border-left 重點｜
名詞速查｜易混淆框｜案例框（teal 淡底）｜考點框（amber）｜官方考綱對照框（slate 參考文件）｜
自我檢測｜影片框｜今日時事框｜頁尾。

## 7. HTML Email 在地化限制（重要）

- **全程 inline CSS**：Gmail 會剝除 `<head>`/`<style>` 與 class，故所有樣式寫在 `style=""`。
- **600px 寬**、`role="presentation"` 表格排版，相容多數客戶端。
- **不用 web font**：見上。
- **`<details>` 折疊在多數 email 客戶端失效**：Gmail 會移除收合，內容直接全顯示。
  - 既有 120 封沿用 `<details>`（收斂時保留結構，僅換色）。
  - `master.html` 的「自我檢測」改用 **email-robust 靜態區塊**（解答以分隔線＋ teal 字呈現，不依賴折疊）。
- **深色模式**：部分客戶端會自動反相；本系統用高對比語意色，降低反相破圖風險。

## 8. 如何使用

```bash
# 既有信件收斂到本系統（預覽單檔→輸出到 preview/）
python3 scripts/restyle_emails.py --out templates/preview emails/day-001.html

# 批次套用到全部既有信件（emails + docs/archive + sample）
python3 scripts/restyle_emails.py --all

# 撰寫新信件：複製 master.html，替換 {{PLACEHOLDER}}，刪除用不到的元件區塊
```
