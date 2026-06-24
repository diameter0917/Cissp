#!/usr/bin/env python3
"""
send_daily.py
=============
每日（平日）寄信主程式。由 GitHub Actions 在台北 07:00 觸發。

流程：
  1. 讀 docs/schedule.json，以台灣時區 (UTC+8) 今天日期找出今天要寄的單元。
     若今天是週末或不在排程內 → 正常結束、不報錯（與 cron 形成雙重保險）。
  2. 讀對應 emails/day-XXX.html。
  3. 合併今日時事：若 news/day-XXX-news.html 存在，填入 <!-- TODAY_NEWS --> 占位處；
     不存在則移除占位標記、照常只寄教材本文（優雅降級）。
  4. 用 Gmail SMTP (smtp.gmail.com:587, STARTTLS) 寄出 multipart/alternative
     （HTML 為主 + 純文字 fallback）。認證用環境變數 GMAIL_USER / GMAIL_APP_PASSWORD /
     RECIPIENT_EMAIL（由 GitHub Secrets 注入）。不使用任何付費 API。
  5. 更新 sent_log.json（不存在則建立）並複製到 docs/sent_log.json。

環境變數：
  GMAIL_USER, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL  （必要）
  SEND_DATE （選用，YYYY-MM-DD，覆蓋「今天」以便手動測試）
  DRY_RUN   （選用，設為 1 時不實際寄信，只印出將寄送的內容摘要）
"""

import json
import os
import re
import smtplib
import sys
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAIPEI = timezone(timedelta(hours=8))
NEWS_MARKER = "<!-- TODAY_NEWS -->"


# ---------- 工具 ----------

def log(msg):
    print(f"[send_daily] {msg}", flush=True)


def today_taipei() -> str:
    override = os.environ.get("SEND_DATE")
    if override:
        return override
    return datetime.now(TAIPEI).date().isoformat()


def load_schedule():
    path = ROOT / "docs" / "schedule.json"
    if not path.exists():
        path = ROOT / "schedule.json"
    if not path.exists():
        log("找不到 schedule.json，結束。")
        sys.exit(0)
    return json.loads(path.read_text(encoding="utf-8"))


class _TextExtractor(HTMLParser):
    """把 HTML 轉成可讀純文字 fallback（標準庫，無外部相依）。"""
    BLOCK = {"br", "p", "div", "tr", "li", "h1", "h2", "h3", "details", "summary", "table"}

    def __init__(self):
        super().__init__()
        self.out = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self._skip = True
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.out.append(data.strip())


def html_to_text(html: str) -> str:
    p = _TextExtractor()
    p.feed(html)
    text = ""
    for tok in p.out:
        text += tok if tok == "\n" else (" " + tok)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def merge_news(html: str, seq: int) -> str:
    news_path = ROOT / "news" / f"day-{seq:03d}-news.html"
    if news_path.exists():
        snippet = news_path.read_text(encoding="utf-8").strip()
        log(f"合併今日時事：{news_path.name}（{len(snippet)} 字）")
        return html.replace(NEWS_MARKER, snippet)
    log("今日無時事檔，移除占位標記、只寄教材本文。")
    return html.replace(NEWS_MARKER, "")


def build_subject(item) -> str:
    week = (item["seq"] - 1) // 5 + 1
    phase_short = {"P1": "初期", "P2": "中期", "P3": "後期"}.get(item["phase"], item["phase"])
    return f"【CISSP W{week} {phase_short}·{item['domain']}】{item['code']} {item['title_zh']}"


# ---------- 寄信 ----------

def send_email(subject, html_body, gmail_user, app_password, recipient):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = recipient

    text_body = html_to_text(html_body)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(gmail_user, app_password)
        server.sendmail(gmail_user, [recipient], msg.as_string())


# ---------- log 回寫 ----------

def update_sent_log(item):
    log_path = ROOT / "sent_log.json"
    data = []
    if log_path.exists():
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = []
    # 移除同 seq 的舊紀錄（重寄時覆蓋）
    data = [r for r in data if r.get("seq") != item["seq"]]
    data.append({
        "seq": item["seq"],
        "date": item["date"],
        "code": item["code"],
        "phase": item["phase"],
        "title_zh": item["title_zh"],
        "sent_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "sent",
    })
    data.sort(key=lambda r: r.get("seq", 0))
    log_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "sent_log.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"已回寫 sent_log.json（共 {len(data)} 筆）")


def main():
    schedule = load_schedule()
    today = today_taipei()
    item = next((i for i in schedule["items"] if i["date"] == today), None)

    if item is None:
        log(f"今天（{today}, Asia/Taipei）非排程日（週末或超出範圍），不寄信，正常結束。")
        return

    log(f"今天要寄：seq={item['seq']} {item['code']} {item['title_zh']}（{today}）")

    email_path = ROOT / item["email_file"]
    if not email_path.exists():
        log(f"⚠️ 找不到教材檔 {item['email_file']}，跳過寄送（不報錯）。")
        return

    html = email_path.read_text(encoding="utf-8")
    html = merge_news(html, item["seq"])
    subject = build_subject(item)
    log(f"主旨：{subject}")

    if os.environ.get("DRY_RUN") == "1":
        log("DRY_RUN=1：不實際寄信、不回寫 sent_log（純測試流程）。")
        log(f"純文字 fallback 預覽（前 200 字）：\n{html_to_text(html)[:200]}")
        return

    gmail_user = os.environ.get("GMAIL_USER")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL")
    missing = [k for k, v in {
        "GMAIL_USER": gmail_user, "GMAIL_APP_PASSWORD": app_password,
        "RECIPIENT_EMAIL": recipient}.items() if not v]
    if missing:
        log(f"✗ 缺少環境變數：{', '.join(missing)}。無法寄信。")
        sys.exit(1)

    try:
        send_email(subject, html, gmail_user, app_password, recipient)
        log("✅ 寄送成功。")
    except Exception as e:
        log(f"✗ 寄送失敗：{type(e).__name__}: {e}")
        sys.exit(1)

    update_sent_log(item)


if __name__ == "__main__":
    main()
