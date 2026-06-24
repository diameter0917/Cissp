# CISSP 每日電子報系統（螺旋式三階段）

全自動的 CISSP 每日學習電子報：平日（週一至週五）早上 7 點（台灣時間）透過 GitHub Actions + Gmail SMTP 自動寄一封繁中說明、英文術語並列的 CISSP 教材到信箱；半年內依螺旋式三階段（初期輪廓 → 中期細節 → 後期考點）走完 8 大 Domain、共 **120 封**。

教材是**預生成的靜態 HTML**（零 pay-per-use API、寄送免費）；每天另由一個輕量 Claude Routine 產生「今日時事延伸」一小段，寄信時合併進同一封信（有就附上、沒有不影響）。

---

## 目前進度

| 項目 | 狀態 |
|---|---|
| 排程系統 `build_schedule.py` → `schedule.json` | ✅ 完成（120 單元，起始 2026-06-25） |
| `video_index.json`（8 支 course 影片 + 字幕） | ✅ 完成（mindmap/practice 走 playlist 備援） |
| 寄信程式 `send_daily.py`（含今日時事合併、優雅降級） | ✅ 完成 |
| 網頁版產生器 `build_archive.py` | ✅ 完成 |
| 追蹤頁 `docs/index.html`（篩選/搜尋/進度） | ✅ 完成 |
| GitHub Actions `daily.yml`（平日 cron + 手動觸發） | ✅ 完成 |
| 教材信件 `emails/day-XXX.html` | 🟡 **已生成 P1-D1 樣本（day-001～005）**；其餘 115 封待生成 |

> **day-001** 採用 `templates/sample_day-001.html` 作為全系統版型基準；day-002～005 依同一設計系統生成。

---

## 檔案結構

```
cissp/
├── cissp_curriculum.json          # 課綱資料來源（120 單元 / 3 階段 / 8 Domain）
├── templates/sample_day-001.html  # 風格範本（所有信件版型基準）
├── video_index.json               # 影片索引（8 支 course 影片，由 build_video_index.py 產生）
├── transcripts/                   # 影片字幕（<id>.txt；對齊/延伸參考用）
├── emails/day-XXX.html            # 預生成電子報（inline CSS，寄信用）
├── news/                          # 每日 Routine 寫入 day-XXX-news.html（今日時事）
├── schedule.json                  # 日期→單元（build_schedule.py 產生）
├── sent_log.json                  # 寄送狀態（workflow 自動回寫）
├── scripts/
│   ├── build_schedule.py          # 由 curriculum 產生 schedule.json（跳過週末）
│   ├── build_video_index.py       # 由 transcripts 產生 video_index.json
│   ├── build_archive.py           # 由 emails 產生 docs/archive 網頁版
│   └── send_daily.py              # 挑當天單元、合併時事、SMTP 寄出、回寫 log
├── docs/                          # GitHub Pages 根
│   ├── index.html                 # 追蹤頁（表格/篩選/進度/搜尋）
│   ├── archive/day-XXX.html       # 歷史信件網頁版（可點開重看）
│   ├── schedule.json              # schedule.json 副本（追蹤頁/Routine 讀取）
│   └── sent_log.json              # sent_log.json 副本
└── .github/workflows/daily.yml    # 每日（平日）排程 workflow
```

---

## 設定待辦清單（你要做的事）

### A. GitHub 端

1. 把本 repo 設為 **public**（GitHub Pages 免費版 + Routine 要讀公開 `schedule.json`）。
2. Gmail 開啟兩步驟驗證 → 產生**應用程式密碼（App Password）**。
3. 在 repo 設三個 Secrets（**Settings → Secrets and variables → Actions → New repository secret**）：
   - `GMAIL_USER` — 寄件 Gmail（如 `you@gmail.com`）
   - `GMAIL_APP_PASSWORD` — 剛產生的 16 碼應用程式密碼（**不是**你的 Gmail 登入密碼）
   - `RECIPIENT_EMAIL` — 你要收信的信箱
4. **Settings → Actions → General → Workflow permissions** → 選 **Read and write permissions**（讓 workflow 能 push 回 `sent_log.json`）。

### B. 開啟 GitHub Pages（追蹤頁）

5. **Settings → Pages → Build and deployment → Source** 選 **Deploy from a branch**，分支選主分支、資料夾選 **`/docs`**，存檔。
   稍候即可在 `https://<帳號>.github.io/<repo>/` 看到追蹤頁。

### C. 手動測試寄信

6. **Actions → CISSP Daily Newsletter → Run workflow**：
   - `send_date` 填一個排程內的平日（例：`2026-06-25` 對應 day-001），或留空用今天。
   - `dry_run` 填 `1` 可只測流程不真的寄信；填 `0`（或留空）會實際寄出。
   - 跑完到信箱確認收到、並看 `docs/index.html` 該封是否變「✅ 已寄」。

### D. 設定每日「今日時事」Routine（選用，混合架構的時事來源）

7. 在 **claude.ai/code/routines** 建立一個 Claude Code Routine：
   - **指定 repo**：本 `cissp` repo。
   - **排程**：每個平日，台北約 **06:30**（早於寄信 workflow 的 07:00）。
   - **Permissions**：開啟「**Allow unrestricted branch pushes**」，讓它能把 `news/` 檔 commit 回主分支。
   - **網路**：放寬到可 web 搜尋/讀新聞來源。
   - **Prompt**：見本 repo `CLAUDE_CODE_PROMPT.md` 附錄（讀 `docs/schedule.json` 找今天單元 → 搜尋近 7 天相關資安新聞 → 寫成 `news/day-XXX-news.html` → commit 加 `[skip ci]`）。
   - 時事檔的 HTML 會被 `send_daily.py` 填入教材的 `<!-- TODAY_NEWS -->` 占位處；當天沒跑成也不影響教材照常寄出。

---

## 排程與寄送邏輯

- **`build_schedule.py`**：依 `cissp_curriculum.json` 的 `seq` 順序，從起始日起只排週一至週五（跳過週末），120 個工作日 ≈ 24 週。
  - 重新排程：`python scripts/build_schedule.py 2026-06-25`（給日期）或不給參數（預設下一個工作日）。可重跑、可排第二輪。
- **`send_daily.py`**：用台灣時區今天日期找單元；週末或非排程日**正常結束不報錯**（與 cron 雙重保險）。寄 `multipart/alternative`（HTML + 純文字 fallback）。主旨格式：`【CISSP W1 初期·D1】P1-D1-1 Domain 1 全景與 CIA 鐵三角`。
- **`daily.yml`**：`cron: '0 23 * * 0-4'`（台北平日 07:00）；另有 `workflow_dispatch` 手動觸發。commit 加 `[skip ci]` 避免迴圈；無變更時略過 commit。

### 本機重建指令

```bash
python scripts/build_video_index.py      # 產生 video_index.json
python scripts/build_schedule.py         # 產生 schedule.json (+ docs 副本)
python scripts/build_archive.py          # 由 emails 產生 docs/archive 網頁版
SEND_DATE=2026-06-25 DRY_RUN=1 python scripts/send_daily.py   # 本機乾跑測試
```

---

## 注意事項

- **內容正確性**：教材由 AI 依官方大綱生成，閱讀時請順手把關；不確定處已盡量標註，未杜撰。
- **Gmail 寄送上限**：個人 Gmail 每日寄送上限遠高於「一天一封」，不影響本用途。
- **影片連結**：初期（P1）連各 Domain 的完整課程影片（已對應 8 支）；中期（P2）/後期（P3）目前因缺逐片標題，連對應 playlist（備援路徑）。若日後補上完整 `video_index.json`，連結會自動更精準。
- **不要在雲端 session 連 YouTube / 跑 yt-dlp**（IP 會被擋）；影片資料用本機 `prepare_youtube.py` 跑好再 commit。
