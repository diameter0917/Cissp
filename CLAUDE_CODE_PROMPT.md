# Claude Code 任務指令：CISSP 每日電子報系統（螺旋式三階段版）

> 把這整份貼進 Claude Code，並把 `cissp_curriculum.json` 一起放進專案 `cissp` 根目錄。

---

## 一、專案目標

在現有 GitHub 專案 `cissp` 中，建立一套**全自動的 CISSP 每日學習電子報系統**：

- **採混合架構**：教材核心為**靜態預生成**（一次寫好存進 repo，評審過、固定、免費）；每天另由一個輕量 **Claude Routine** 產生「今日時事延伸」一小段，commit 進 repo，由寄信流程**與當天教材合併成同一封信**寄出。
- **僅平日（週一至週五）**透過 **GitHub Actions + Gmail SMTP** 自動寄信，週末休息。
- 教材部分**執行路徑零 pay-per-use API**（純 SMTP 寄送）；只有「今日時事」那一小段每天消耗少量 Max 額度。
- 採**螺旋式三階段**結構，依 `cissp_curriculum.json` 的 120 個單元排程，**24 週、約 5.5 個月、半年內跑完**。
- 教材生成時，除官方 CISSP 大綱外，**參照對應影片的字幕**對齊結構與涵蓋範圍（見「影片資料」一節）。
- 寄出後**自動回寫寄送狀態**到 repo。
- 在 **GitHub Pages** 上有追蹤網頁：表格/快速索引顯示每封信是否已寄送，可隨時點開重看任一封。
- 產生**公開的 `schedule.json`**，供時事 Routine 與追蹤頁讀取當天主題。

我在英文版考 CISSP，但需要**繁體中文說明 + 英文術語並列**（如 `Least Privilege（最小權限）`）。

---

## 二、螺旋式三階段結構（核心）

8 個 Domain（章節），每個 Domain 在每個階段佔 **1 週 = 週一到週五共 5 封**。**階段優先（phase-major）**：先把 8 個 Domain 的初期全上完，再進中期，再進後期。

| 階段 | 內容深度 | 涵蓋順序 | 週次 | 信件 | 搭配影片系列 |
|---|---|---|---|---|---|
| **初期 P1** 章節輪廓 | 建立全貌、輕量、重骨架 | D1→D8 | 第 1–8 週 | 40 | Full Course 2026（該 Domain 完整影片）|
| **中期 P2** 細說內容 | 名詞/條文/案例深入、最完整 | D1→D8 | 第 9–16 週 | 40 | MindMap 主題複習清單 |
| **後期 P3** 考試重點 | 考試陷阱、選最佳答案、刷題、偏條列 | D1→D8 | 第 17–24 週 | 40 | 考題練習清單（刷題）|

`cissp_curriculum.json` 的 `units` 已按此順序排好 `seq` 1–120（如 `P1-D1-1` … `P3-D8-5`），`weekday_in_week` 標示該封是該 Domain 週的週幾（1=週一…5=週五）。

---

## 三、內容規格（每封電子報）

依 `cissp_curriculum.json` 每個單元的 `focus_zh`（內容大綱）、`suggested_case`（案例）生成一封 HTML 電子報。每封含以下區塊，**繁中說明 + 英文術語並列**：

> **內容來源原則（重要）**：以**官方 CISSP 大綱為正確性錨點**（名詞、條文以官方為準）。教材**優先對齊「與本單元主題最相符的短片」字幕**——該 Domain 的「Domain N Review / Mind Map」分集或主題 MindMap（字幕在 `transcripts/<video_id>.txt`）；這些短片逐一對應子主題，最貼合每日一個主題的信。該 Domain 的 course 完整影片字幕可當補充。讓「看影片 + 讀信」對得起來，並可在信中延伸補充影片提到的點。字幕僅作對齊與延伸參考——**自動字幕對技術名詞常有錯，不可當作事實來源**；用自己的話寫，不照抄字幕字句。抓不到字幕時退回純大綱生成。

1. **本日主題 + Domain + 階段標記**：如 `D1 · 初期 · 16% · P1-D1-2`，顯示 Domain 名稱、權重、階段。
2. **深入淺出講解**：**依階段調整深度** —
   - 初期 P1：重輪廓與直覺，先建立「這個 Domain 在講什麼」的全貌，可略短。
   - 中期 P2：最完整，深入名詞、條文、機制、案例。
   - 後期 P3：偏條列，聚焦考試會怎麼考。
3. **關鍵名詞解釋**：條列 3–6 個核心術語，英文 + 中文解釋。
4. **條文／標準說明**：引用相關標準/法規（NIST SP 800 系列、ISO 27001/27701、GDPR、台灣個資法 PDPA、FSC 金融資安規範等，適用時才放）。
5. **真實事件案例討論**：用該單元 `suggested_case` 指定的教科書級事件串起概念。
6. **CISSP 考點提醒**：**後期 P3 以此為主軸**；說明常見陷阱與 (ISC)² 「選最佳答案」的思路。
7. **一句話總結 + 1–2 題自我檢測**（附解答，可用 `<details>` 收合）。
8. **📺 本日對應影片（固定放兩支）**：
   - **① 重點短片（聚焦本主題）**：該 Domain 中與本單元主題最相符的 **mindmap** 短片（「Domain N Review / Mind Map」分集或主題 MindMap），每支聚焦單一子主題，最適合每日一主題。
   - **② 完整課程（看全貌）**：保留該 Domain 的 **course** 完整影片；若能從 `transcripts/_timed/<id>.vtt` 定位主題時間碼，用 `https://youtu.be/<id>?t=<秒數>` 標「從約 mm:ss」，否則連開頭。
   - **後期 P3** 可再加 **③** 該 Domain 的 **practice** 考題影片（刷題）。
   - 兩支各有清楚標籤、都是正式連結（不要把完整課程做成不起眼的小附註）。①若對不到夠精準的短片，退回連 course 或對應 playlist（此時可能只剩一支）。
9. **🗞️ 今日時事延伸（此區塊由每日 Routine 動態填入，非預生成）**：在教材本文末預留一個明確的占位標記 `<!-- TODAY_NEWS -->`。每日 Routine 會把當天與本主題相關的最新資安新聞（約 3 點）寫進這個位置；寄信時若該段存在就合併、不存在就照常只寄教材本文（見第六節與附錄）。

**呈現方式（重要）：不要只用文字敘述。** 凡是有結構的內容都盡量視覺化，幫助理解與記憶：
- 比較／對照 → **表格**；流程或關係 → **box-and-arrow 示意圖**；分類 → **矩陣**；層級 → **樹狀圖**；時序 → **時間軸**；重點口訣 → **記憶框**（如 CIA↔DAD、三柱圖）。
- **每封至少放 1–2 個視覺化元素**（表格或示意圖），不要整封都是段落。
- 文字負責解釋「為什麼、怎麼想」，視覺負責「結構、對照、記憶點」，兩者搭配。

**份量與深度（已提高）**：內容要更充實，不要只點到為止。具體要求：
- 名詞解釋至少 **5–8 個**；適時加入「**易混淆／常見誤解**」小段、控制對應、記憶法（如 CIA 的反面 DAD）。
- 自我檢測 **2–3 題**；中期可放第二個案例或一個對照表。
- **長度（依階段）**：初期 P1 約 **1,500–2,200 字**（最精簡、重輪廓）；中期 P2 約 **2,800–3,800 字**（最完整、深入名詞條文案例）；後期 P3 約 **2,000–2,800 字**（偏條列、考點與刷題）。閱讀約 12–15 分鐘。
- 寧可內容紮實，但仍要好讀：多用小標、表格、重點標記與留白，避免大段不換行的長文。

**可讀性**：手機單欄、區塊分明、適度顏色標記。參見下方「HTML 範本規格」。

### HTML 範本規格（風格範本）

我會把 `sample_day-001.html`（初期第一封的完整範本）放進專案（例如 `templates/sample_day-001.html`）。**請開啟它，並以它為所有 120 封信的版型與設計基準**，逐封只換內容、不改設計系統。要點：

- **設計 token**：報頭深藍 `#15233B`；階段強調色——初期 P1 `#0E7C7B`(teal)、中期 P2 `#3D52A0`(indigo)、後期 P3 `#B45309`(amber)；頁面底 `#ECEFF3`、卡片白、邊框 `#E2E5EA`、次要文字 `#5B6675`；考點框用 amber 系。主字體 `-apple-system,'PingFang TC','Microsoft JhengHei','Noto Sans TC',sans-serif`，代碼/標籤用等寬字。
- **報頭結構**：等寬字「CISSP 每日電子報 · DAY n/120」+ 單元代碼晶片（如 `P1-D1-1`，用該階段色）+「階段 | Domain | 權重」+ 中文大標 + 英文小標 + 一條進度條（寬度＝seq/120）。
- **區塊以等寬數字序號標題**（01/02/…），各區塊間用留白與圓角卡片分隔。沿用範本的：CIA/比較用表格、案例用 teal 淡底框、考點用 amber 左邊框框、易混淆用灰底框、自我檢測用 `<details>` 收合、影片區塊、`<!-- TODAY_NEWS -->` 占位 + 時事框、頁尾（回索引 + 等寬 `Day n/120 · 代碼`）。
- **全程 inline CSS**（信箱不吃外部樣式表），單欄、最大寬約 600px，行高約 1.8。
- **示意圖一律用 email-safe 的 HTML/CSS 製作**（表格、加邊框的 `div`、底色色塊、文字箭頭 → ↓ 等；參見範本中的「CIA 三柱」示意圖），**不要用 SVG 或外部圖片**——多數信箱（Gmail、Outlook）會擋。網頁版（`docs/archive`）沿用同樣的 HTML 圖，兩邊一致。
- **依階段微調**：強調色換成該階段色；中期 P2 內容最多（可加第二案例、對照表）；後期 P3 偏條列與考點。其餘版型保持一致。
- 各封 HTML 同時輸出網頁版到 `docs/archive/day-XXX.html`（內容相同，頁尾「← 回索引」連回 `index.html`）。

---

## 四、檔案結構

```
cissp/
├── cissp_curriculum.json        # 我已提供，讀它當資料來源
├── templates/sample_day-001.html # 我提供的風格範本，所有信件照它的版型生成
├── video_index.json             # 我已預先產生並 commit：全部影片清單(含分類/domain/字幕長度) + 章節
├── transcripts/                 # 我已預先產生：<video_id>.txt 各影片字幕；_timed/<id>.vtt 為 course 影片時間碼字幕
├── news/                        # 每日 Routine 產生：day-XXX-news.html（今日時事段落），由 send_daily 合併
├── schedule.json                # 你產生：日期→單元（給時事 Routine 與追蹤頁讀），複製一份到 docs/
├── sent_log.json                # workflow 自動回寫，複製一份到 docs/
├── emails/day-001.html ... day-120.html   # 120 封預生成電子報（完整 HTML，inline CSS）
├── scripts/
│   ├── send_daily.py            # 挑當天單元、合併今日時事、寄出、回寫 log
│   └── build_schedule.py        # 由 curriculum 產生 schedule.json（跳過週末）
├── docs/                        # GitHub Pages 根
│   ├── index.html               # 追蹤頁：表格/索引 + 已寄狀態 + 進度 + 階段/Domain 篩選
│   ├── archive/day-001.html ... # 歷史信件網頁版（可點開重看）
│   ├── schedule.json
│   └── sent_log.json
├── .github/workflows/daily.yml  # 每日(平日)排程 workflow
└── README.md
```

`emails/` 是寄信用完整 HTML（inline CSS，信箱不吃外部 CSS）；`docs/archive/` 是網頁瀏覽版。

### 影片資料（已預先產生並 commit，直接使用，不要自己連 YouTube）

`video_index.json` 與 `transcripts/` **已由我在本機用 yt-dlp 跑好並 commit 進 repo**。請**直接讀取使用，不要在 Claude Code 環境再連 YouTube 或跑 yt-dlp**（雲端環境的 IP 會被 YouTube 擋）。

**`video_index.json` 實際結構**：
```json
{
  "videos": [
    {"id":"J-su239XmCE","title":"...","url":"https://youtu.be/J-su239XmCE",
     "playlists":["course_2026","practice"],"category":"course","domain":"D1","transcript_chars":68982}
  ],
  "by_category": {"course":[...8 ids...],"mindmap":[...],"practice":[...],"other":[...]},
  "domain_chapters": {"D1":{"video_id":"...","chapters":[]}, ...}
}
```
- **`category` 依影片內容判定**（course / mindmap / practice / other），與它出現在哪個 playlist 無關。
- 每支影片有 `domain`（D1–D8 或 null）。**course / mindmap / practice 三類都已涵蓋全部 8 個 Domain**。
- 字幕在 `transcripts/<video_id>.txt`（純文字）；8 支 course 影片另有帶時間碼字幕 `transcripts/_timed/<video_id>.vtt`。
- 少數影片 `transcript_chars` 為 0（無字幕）或歸 other——略過即可。

**怎麼選影片與對齊字幕（每封固定放兩支）**（呼應第三節第 8 點與「內容來源原則」）：
- **① 重點短片（主要、用於對齊）**：在 `category=="mindmap"` 且 `domain==該Domain` 的短片中，挑**標題/主題與本單元最相符**的一支（例如 D5 存取控制單元 → 「Access Control MindMap | Domain 5」或「Domain 5 Review (1 of 2) | Access Control」）。用其 `transcripts/<id>.txt` 對齊教材，並當作信裡的第一個影片連結。
- **② 完整課程（保留）**：該 Domain 的 `category=="course"` 完整影片，當第二個連結；其 `_timed/<id>.vtt` 可帶近似 `?t=` 時間碼。
- **後期 P3 額外**：再附 `category=="practice"` 該 Domain 考題影片（刷題）。
- ①對不到夠精準的短片時，退回 course 影片或對應 playlist。

**影片時間軸（用於 course「完整版」次要連結，近似定位）**：course 影片**沒有章節**（`chapters` 皆為空）。若要在「完整版」連結帶上時間碼，就用 `transcripts/_timed/<id>.vtt` 搜尋當天主題英文關鍵字首次出現的時間碼，組成 `https://youtu.be/<id>?t=<秒數>`、標「完整版・從約 mm:ss」。定位不到就連完整影片開頭。**主要連結用的短片本身已聚焦單一主題，不需時間軸。**

**僅當 `video_index.json` 或 `transcripts/` 不存在時**（尚未 commit）：才退回「影片連結用 `cissp_curriculum.json` 的 `video_resources` playlist URL、教材純大綱生成」，**仍不要自己跑 yt-dlp**。
- 生成各封信時，用 `video_index.json` 把該單元主題對應到**最相符的單支影片**（Domain + 主題關鍵字比對），對不上才用 playlist URL。

---

## 五、排程邏輯（build_schedule.py）

- 讀 `cissp_curriculum.json`，依 `seq` 順序，從一個**起始日期**（檔頂變數，預設下一個工作日）開始，**只排週一至週五，跳過週六日**，每個工作日對應一個單元。
- 120 個工作日 ≈ 24 週。產生 `schedule.json`：

```json
{
  "start_date": "2026-06-25",
  "timezone": "Asia/Taipei",
  "weekdays_only": true,
  "items": [
    {
      "date": "2026-06-25", "seq": 1, "phase": "P1", "phase_name_zh": "初期：章節輪廓",
      "domain": "D1", "domain_name_zh": "安全與風險管理", "weight": "16%",
      "code": "P1-D1-1", "title_zh": "Domain 1 全景與 CIA 鐵三角",
      "title_en": "Domain 1 Big Picture & the CIA Triad",
      "email_file": "emails/day-001.html", "archive_url": "archive/day-001.html",
      "video_url": "https://youtu.be/J-su239XmCE"
    }
  ]
}
```

- `video_url` 依該單元的 `phase` 決定要放哪個系列的連結（初期=該 Domain 完整影片；中期=MindMap 清單；後期=考題清單）。
- 跑完把 `schedule.json` 複製一份到 `docs/schedule.json`。
- **可重跑**：改起始日期或之後要排「第二輪」時能重新生成（用 seq 疊代，別寫死）。

---

## 六、寄信程式（send_daily.py）

1. 讀 `docs/schedule.json`，用**台灣時區 (UTC+8)** 的今天日期，找今天要寄的單元；**若今天是週末或不在排程內，正常結束、不報錯**。
2. 讀對應的 `emails/day-XXX.html`。
2b. **合併今日時事**：檢查 `news/day-XXX-news.html` 是否存在（由當天的時事 Routine 產生）。若存在，將其內容填入教材 HTML 的 `<!-- TODAY_NEWS -->` 占位處；若不存在（Routine 當天失敗或還沒跑），就移除占位標記、照常只寄教材本文（優雅降級，不報錯）。
3. 用 **Gmail SMTP（smtp.gmail.com:587, STARTTLS）+ `smtplib`** 寄出，認證用環境變數 `GMAIL_USER`、`GMAIL_APP_PASSWORD`、`RECIPIENT_EMAIL`（從 GitHub Secrets 注入），**不用任何付費 API**。
   - 主旨：`【CISSP W3 初期·D1】P1-D1-1 Domain 1 全景與 CIA 鐵三角`（含階段與代碼）。
   - 寄 `multipart/alternative`，HTML 為主、附純文字 fallback。
4. 寄成功後更新 `sent_log.json`（不存在就建立）：`{seq, date, code, phase, title_zh, sent_at_utc, status:"sent"}`，並複製一份到 `docs/sent_log.json`。
5. 基本錯誤處理與 log 輸出，方便在 Actions 介面排查。

---

## 七、每日 Workflow（.github/workflows/daily.yml）

- 用 `schedule:` cron。我要**台灣平日早上 7 點**收信。台北 07:00 = 前一天 UTC 23:00；台北週一～週五對應 UTC 週日～週四。故設 `cron: '0 23 * * 0-4'`。另加 `workflow_dispatch:` 供手動測試。
- 步驟：checkout（需寫回權限）→ setup Python → 跑 `scripts/send_daily.py`（3 個 Secrets 用 `env:` 注入）→ 把 `sent_log.json`、`docs/sent_log.json` commit & push 回去。
- **權限**：頂層加
  ```yaml
  permissions:
    contents: write
  ```
  用內建 `GITHUB_TOKEN` push，不需額外 PAT。
- **避免無限迴圈**：commit message 加 `[skip ci]`；本 workflow 只由 `schedule`/`workflow_dispatch` 觸發，不要由 push 觸發。commit 前先檢查有無變更，避免無變更時失敗。
- send_daily.py 自身也會再判斷一次「今天是否為排程日」，與 cron 形成雙重保險（也能處理放假/暫停）。
- **與時事 Routine 的時序**：時事 Routine（見附錄）需排在這個寄信 workflow **之前**完成，例如 Routine 設台北 06:30、寄信 workflow 設台北 07:00（`0 23 * * 0-4`）。Routine 把 `news/day-XXX-news.html` commit 進 repo，寄信 workflow 再 checkout 到最新、合併寄出。若 Routine 當天沒跑成，寄信照常只寄教材本文。

---

## 八、追蹤網頁（docs/index.html，部署於 GitHub Pages）

純靜態**單檔** `docs/index.html`（內嵌 CSS/JS，盡量不依賴外部框架以免離線壞掉）：

- 載入時 `fetch('schedule.json')` 與 `fetch('sent_log.json')`。
- **表格 / 快速索引**：每列一單元，欄位 — Seq、日期、**階段**（初/中/後，用顏色標籤）、Domain（顏色標籤）、代碼、中文標題、**寄送狀態**（已寄 ✅ / 未寄 ⬜）、**連結**（點開 `archive/day-XXX.html` 重看）。
- 上方提供：**階段篩選**（初期/中期/後期/全部）、**Domain 篩選**（8 個 + 全部）、**進度條**（已寄 X / 120）、**搜尋框**（中英標題）。
- 行動裝置友善（我常用手機）。視覺乾淨專業。
- 另把 120 封輸出網頁版到 `docs/archive/day-XXX.html`，每頁頂部有「← 回索引」。

---

## 九、執行順序

1. 讀 `cissp_curriculum.json`，確認 120 個單元、3 個 phase、8 個 domain 都讀到。
2. 讀 `video_index.json` 與 `transcripts/`（**我已預先 commit，不要自己跑 yt-dlp / 連 YouTube**），確認影片分類與字幕可用；若不存在才退回 playlist URL / 純大綱備援。
3. 寫 `build_schedule.py` 並執行 → 產生 `schedule.json`（+ 複製到 `docs/`）。
4. **批次生成 120 封 `emails/day-XXX.html`**：請**分階段、分 Domain 進行**（先做 P1-D1 那 5 封 → 給我看樣本 → 確認風格後再全量）。注意三個階段的深度差異；用 `video_index.json` 對應具體影片；依「內容來源原則」參照 `transcripts/` 對齊影片；**每封本文末加 `<!-- TODAY_NEWS -->` 占位標記**。
5. 建立空的 `news/` 目錄（放 `.gitkeep`），供每日時事 Routine 寫入。
6. 由 emails 產生 `docs/archive/day-XXX.html` 網頁版。
7. 寫 `send_daily.py`（含今日時事合併邏輯）、`daily.yml`、`docs/index.html`、`README.md`。
8. 給我一份**待辦清單**：要設哪些 Secrets、開哪些權限、如何開 Pages、如何手動觸發測試、以及如何設定附錄的時事 Routine。

---

## 十、限制與注意

- **成本（混合架構）**：教材寄送執行路徑零 pay-per-use API（純 SMTP + Actions 內建能力，內容是預生成靜態檔）；只有「今日時事」那一小段由每日 Routine 產生，消耗少量 Max 訂閱額度（非 API 計費）。
- **內容正確性**：CISSP 名詞與條文要準確，沒把握就標註讓我查證，不要編造。
- **Gmail 寄信限制**：個人 Gmail 每日寄送有上限（遠高於一天一封，不影響本用途），README 提醒我。
- **先 MVP 再擴充**：可先把「排程 + 寄信 + 1 封樣本 + workflow + 追蹤頁骨架」端到端打通，再回頭全量生成 120 封。
- 先**確認計畫**再動工；若有更好的結構建議，先告訴我。

---

## 附錄：每日「今日時事」Routine（混合架構的時事來源）

這部分**由我（使用者）在 claude.ai/code/routines 設定一個 Claude Code Routine**，不是 repo 裡的程式。它負責每天產生「今日時事延伸」一小段、commit 進 repo，讓寄信 workflow 合併進當天教材一起寄出。

**設定要點**
- **排程**：每個平日，台北時間約 06:30（早於寄信 workflow 的 07:00）。
- **指定 repo**：選 `cissp` repo（Routine 會 clone 它）。
- **分支推送權限**：在該 routine 的 Permissions 開啟「Allow unrestricted branch pushes」，讓它能把 `news/` 檔案直接 commit 回主分支（否則它只會推到 `claude/` 前綴分支、寄信 workflow 讀不到）。
- **網路**：環境網路要允許 web 搜尋/讀新聞來源（預設環境會擋大部分外部網路，需放寬到可查新聞）。
- **連接器**：用不到 Gmail 連接器（寄信交給既有 SMTP workflow）；可把不需要的連接器移除，降低風險。

**Routine 的 prompt（貼這個）**
> 你在 `cissp` repo 的 cloud session 中。步驟：
> 1. 讀 `docs/schedule.json`，用台灣時區今天的日期，找出今天對應的 CISSP 單元（取其 `domain_name_zh`、`title_zh`、`code`、`seq`）。若今天是週末或不在排程內，直接結束、不要產出。
> 2. 針對該單元主題，web 搜尋「最近 7 天」內相關的真實資安新聞/事件（2–3 則）。
> 3. 用繁體中文寫一段「🗞️ 今日時事延伸」HTML 區塊（約 3 點），每點：一句話新聞重點 + 一句話如何對照／呼應今天的 CISSP 概念。英文術語並列。簡潔、約 200–350 字。
> 4. 把這段 HTML 存成 `news/day-XXX-news.html`（XXX 為今天的 `seq`，補零三位），commit 並 push 到主分支。commit message 加 `[skip ci]`。
> 5. 若搜尋不到相關新聞，就寫一段「本主題近期無顯著新聞，補充一個經典案例的簡短延伸」當替代，一樣存檔 commit。

**運作流程**：Routine（06:30）產時事並 commit → 寄信 workflow（07:00）checkout 最新、把時事合併進當天教材的 `<!-- TODAY_NEWS -->`、SMTP 寄出 → 回寫 `sent_log.json`。教材永遠會寄；時事是「有就附上、沒有不影響」。

這樣：教材核心評審過、固定、零成本；時事每天新、寫進同一封信；每天只為「時事那一小段」消耗少量 Max 額度；寄信仍走最穩的 SMTP。
