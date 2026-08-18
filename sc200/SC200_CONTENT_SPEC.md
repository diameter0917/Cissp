# SC200_CONTENT_SPEC.md — SC-200 內容規格書

> 所有電子報、Podcast 腳本、題庫的**一致性契約**。任何內容批次（W1–W5、刷題階段）
> 都必須遵守本文件，避免 25 封信、25 集腳本、585 題在多批次生成間漂移。
> （角色等同 CISSP 專案的 `CLAUDE_CODE_PROMPT.md`。）

## 0. 內容主軸與準確性護欄

1. **影片為主軸**：每個學習單元以 `video_eps` 指定的官方影片（EP1–EP10）為主。
   `sc200/transcripts/` 有字幕時，「影片伴讀」章節必須依字幕實際內容整理（含時間碼）；
   還沒有字幕時，伴讀章節寫成「觀看重點指引」（告訴讀者看什麼），並在字幕到位後回補。
2. **考綱為底線**：內容錨定官方 study guide（2026-07-28 版）三大領域。影片沒講到的
   考綱項目，一律放進「考綱補洞」章節，不可遺漏。
3. **UI 措辭以能力為主**：入口網站的按鈕路徑常改版，描述以「能做什麼／在哪一類設定」
   為主，避免逐步點擊路徑寫死。
4. **連結一律 `https://learn.microsoft.com/zh-tw/...`**。本開發環境無法驗證連結，
   路徑用穩定的文件 slug（azure/sentinel、defender-endpoint、defender-xdr、
   defender-office-365、defender-for-identity、defender-for-cloud、security-copilot），
   收尾時提醒使用者抽查。
5. **2026 新考點**（內嵌 Security Copilot／agentic AI、Sentinel data lake、KQL jobs、
   summary rules、Sentinel Graph、Sentinel MCP Server）：內容標 `<span class="badge-2026">2026 新考點</span>`，
   題目 tags 加 `"2026"`，全題庫占比 ≥10%。

## 1. 語言政策與詞彙表

繁體中文說明＋英文術語並列；產品名、功能名保留英文原文，首次出現時加中文說明。
**固定譯法**（微軟 zh-TW 官方用語，禁止混用其他譯法）：

| 英文 | 繁中固定譯法 |
|---|---|
| workspace | 工作區 |
| data connector | 資料連接器 |
| Data Collection Rule (DCR) | 資料收集規則 |
| analytics rule | 分析規則 |
| automation rule | 自動化規則 |
| playbook | 劇本（Playbook） |
| workbook | 活頁簿（Workbook） |
| hunting | 威脅搜捕／搜捕 |
| incident | 事件 |
| alert | 警示 |
| entity | 實體 |
| watchlist | 監視清單（Watchlist） |
| threat intelligence | 威脅情報 |
| advanced hunting | 進階搜捕 |
| custom detection | 自訂偵測 |
| live response | 即時回應（Live Response） |
| device isolation | 裝置隔離 |
| attack surface reduction (ASR) | 攻擊面縮小（ASR） |
| retention | 保留（期） |
| ingestion | 擷取 |
| bookmark | 書籤 |
| notebook | 筆記本（Notebook） |
| tenant | 租用戶 |
| commitment tier | 承諾層級 |

縮寫慣例：MDE＝Defender for Endpoint、MDO＝Defender for Office 365、
MDI＝Defender for Identity、MDA＝Defender for Cloud Apps、MDTI＝Defender Threat Intelligence、
XDR＝Defender XDR。每封信第一次出現時用全名＋縮寫。

## 2. 電子報章節契約（`sc200/content/day-NNN.html`）

只寫**本文片段**（不含 `<html>`／報頭／自測／Podcast 框——由 `build_site.py` 包裝）。
目標 3,000–4,000 繁中字。章節依序：

1. `01 — 📌 本日導讀`（`<h2 data-toc="導讀">`）：150–250 字＋學習目標 checklist，
   每項對應官方考綱條目（引用考綱原文措辭）。
2. `02 — 📺 影片伴讀`（`data-toc="影片伴讀"`）：依影片章節分段整理重點；
   有字幕時附時間碼（格式 `EP4 12:35`，用 `.timestamp` 樣式）；無字幕時寫觀看指引。
3. `03..NN — 核心概念` 3–5 節（各有 `data-toc`）：表格、比較矩陣、`.point` 重點框、
   `.case-box` 實戰情境（SOC walkthrough：警示→分診→調查→回應）、`.exam-box` 考點聚焦
   （每封 ≥2 個，含「選最佳答案」思路與陷阱）。
4. `kql_focus: true` 的單元：**必備** `<pre class="kql">` 程式碼區塊 2–4 段＋逐行中文解說
   （`.kql-note`）。非 KQL 單元有相關查詢時也鼓勵放。
5. 倒數第二節 `NN — 🧩 考綱補洞`（`data-toc="考綱補洞"`）：影片未涵蓋的考綱項目補講；
   若影片已全涵蓋，改寫「考綱對照確認」清單。
6. 最後一節 `NN — 📚 延伸閱讀`（`data-toc="延伸閱讀"`）：3–5 條 MS Learn zh-TW 深連結
   （`<ul>`，每條附一句「讀什麼」）。

規範：eyebrow 編號 `01 —` 起連續；`data-toc` 標籤 ≤6 字；表格包 `.tbl-scroll`；
不用外部圖片／SVG／CDN。

## 3. Podcast 腳本契約（`sc200/podcast/scripts/ep-NNN.json`）

```json
{
  "episode": 7, "unit": "P1-W2-2", "title_zh": "資料連接器 I",
  "dialogue": [
    {"speaker": "host_f", "text": "..."},
    {"speaker": "host_m", "text": "..."}
  ]
}
```

- **角色**（固定人設）：
  - `host_f` 曉臻（zh-TW-HsiaoChenNeural）＝引導者：開場、提問、幫聽眾追問
    「為什麼」「跟昨天講的差在哪」、每段小結、收尾預告。
  - `host_m` 雲哲（zh-TW-YunJheNeural）＝專家：技術解釋、實戰經驗、考點提醒。
- **結構**：冷開場（兩句寒暄＋預告本日主題）→ 本日三重點 → 主體對談（跟著影片
  章節走）→ 考點快問快答（曉臻出 3 題口頭是非/選擇，雲哲答＋解釋）→ 收尾（明天預告）。
- **量**：30–60 turn，每 turn 1–3 句；總字數 2,200–2,800（≈9–11 分鐘）。
- **口語化**：用「你」稱呼聽眾；英文術語直接唸（edge-tts 可正常唸英文）；
  避免長串子句；數字與縮寫寫成口語（「四十趴」寫「40%」即可，TTS 會唸對）。
- **發音替換表**（由 `gen_podcast.py` 在 TTS 前套用，顯示文字不變）：
  `KQL→K Q L`、`XDR→X D R`、`SIEM→SIM`、`SOAR→SORE`、`MDE→M D E`、`MDO→M D O`、
  `MDI→M D I`、`SCU→S C U`、`DCR→D C R`、`ASIM→A SIM`、`UEBA→U E B A`、
  `NRT→N R T`、`ATT&CK→attack`、`IoC→I O C`。

## 4. 題庫撰寫規則（`sc200/bank/*.json`）

Schema 見 `validate_questions.py`。撰寫規則：

1. **情境先行**：題幹以 SOC 場景開頭（You are a security operations analyst...），
   問「應該用什麼／下一步做什麼／最佳做法」，仿真實考試的 best-answer 風格。
2. **干擾項同類**：錯誤選項必須是同領域的真實功能（如問 DCR 時干擾項用
   watchlist／summary rule／ASIM），不可用明顯無關的選項。
3. **why_wrong_zh 每個錯項都要**：說明「它是做什麼的、為何不是本題答案」。
4. **難度**：1＝定義層（記憶）、2＝應用層（選工具/流程）、3＝分析層（多條件取捨）。
   分布約 25%／55%／20%。
5. **答案字母打散**：單選正解平均分布 A–D（驗證器門檻：單檔任一字母 ≤32%）。
6. **id 規則**：`D1-0001`…（practice）、`M1-0001`…（mock）。`unit` 標籤：每學習單元
   恰好 5 題（合計 125 題）同時作為該單元電子報自測題。`set`：practice 檔內
   A/B 各半（D3 為 A 40／B 30、多的进 A）。
7. **multi 題**：占比約 10%，題幹註明（Select all that apply.）。
8. **模擬考**（mock-01/02/03）：各 55 題、固定順序、D1 24／D2 21／D3 10，
   與 practice 題幹不重複（驗證器有近重複偵測）。

## 5. 批次流程（每週一批）

1. 寫 5 個 `content/day-NNN.html`＋5 個 `podcast/scripts/ep-NNN.json`＋該週 ~84 題
   （5×5 unit 題＋domain 題組份額）。
2. `python3 sc200/scripts/validate_questions.py`＋`python3 sc200/scripts/build_site.py --check` 全綠。
3. commit `content(sc200): week N — ...` 並 push——push 會自動觸發
   `sc200-podcast.yml` 合成該週音檔（commit 回分支，記得先 pull 再繼續下一批）。

## 6. 本機字幕抓取（Actions 被 YouTube 擋時的路徑 B）

在能連 YouTube 的電腦上執行一次：

```bash
python -m pip install -U yt-dlp
python sc200/scripts/fetch_transcripts.py
git add sc200/transcripts && git commit -m "chore(sc200): fetch transcripts locally [skip ci]" && git push
```

（與 CISSP 專案 `prepare_youtube.py` 的做法相同；已抓過的 EP 會自動略過。）
