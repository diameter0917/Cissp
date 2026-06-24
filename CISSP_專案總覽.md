# CISSP 每日電子報系統 — 專案總覽

這份文件把整個規劃從頭到尾講一遍，方便你全盤確認。搭配另外兩個檔案使用：
- **`CLAUDE_CODE_PROMPT.md`** — 給 Claude Code 執行的指令（貼進去就開工）
- **`cissp_curriculum.json`** — 餵給 Claude Code 的課綱資料（120 個單元）

---

## 1. 這個系統在做什麼

每個平日早上 7 點（台灣時間），自動寄一封約 10 分鐘可讀完的 CISSP 學習電子報到你信箱，內容繁中說明、英文術語並列，搭配真實事件案例與對應的教學影片。整套系統半年內帶你把 CISSP 八大考科走完一輪，且運作期間零 API 費用。

整個系統分兩塊運作，外加一個成本說明：

**建置（一次性，由 Claude Code 完成）**：產生 120 封教材信、排程表、寄信程式、追蹤網頁、GitHub Actions 設定，並抓影片字幕讓教材對齊影片。

**每日運作（混合架構）**：教材是預先產好的靜態檔（評審過、固定、寄送免費）；每天另由一個輕量 Claude Routine 產生「今日時事延伸」一小段、commit 進 repo；GitHub Actions 把教材與當天時事**合併成同一封信**、用 Gmail SMTP 寄出、把「已寄送」寫回 repo。時事有就附上、沒有不影響教材照常寄。

**成本**：教材寄送完全免費（純 SMTP，零 API）；只有「今日時事」那一小段每天消耗少量 Max 訂閱額度。寄信走最穩的 SMTP，不依賴連接器寄信。

---

## 2. 學習結構：螺旋式三階段

這是整個設計的核心。8 個 Domain（章節）會被走過三輪，每輪深度遞增，每個 Domain 在每輪佔一週（週一到週五 5 封）。**階段優先**：先把 8 個 Domain 的輪廓全看完，再進中期、再進後期。

| 階段 | 內容 | 涵蓋順序 | 週次 | 信件數 | 搭配影片 |
|---|---|---|---|---|---|
| 初期：章節輪廓 | 建立全貌、先抓骨架 | D1 → D8 | 第 1–8 週 | 40 | Full Course 2026（各 Domain 完整影片）|
| 中期：細說內容 | 名詞、條文、案例深入（最完整）| D1 → D8 | 第 9–16 週 | 40 | MindMap 主題複習 |
| 後期：考試重點 | 考試陷阱、選最佳答案、刷題 | D1 → D8 | 第 17–24 週 | 40 | 考題練習清單 |

**合計 120 封、24 週、約 5.5 個月**，週末休息，半年內跑完第一輪。

為什麼這樣設計：你原本擔心「一個章節拖快一個月太久」。螺旋式正好解決——先用 8 週快速建立整個 CISSP 的輪廓，不會卡在某一個 Domain 太久；之後兩輪再回頭加深。這也滿足「先了解輪廓、主題輪過後再重複相同主題但不同細節」的需求。

每個 Domain 佔多少分量，是依官方考試權重設計的（D1 安全與風險管理最重，16%）。八大 Domain 與權重採用 (ISC)² 2024/4/15 生效的現行版本。

---

## 3. 每封信長什麼樣

每封信固定八個區塊，繁中說明、英文術語並列（例如 `Least Privilege（最小權限）`）：

1. 本日主題 + 所屬 Domain + 階段標記（如 `D1 · 初期 · 16%`）
2. 深入淺出講解（深度隨階段變化：初期重輪廓、中期最深入、後期偏考點條列）
3. 關鍵名詞解釋（英文 + 中文並列）
4. 條文／標準說明（NIST、ISO 27001/27701、GDPR、台灣個資法、FSC 等，適用時才放）
5. 真實事件案例（用教科書級事件串概念，例如 Equifax、SolarWinds、Colonial Pipeline）
6. CISSP 考點提醒（後期為主軸，講陷阱與「選最佳答案」思路）
7. 一句話總結 + 1–2 題自我檢測
8. 📺 本日對應影片（依階段連到對應的影片）

長度約 1,000–1,600 字，手機好讀。

**案例的時效處理**：靜態信用的是「不會過期」的經典事件當教材；「每天最新的時事」由 Routine 即時補。兩者分工，所以信件就算半年後讀，案例也不會顯得過時。

---

## 4. 影片整合

你給的兩個 playlist，加上我找到的第三個系列，剛好對應三個階段：

- **初期** → CISSP Full Course 2026（一支影片講完一個 Domain，已確認 8 支對 8 個 Domain）
- **中期** → CISSP MindMap / Domain Review（主題式心智圖複習）
- **後期** → CISSP Exam Questions（26 支考題，刷題用）

三個 playlist 的網址都已寫進 `cissp_curriculum.json`。**影片資料由你在本機跑 `prepare_youtube.py` 一次抓好**（用 yt-dlp，不需 YouTube API 金鑰），產生 `video_index.json`(全部影片清單+依內容分類+字幕長度+章節)與 `transcripts/`(各影片字幕)，commit 進 repo。Claude Code 之後直接讀這些現成檔案、把對應主題的具體影片連進每封信（例如 Domain 5 存取控制那封 → 「Access Control MindMap｜Domain 5」），**完全不必自己連 YouTube**。

**每封信固定放兩支影片**：① 與本單元主題最相符的**重點短片**（「Domain N Review / Mind Map」分集或主題 MindMap，聚焦單一子主題，最適合每日一主題，也用來對齊教材）；② 保留該 Domain 的 **course 完整課程**影片當「看全貌」。後期 P3 可再加該 Domain 的 practice 考題影片。三類影片都已涵蓋全部 8 個 Domain。

**教材對齊影片**：生成教材時參照對應影片的字幕**對齊結構與涵蓋範圍**，讓「看影片 + 讀信」是同一條脈絡、並可延伸補充影片提到的點。重要原則：**以官方 CISSP 大綱為正確性錨點**，字幕只當對齊與延伸參考（自動字幕對技術名詞常有錯，不當事實來源），用自己的話寫。

**備援**：若 `video_index.json`/`transcripts/` 不存在，影片退回連整個 playlist、教材走純大綱，系統照常運作。

---

## 5. 寄送與追蹤

**寄送**：GitHub Actions 用 cron 在台灣平日早上 7 點觸發（`0 23 * * 0-4`，UTC），跑寄信程式，用 Gmail SMTP（app password）寄出。寄信程式自己也會再確認「今天是不是排程日」，雙重保險。

**追蹤網頁**（GitHub Pages）：一個表格／快速索引，每列一封信，顯示階段、Domain、標題、是否已寄送（綠勾／空格），可隨時點開重看任一封歷史信件。上方有階段／Domain 篩選、進度條（已寄 X／120）、搜尋框。手機友善。

**全自動狀態回寫**：Actions 寄完信後，自動把「已寄送」寫回 repo 的 `sent_log.json`，追蹤頁讀這個檔顯示綠勾。你完全不用手動打勾。

---

## 6. 成本設計（混合架構）

- **教材寄送執行路徑零 pay-per-use API**：寄信、排程、狀態回寫全部用 Python 標準庫與 GitHub Actions 內建能力。教材是預先生成的靜態檔，每天寄信不呼叫任何 AI API。
- **只有「今日時事」那一小段**由每日 Routine 產生，消耗少量 Max 訂閱額度（非 API 計費）；一天一封遠在 Routine 每日上限內。
- **yt-dlp 只在建置時跑一次**，不放進每日流程。
- **寄信走最穩的 SMTP**，不依賴連接器寄信。

這在你最在意的「教材零成本 + 可把關正確性 + 寄送可靠」與「時事夠新、寫進同一封信」之間取得平衡。

---

## 7. 手機可行性

可以全程在手機做。用手機的 Claude Code 雲端 session 跑，把 prompt 貼進去就能生成所有檔案並 commit 到 GitHub。每日寄信本來就在 GitHub Actions 上跑，跟你用手機或電腦設定無關。

唯一要注意：yt-dlp 那一步在雲端 session 可能被 YouTube 擋（已有備援退回 playlist 連結，不影響系統運作）。若想要精準的單支影片連結，可改在任一台真電腦（或免費的 Google Cloud Shell、或用 Remote Control 連回家中電腦）把那一步跑一次，產生 `video_index.json` 後 commit 進 repo。

貼長 prompt 很適合手機——你不用打長指令，貼上後看樣本、回「OK 繼續」即可。

---

## 8. 你要做的事

### A. 現在就能先設定（GitHub 端）

1. 把 `cissp` repo 設為 **public**（GitHub Pages 免費版 + Routine 要讀公開的 schedule.json 都需要）
2. Gmail 開兩步驟驗證 → 產生**應用程式密碼**（app password）
3. 在 repo 設三個 Secrets（Settings → Secrets and variables → Actions）：
   - `GMAIL_USER`（寄件 Gmail）
   - `GMAIL_APP_PASSWORD`（剛產生的密碼）
   - `RECIPIENT_EMAIL`（你要收信的信箱）
4. Settings → Actions → General → Workflow permissions → 選 **Read and write**
5. GitHub Pages 先別開，等 Claude Code 建好 `/docs` 後再到 Settings → Pages 設來源

### B. 在電腦上抓 YouTube 資料（只此一步需要電腦，✅ 你已完成）

6. 在能連 YouTube 的電腦跑 `python prepare_youtube.py`（用 yt-dlp），產生 `video_index.json` 與 `transcripts/`，再 commit 進 repo。這一步把唯一會被雲端擋的部分一次解決，之後 Claude Code 直接用現成檔。

### C. 開工（貼 prompt 給 Claude Code，手機/電腦皆可）

7. 把 `cissp_curriculum.json` 放進 `cissp` 專案根目錄；把 `sample_day-001.html` 放進 `templates/`（風格範本，Claude Code 照它的版型生成 120 封）
8. 把 `CLAUDE_CODE_PROMPT.md` 內容貼給 Claude Code
9. Claude Code 會先跟你確認計畫 → 同意後開始；它會**先做 P1-D1 那 5 封樣本給你看**，確認風格後再全量生成 120 封

### D. 系統跑起來後

10. 到 Settings → Pages 開啟 GitHub Pages（來源指向 `/docs`）
11. 在 **claude.ai/code/routines** 設一個每日時事 Routine（Claude Code Routine，prompt 與設定見 prompt 檔附錄）：選 `cissp` repo、排台北約 06:30（早於寄信的 07:00）、開啟該 routine 的「Allow unrestricted branch pushes」讓它能 commit 時事檔回主分支、並把環境網路放寬到可查新聞。它每天產「今日時事」commit 進 repo，寄信 workflow 再合併寄出。

---

## 9. 三個檔案的分工

| 檔案 | 給誰 | 作用 |
|---|---|---|
| 本總覽 | 你 | 全盤理解與行動清單 |
| `CLAUDE_CODE_PROMPT.md` | Claude Code | 建置整個系統的指令 |
| `cissp_curriculum.json` | Claude Code | 120 單元課綱 + 影片資源資料 |

---

## 10. 幾個務實的提醒

- **內容由 Claude Code 生成，不是我**：120 篇教材由 Claude Code 依課綱生成，正確性請在閱讀時順手把關。prompt 已要求它對沒把握的事實標註、不要編造。
- **先 MVP 再全量**：建議先把「排程 + 寄信 + 1 封樣本 + workflow + 追蹤頁骨架」端到端打通、確認能寄到信，再回頭全量生成 120 封。
- **影片精準對應是加分、非必要**：就算 yt-dlp 走備援（只給 playlist 連結），系統一樣完整可用。
- **第二輪可延伸**：排程邏輯用 seq 疊代設計，跑完第一輪後，未來要排第二輪（相同主題、換新案例）可重新生成，不用打掉重做。
