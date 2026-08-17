# 在自己的電腦抓官方影片字幕（完整步驟）

> **為什麼要在自己電腦跑？**
> YouTube 對雲端／資料中心 IP（GitHub Actions runner、Claude 的雲端環境）有 bot 偵測，
> 會回「Sign in to confirm you're not a bot」而抓不到字幕。從**家用網路**執行就沒這個問題。
> 這是 CISSP 專案當初也走過的同一條路（`prepare_youtube.py`）。
>
> **抓回來的字幕做什麼用？** 抓完 commit 上來之後，教材產製會用它做三件事：
> ① 電子報「影片伴讀」章節補上**時間碼定位**（幾分幾秒講到哪個主題，方便跳看）；
> ② 用 `check_coverage.py` 比對**影片講了但教材沒寫**的缺口，逐一補進教材；
> ③ 比對**電子報寫了但 Podcast 沒講**的主題，補進對談腳本。
> 詳見本文最後一節。

全程約 **10–20 分鐘**（大部分是等下載）。

---

## 步驟 0：確認有 Python

打開終端機：

- **Windows**：按 `Win` 鍵 → 輸入「PowerShell」→ 開啟 **Windows PowerShell**
- **macOS**：按 `Cmd + 空白鍵` → 輸入「終端機」或「Terminal」→ Enter
- **Linux**：開你慣用的終端機

輸入這行後按 Enter：

```bash
python3 --version
```

- 出現 `Python 3.9.x` 以上 → ✅ 過關，跳到步驟 1。
- **Windows 若顯示找不到指令**，改試 `python --version`；若仍失敗，到
  <https://www.python.org/downloads/> 下載安裝，**安裝時務必勾選
  「Add Python to PATH」**，裝完關掉 PowerShell 重開再試一次。
- **macOS 若顯示找不到**，執行 `xcode-select --install` 安裝開發者工具（內含 Python 3）。

> 之後的指令，Windows 使用者若 `python3` 無效，一律把 `python3` 換成 `python`。

---

## 步驟 1：安裝 yt-dlp

```bash
python3 -m pip install -U yt-dlp
```

- `-U` 是「有裝就升級」。**yt-dlp 一定要用最新版**——YouTube 常改反爬機制，
  舊版會抓不到。之後若某天抓失敗，第一件事就是重跑這行升級。
- 看到 `Successfully installed yt-dlp-...` 即完成。
- 若出現權限錯誤（Permission denied），改用：
  `python3 -m pip install -U --user yt-dlp`

驗證安裝：

```bash
python3 -m yt_dlp --version
```

會印出像 `2026.08.xx` 的版本號。

---

## 步驟 2：把 repo 抓到本機

**如果你電腦上還沒有這個 repo**：

```bash
git clone https://github.com/diameter0917/Cissp.git
cd Cissp
git checkout claude/sc-200-study-project-dyje4p
```

**如果已經有了**（進到該資料夾後）：

```bash
cd 你的/Cissp/資料夾路徑
git checkout claude/sc-200-study-project-dyje4p
git pull origin claude/sc-200-study-project-dyje4p
```

> ⚠️ 分支名稱一定要是 `claude/sc-200-study-project-dyje4p`（SC-200 專案的開發分支）。
> 確認方式：`git branch --show-current`

---

## 步驟 3：執行抓取腳本

```bash
python3 sc200/scripts/fetch_transcripts.py
```

**過程中你會看到**（每支影片一段）：

```
yt-dlp 版本: 2026.08.xx

[EP1] https://youtu.be/8gCUtYEpTe8
    《Mitigate threats using Microsoft Defender XDR | SC-200 | Episode 1》 1:02:33，章節 14 個
    字幕： en 45,231 字、zh-Hant 38,102 字

[EP2] https://youtu.be/QmvVYOG4uWI
    ...
```

- 全部 10 支跑完約 **5–15 分鐘**（影片很長，字幕檔不小）。
- **中途可以按 `Ctrl + C` 中斷**，之後重跑會自動跳過已抓好的，接著抓沒抓完的。
- 已經抓過的會顯示「略過（已存在）」；要全部重抓才加 `--force`。

**成功的標準**：最後一行出現

```
✅ 完成：10/10 支有字幕。結果見 sc200/transcripts/index.json
```

### 抓下來的東西

| 檔案 | 內容 |
|---|---|
| `sc200/transcripts/ep-NN.info.json` | 影片標題、長度、**章節清單（含起始秒數）** |
| `sc200/transcripts/ep-NN.en.txt` | 英文字幕純文字（教材對齊用） |
| `sc200/transcripts/ep-NN.zh-Hant.txt` | **YouTube 自動翻譯的繁中字幕**純文字 |
| `sc200/transcripts/_timed/ep-NN.*.vtt` | 帶時間碼的字幕（電子報時間碼定位用） |
| `sc200/transcripts/index.json` | 十支影片的抓取狀態總表 |

---

## 步驟 4：commit 並推回 GitHub

```bash
git add sc200/transcripts
git commit -m "chore(sc200): fetch video transcripts locally [skip ci]"
git push origin claude/sc-200-study-project-dyje4p
```

> `[skip ci]` 是為了不觸發不必要的 CI。
>
> 字幕檔加起來大約 **2–5 MB**，直接進 git 沒問題（CISSP 專案已有 91 份字幕的前例）。

推完之後告訴我一聲，我就會接著做「步驟 6」的教材補強。

---

## 步驟 5（可選）：自己先看覆蓋度報告

字幕到位後，本機就能跑覆蓋度比對：

```bash
python3 sc200/scripts/check_coverage.py
```

會產生 `sc200/coverage_report.md`，逐個單元列出：

- 🔴 **要補教材**：影片講了、電子報沒寫的主題
- 🟡 **要補音檔**：電子報寫了、Podcast 沒講的主題
- 🔵 **自主補強**：電子報寫了、影片沒講 → 應該落在「考綱補洞」章節（刻意的）
- 🔍 **字幕高頻片語**：詞典沒收錄但影片一直提的詞（可能是新功能／改名）

只看某幾天：`python3 sc200/scripts/check_coverage.py 7 8 9`

---

## 步驟 6：字幕回饋進教材（我來做）

你 push 完字幕後，我會依序處理：

1. **回填時間碼**：由 `ep-NN.info.json` 的章節與 `_timed/*.vtt`，把各單元對應的影片段落
   （起訖秒數）寫進 `sc200_curriculum.json` 的 `video_segments`，電子報的「影片伴讀」
   就會出現可點的 `12:35` 時間碼跳看連結。
2. **補教材缺口**：跑 `check_coverage.py`，把 🔴 項目逐一補進對應電子報的核心章節；
   確認 🔵 項目確實寫在「考綱補洞」章節裡（那是刻意超出影片、補足官方考綱的部分）。
3. **補 Podcast**：把 🟡 項目補進對談腳本，push 後 GitHub Actions 會自動重新合成該集音檔
   （腳本 sha256 有變才重做，沒改的集數不會重跑）。
4. **校準課綱**：若影片實際內容與單元規劃有出入（例如某主題在別集才講），調整
   `video_eps` 對應並在報告中說明。

---

## 疑難排解

| 症狀 | 原因與解法 |
|---|---|
| **`HTTP Error 429: Too Many Requests`** | **最常見**。不是被封鎖，是短時間請求太多被限流。腳本已內建退避重試（60→180→420 秒），若仍失敗：① 隔 10–30 分鐘再跑一次（已抓好的會自動略過、只續抓沒抓到的）；② 改用慢速模式 `python3 sc200/scripts/fetch_transcripts.py --slow`；③ 一次只抓幾支 `--only EP1 EP2 EP3`，分批進行；④ 加瀏覽器 cookies（見下一列）大幅提高額度 |
| `This video is DRM protected` / `Requested format is not available` | 舊版腳本切換 player client 造成的誤導訊息，**已修正**。請 `git pull` 取得最新版腳本後重跑 |
| `Sign in to confirm you're not a bot` | IP 被判定為機器人。① `python3 -m pip install -U yt-dlp` 升級；② 換網路（手機熱點）；③ 用瀏覽器 cookies：先在瀏覽器登入 YouTube，然後 `python3 sc200/scripts/fetch_transcripts.py --cookies-from-browser chrome`（可換 `edge`／`firefox`；Windows 用 Edge 通常最順） |
| `找不到 yt-dlp` | 沒裝或裝到別的 Python。重跑步驟 1，並確認用同一個 `python3` |
| 某幾支顯示「⚠️ 無字幕」 | 該影片可能真的沒開自動字幕。其餘照常可用，不影響流程 |
| 只拿到 `en` 沒有 `zh-Hant` | YouTube 的自動翻譯軌偶爾不供給。英文字幕已足夠做教材對齊與覆蓋度比對 |
| `git push` 要求帳密 | GitHub 已不接受密碼。用 [Personal Access Token](https://github.com/settings/tokens) 當密碼，或改用 SSH／GitHub Desktop |
| 下載很慢 | 正常，字幕檔大且有禮貌性延遲（腳本內建 `--sleep-requests`，避免被鎖）。放著跑即可 |
| 想確認抓到什麼 | `python3 -c "import json;print(json.load(open('sc200/transcripts/index.json'))['episodes'])"` |

---

## 十支影片對照表

| EP | 主題 | 對應學習單元 |
|---|---|---|
| EP1 | Mitigate threats using Microsoft Defender XDR | Day 1、4、12、14、15、21 |
| EP2 | Mitigate threats using Microsoft Security Copilot | Day 11、20 |
| EP3 | Mitigate threats using Microsoft Purview | Day 20 |
| EP4 | Mitigate threats using Microsoft Defender for Endpoint | Day 5、13 |
| EP5 | Mitigate threats using Microsoft Defender for Cloud | Day 16 |
| EP6 | Create queries in Microsoft Sentinel using KQL | Day 2、3 |
| EP7 | Configure Microsoft Sentinel environment | Day 6、9、10 |
| EP8 | Connect logs to Microsoft Sentinel | Day 7、8 |
| EP9 | Create detections and perform investigations in Sentinel | Day 17、18、19、25 |
| EP10 | Perform threat hunting in Microsoft Sentinel | Day 21–25 |
