# 字幕 × 教材覆蓋度報告

由 `sc200/scripts/check_coverage.py` 產生。**以影片為單位**比對——每支 EP 是一整條
學習路徑、橫跨數個單元，故「教材是否涵蓋」須把該影片對應的所有單元合起來看。

- 🔴 **真缺口**：影片講了、全課程都沒寫 → 必須補進最相關那一課
- 🟠 **對應錯位**：影片在此講、教材寫在別課 → 確認編排是否要調整（資訊性）
- 🟡 **要補音檔**：該課電子報實質著墨、Podcast 沒講 → 補進對談腳本
- 🔵 **自主補強**：電子報寫了、影片沒講 → 應落在「考綱補洞」章節（刻意的，確認即可）

## EP1｜Mitigate threats using Microsoft Defender XDR | SC-200 | Episode 1

對應單元：Day 001、Day 004、Day 012、Day 014、Day 015、Day 021

> ⚠️ 尚無字幕文字，略過比對。

## EP2｜Mitigate threats using Microsoft Security Copilot | SC-200 | Episode 2

對應單元：Day 011、Day 020

**影片主題覆蓋率：19/19（100%，全課程口徑）**（字幕語言：en、zh-Hant）

### 🟠 對應錯位（影片在這裡講、教材寫在別課 → 確認編排即可）
- `Defender XDR portal`（字幕 2 次）→ 教材在 Day 001、Day 004、Day 006、Day 009、Day 012、Day 017、Day 019
- `KQL: let`（字幕 3 次）→ 教材在 Day 002、Day 003、Day 009、Day 013、Day 017
- `Log Analytics workspace`（字幕 4 次）→ 教材在 Day 001、Day 002、Day 003、Day 004、Day 006、Day 007、Day 008、Day 009、Day 010、Day 012、Day 016、Day 017、Day 018、Day 019
- `MITRE ATT&CK mapping`（字幕 2 次）→ 教材在 Day 009、Day 012、Day 016、Day 017、Day 018、Day 019
- `incident classification`（字幕 14 次）→ 教材在 Day 005、Day 006、Day 012、Day 013、Day 015、Day 016、Day 018、Day 019
- `indicators (IoC allow/block)`（字幕 7 次）→ 教材在 Day 001、Day 003、Day 005、Day 009、Day 012、Day 013、Day 016、Day 017、Day 018、Day 019
- `lateral movement path`（字幕 2 次）→ 教材在 Day 001、Day 003、Day 004、Day 005、Day 012、Day 013、Day 015

### Day 011 · Security Copilot 設定與管理：SCU、外掛與 Agents
- 🟡 要補音檔：`playbooks (Logic Apps)`、`threat intelligence (TI)`
- 🔵 自主補強（應在考綱補洞）：`KQL: where`、`MDTI`、`automation rules`、`risk-based Conditional Access`

- Day 020 Microsoft Purview 威脅調查與 Copilot 引導式回應：❌ 電子報未撰寫
## EP3｜Mitigate threats using Microsoft Purview | SC-200 | Episode 3

對應單元：Day 020

**影片主題覆蓋率：12/13（92%，全課程口徑）**（字幕語言：en、zh-Hant）

### 🔴 真缺口（影片講了、全課程都沒寫 → 必須補）
- `eDiscovery`（字幕出現 35 次）（Day 020 尚未撰寫，屆時應涵蓋）

### 🟠 對應錯位（影片在這裡講、教材寫在別課 → 確認編排即可）
- `DLP alerts`（字幕 29 次）→ 教材在 Day 001、Day 012
- `Defender for Cloud alerts`（字幕 5 次）→ 教材在 Day 001、Day 002、Day 004、Day 005、Day 007、Day 012、Day 016、Day 017、Day 018
- `KQL: has vs contains`（字幕 2 次）→ 教材在 Day 002、Day 003、Day 008、Day 010、Day 011、Day 016、Day 017
- `KQL: let`（字幕 3 次）→ 教材在 Day 002、Day 003、Day 009、Day 013、Day 017
- `Purview Audit`（字幕 86 次）→ 教材在 Day 001、Day 006、Day 011、Day 012、Day 013、Day 016、Day 018
- `SCU capacity`（字幕 2 次）→ 教材在 Day 011
- `Security Copilot`（字幕 4 次）→ 教材在 Day 001、Day 004、Day 009、Day 011、Day 012、Day 013、Day 014、Day 015、Day 016、Day 017、Day 019
- `data retention / archive`（字幕 15 次）→ 教材在 Day 001、Day 004、Day 006、Day 007、Day 010、Day 018
- `incident classification`（字幕 2 次）→ 教材在 Day 005、Day 006、Day 012、Day 013、Day 015、Day 016、Day 018、Day 019
- `incident vs alert`（字幕 22 次）→ 教材在 Day 001、Day 004、Day 005、Day 006、Day 007、Day 010、Day 011、Day 012、Day 014、Day 016、Day 017、Day 018、Day 019
- `indicators (IoC allow/block)`（字幕 4 次）→ 教材在 Day 001、Day 003、Day 005、Day 009、Day 012、Day 013、Day 016、Day 017、Day 018、Day 019
- `insider risk management`（字幕 28 次）→ 教材在 Day 001

- Day 020 Microsoft Purview 威脅調查與 Copilot 引導式回應：❌ 電子報未撰寫
## EP4｜Mitigate threats using Microsoft Defender for Endpoint | SC-200 | Episode 4

對應單元：Day 005、Day 013

**影片主題覆蓋率：14/14（100%，全課程口徑）**（字幕語言：en）

### 🟠 對應錯位（影片在這裡講、教材寫在別課 → 確認編排即可）
- `Defender for Identity (MDI)`（字幕 2 次）→ 教材在 Day 001、Day 002、Day 004、Day 007、Day 008、Day 010、Day 012、Day 014、Day 015、Day 017、Day 018
- `KQL: join`（字幕 4 次）→ 教材在 Day 002、Day 003、Day 004、Day 006、Day 007、Day 009、Day 010、Day 014、Day 017、Day 018
- `risk-based Conditional Access`（字幕 3 次）→ 教材在 Day 002、Day 011、Day 015

### Day 005 · Defender for Endpoint 部署：上線、裝置群組與進階功能
- 🟡 要補音檔：`device discovery`
- 🔵 自主補強（應在考綱補洞）：`KQL: arg_max`、`KQL: summarize`、`KQL: where`、`advanced hunting`、`automation level`、`playbooks (Logic Apps)`、`tamper protection`、`web content filtering`

### Day 013 · MDE 裝置回應：Live Response、隔離與自動調查
- ✅ Podcast 已涵蓋電子報重點
- 🔵 自主補強（應在考綱補洞）：`Action center`、`CEF`、`KQL: let`、`KQL: summarize`、`KQL: where`、`Security Copilot`、`advanced hunting`、`automation level`、`incident classification`、`lateral movement path`、`restrict app execution`

### 🔍 字幕高頻片語（詞典未收錄，人工判斷是否為新主題）
- Defender for Endpoint×48

## EP5｜Mitigate threats using Microsoft Defender for Cloud | SC-200 | Episode 5

對應單元：Day 016

**影片主題覆蓋率：12/12（100%，全課程口徑）**（字幕語言：en、zh-Hant）

### 🟠 對應錯位（影片在這裡講、教材寫在別課 → 確認編排即可）
- `Data Collection Rule (DCR)`（字幕 6 次）→ 教材在 Day 001、Day 002、Day 007、Day 008、Day 009
- `Threat Explorer`（字幕 2 次）→ 教材在 Day 004、Day 009、Day 014
- `lateral movement path`（字幕 4 次）→ 教材在 Day 001、Day 003、Day 004、Day 005、Day 012、Day 013、Day 015
- `threat intelligence (TI)`（字幕 4 次）→ 教材在 Day 001、Day 006、Day 009、Day 010、Day 011、Day 014、Day 015、Day 017、Day 018、Day 019
- `workbooks`（字幕 2 次）→ 教材在 Day 006、Day 007、Day 008、Day 010

### Day 016 · Defender for Cloud 警示回應：工作負載保護
- ❌ Podcast 腳本未撰寫
- 🔵 自主補強（應在考綱補洞）：`KQL: has vs contains`、`KQL: parse / extract`、`KQL: summarize`、`KQL: where`、`Log Analytics workspace`、`MITRE ATT&CK mapping`、`Security Copilot`、`device isolation`、`playbooks (Logic Apps)`

### 🔍 字幕高頻片語（詞典未收錄，人工判斷是否為新主題）
- Defender for Endpoint×8、Defender for App×4、Defender for Key×3

## EP6｜Create queries in Microsoft Sentinel using Kusto Query Language (KQL) | SC-200 | Episode 6

對應單元：Day 002、Day 003

**影片主題覆蓋率：9/9（100%，全課程口徑）**（字幕語言：en）

### 🟠 對應錯位（影片在這裡講、教材寫在別課 → 確認編排即可）
- `incident vs alert`（字幕 9 次）→ 教材在 Day 001、Day 004、Day 005、Day 006、Day 007、Day 010、Day 011、Day 012、Day 014、Day 016、Day 017、Day 018、Day 019

### Day 002 · KQL 基礎 I：查詢結構、where／project／summarize
- ✅ Podcast 已涵蓋電子報重點
- 🔵 自主補強（應在考綱補洞）：`Data Collection Rule (DCR)`、`Defender for Identity (MDI)`、`KQL jobs`、`KQL: bin()`、`Sentinel data lake`、`advanced hunting`、`custom detection rules`、`hunts`、`ingestion-time transformation`、`summary rules`

### Day 003 · KQL 基礎 II：join／union／parse 與時間序列進階
- 🟡 要補音檔：`KQL: has vs contains`、`KQL: let`、`KQL: make_list / make_set`
- 🔵 自主補強（應在考綱補洞）：`KQL: arg_max`、`KQL: bin()`、`KQL: externaldata`、`KQL: make-series / anomalies`、`KQL: mv-expand`、`Log Analytics workspace`、`NRT rules`、`Sentinel data lake`、`Syslog`、`advanced hunting`、`custom detection rules`、`hunting queries`、`hunts`、`lateral movement path`、`watchlist`

## EP7｜Configure Microsoft Sentinel environment | SC-200 | Episode 7

對應單元：Day 006、Day 009、Day 010

> ⚠️ 尚無字幕文字，略過比對。

## EP8｜Connect logs to Microsoft Sentinel | SC-200 | Episode 8

對應單元：Day 007、Day 008

**影片主題覆蓋率：20/20（100%，全課程口徑）**（字幕語言：en）

### 🟠 對應錯位（影片在這裡講、教材寫在別課 → 確認編排即可）
- `Defender XDR portal`（字幕 2 次）→ 教材在 Day 001、Day 004、Day 006、Day 009、Day 012、Day 017、Day 019
- `Entra ID Protection`（字幕 2 次）→ 教材在 Day 012、Day 015、Day 017、Day 018
- `KQL: let`（字幕 2 次）→ 教材在 Day 002、Day 003、Day 009、Day 013、Day 017
- `MDE onboarding`（字幕 2 次）→ 教材在 Day 005、Day 013、Day 016、Day 017
- `MDTI`（字幕 3 次）→ 教材在 Day 009、Day 011
- `Purview Audit`（字幕 2 次）→ 教材在 Day 001、Day 006、Day 011、Day 012、Day 013、Day 016、Day 018
- `STIX / TAXII`（字幕 2 次）→ 教材在 Day 009
- `indicators (IoC allow/block)`（字幕 17 次）→ 教材在 Day 001、Day 003、Day 005、Day 009、Day 012、Day 013、Day 016、Day 017、Day 018、Day 019
- `notebooks (Jupyter/MSTICPy)`（字幕 2 次）→ 教材在 Day 001、Day 010
- `threat intelligence (TI)`（字幕 23 次）→ 教材在 Day 001、Day 006、Day 009、Day 010、Day 011、Day 014、Day 015、Day 017、Day 018、Day 019

### Day 007 · 資料連接器 I：Content Hub、第一方連接器與 DCR
- 🟡 要補音檔：`Defender for Cloud alerts`、`KQL: parse / extract`、`incident vs alert`
- 🔵 自主補強（應在考綱補洞）：`ASIM / normalization`、`KQL: project / extend`、`Log Analytics workspace`、`Sentinel data lake`、`advanced hunting`、`custom logs / Logs Ingestion API`、`hunting queries`、`hunts`、`ingestion-time transformation`、`summary rules`、`watchlist`

### Day 008 · 資料連接器 II：Syslog／CEF／自訂記錄與 ASIM 正規化
- 🟡 要補音檔：`KQL: parse / extract`、`workbooks`
- 🔵 自主補強（應在考綱補洞）：`ASIM / normalization`、`KQL: has vs contains`、`KQL: make_list / make_set`、`KQL: summarize`、`KQL: where`、`Log Analytics workspace`、`Sentinel data lake`、`custom logs / Logs Ingestion API`、`hunting queries`、`hunts`、`ingestion-time transformation`、`watchlist`

## EP9｜Create detections and perform investigations in Microsoft Sentinel | SC-200 | Episode 9

對應單元：Day 017、Day 018、Day 019、Day 025

> ⚠️ 尚無字幕文字，略過比對。

## EP10｜Perform threat hunting in Microsoft Sentinel | SC-200 | Episode 10

對應單元：Day 021、Day 022、Day 023、Day 024、Day 025

**影片主題覆蓋率：14/15（93%，全課程口徑）**（字幕語言：en）

### 🔴 真缺口（影片講了、全課程都沒寫 → 必須補）
- `livestream`（字幕出現 8 次）（Day 021、Day 022、Day 023、Day 024、Day 025 尚未撰寫，屆時應涵蓋）

### 🟠 對應錯位（影片在這裡講、教材寫在別課 → 確認編排即可）
- `KQL jobs`（字幕 4 次）→ 教材在 Day 001、Day 002、Day 003、Day 008、Day 010
- `KQL: has vs contains`（字幕 2 次）→ 教材在 Day 002、Day 003、Day 008、Day 010、Day 011、Day 016、Day 017
- `MCP server`（字幕 2 次）→ 教材在 Day 001、Day 004
- `MITRE ATT&CK mapping`（字幕 6 次）→ 教材在 Day 009、Day 012、Day 016、Day 017、Day 018、Day 019
- `Security Copilot`（字幕 2 次）→ 教材在 Day 001、Day 004、Day 009、Day 011、Day 012、Day 013、Day 014、Day 015、Day 016、Day 017、Day 019
- `Sentinel data lake`（字幕 9 次）→ 教材在 Day 001、Day 002、Day 003、Day 004、Day 007、Day 008、Day 009、Day 010、Day 012
- `bookmarks`（字幕 11 次）→ 教材在 Day 001、Day 018
- `hunts`（字幕 9 次）→ 教材在 Day 001、Day 002、Day 003、Day 004、Day 005、Day 006、Day 007、Day 008、Day 009、Day 010、Day 011、Day 012、Day 013、Day 014、Day 015、Day 017、Day 018、Day 019
- `incident vs alert`（字幕 10 次）→ 教材在 Day 001、Day 004、Day 005、Day 006、Day 007、Day 010、Day 011、Day 012、Day 014、Day 016、Day 017、Day 018、Day 019
- `notebooks (Jupyter/MSTICPy)`（字幕 39 次）→ 教材在 Day 001、Day 010
- `playbooks (Logic Apps)`（字幕 2 次）→ 教材在 Day 001、Day 004、Day 005、Day 006、Day 007、Day 009、Day 011、Day 012、Day 016、Day 017、Day 019
- `search job`（字幕 8 次）→ 教材在 Day 006、Day 010
- `threat intelligence (TI)`（字幕 3 次）→ 教材在 Day 001、Day 006、Day 009、Day 010、Day 011、Day 014、Day 015、Day 017、Day 018、Day 019
- `workbooks`（字幕 4 次）→ 教材在 Day 006、Day 007、Day 008、Day 010

- Day 021 Advanced Hunting：Defender XDR 結構描述與自訂偵測：❌ 電子報未撰寫
- Day 022 Sentinel 威脅搜捕：Hunts、Hunting Queries、書籤與 Livestream：❌ 電子報未撰寫
- Day 023 假說驅動搜捕：MITRE ATT&CK 與 Notebooks：❌ 電子報未撰寫
- Day 024 Sentinel Graph、MCP Server 與 data lake 進階搜捕：❌ 電子報未撰寫
- Day 025 五週總複習：跨領域情境演練與考試策略：❌ 電子報未撰寫
---
合計待補：教材 2 項、Podcast 16 項。
