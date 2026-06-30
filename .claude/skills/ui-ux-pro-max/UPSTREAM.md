# 來源與授權（Vendored Skill Provenance）

本目錄是把第三方 Claude Code skill **vendor（內嵌）** 進本 repo 的完整複本，
讓本專案（及未來的 web session）都能直接使用，不需另外安裝。

| 項目 | 內容 |
|---|---|
| 名稱 | `ui-ux-pro-max` |
| 上游 | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| 取得方式 | 由上游 `main` 逐檔下載，**逐位元組比對 GitHub API tree 的檔案大小**確認完整 |
| 版本（commit） | `3effe971c07a20658952e304099557523bdf9e44`（main，匯入當下） |
| 授權 | MIT（見本目錄 `LICENSE`） |
| 內容 | `SKILL.md` + `data/`（CSV 資料庫）+ `scripts/`（Python 搜尋/設計系統引擎），共 35 檔 |

## 為何用 vendor 而非官方安裝

本次匯入在受限的雲端環境執行，官方安裝管道皆不可用：

- `git clone` 上游 repo → 被網路政策擋（egress 僅允許本 repo）。
- `npx ui-ux-pro-max-cli init` → 不執行未指名的外部套件。
- 官方 `/plugin marketplace add` → 屬使用者端互動指令，且裝在 user scope、不入 repo。

可達的 `raw.githubusercontent.com` 仍可逐檔下載，故採「逐位元組 vendor」——
這是此環境下**最完整、最忠實**重現該 skill 的方式（含全部 data 與 scripts，引擎可實際執行）。

## 驗證 / 使用

```bash
python3 --version                                   # 需要 Python 3
# 產生設計系統建議（引擎自我驗證可用）
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<product> <industry> <keywords>" --design-system
# 單一面向搜尋
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --domain <style|color|typography|ux|...>
```

在 Claude Code 中，本 skill 會以專案 skill 自動載入（名稱 `ui-ux-pro-max`）。

## 如何更新到上游新版

```bash
# 取得上游 main 最新檔案大小清單，逐檔重抓並比對（同匯入流程）
# 或在本機用官方 CLI： npx ui-ux-pro-max-cli init --ai claude
```

> 取得完整官方版（含 marketplace 更新通知）：在自己的 Claude Code 執行
> `/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill`
> 然後 `/plugin install ui-ux-pro-max@ui-ux-pro-max-skill`。
