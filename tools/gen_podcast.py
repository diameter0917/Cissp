#!/usr/bin/env python3
"""
gen_podcast.py — SC-200 Podcast 音檔合成（唯一有外部依賴的腳本）
================================================================
sc200/podcast/scripts/ep-NNN.json（雙主持人對談腳本）
→ edge-tts 逐 turn 合成（曉臻＋雲哲兩聲道）
→ ffmpeg concat 重編碼 48kbps mono 24kHz（正確時長 metadata + ID3）
→ docs/sc200/podcast/ep-NNN.mp3 ＋ sc200/podcast/episodes.json（manifest）

需求：pip install edge-tts；ffmpeg（GitHub Actions runner 內建）
注意：edge-tts 需連微軟語音端點——本開發環境的 proxy 會擋，
      請在 GitHub Actions（sc200-podcast.yml）或能連網的本機執行。

用法：python tools/gen_podcast.py --project sc200|cissp [ep ...] [--force]
      不給參數＝合成所有「腳本 hash 與 manifest 不符或音檔缺失」的集數。
"""

import argparse
import asyncio
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 專案由命令列指定（sc200／cissp），兩套課程共用同一條合成管線
_ap = argparse.ArgumentParser(add_help=False)
_ap.add_argument("--project", default="sc200")
PROJECT = _ap.parse_known_args()[0].project
PROJ = ROOT / PROJECT
SCRIPTS = PROJ / "podcast" / "scripts"
MANIFEST = PROJ / "podcast" / "episodes.json"
OUT_DIR = ROOT / "docs" / PROJECT / "podcast"

CONFIG = json.loads((PROJ / "site_config.json").read_text(encoding="utf-8"))["podcast"]
VOICES = {"host_f": CONFIG["voice_host_f"], "host_m": CONFIG["voice_host_m"]}

# 發音替換表（見 SC200_CONTENT_SPEC.md §3；只影響 TTS，不影響顯示文字）
SPEECH_SUBS = [
    # CISSP 常用縮寫
    ("BIA", "B I A"), ("RTO", "R T O"), ("RPO", "R P O"), ("MTD", "M T D"),
    ("SOD", "S O D"), ("DAC", "D A C"), ("MAC", "M A C"), ("RBAC", "R BACK"),
    ("ALE", "A L E"), ("SLE", "S L E"), ("ARO", "A R O"), ("BCP", "B C P"),
    ("DRP", "D R P"), ("SLA", "S L A"), ("PII", "P I I"), ("IAM", "I A M"),
    ("PKI", "P K I"), ("TPM", "T P M"), ("SDLC", "S D L C"), ("SAST", "SAST"),
    ("DAST", "DAST"), ("CIA", "C I A"), ("GDPR", "G D P R"), ("NIST", "NIST"),
    # SC-200 常用縮寫
    ("ATT&CK", "attack"), ("KQL", "K Q L"), ("XDR", "X D R"), ("SIEM", "SIM"),
    ("SOAR", "SORE"), ("MDE", "M D E"), ("MDO", "M D O"), ("MDI", "M D I"),
    ("MDTI", "M D T I"), ("SCU", "S C U"), ("DCR", "D C R"), ("ASIM", "A SIM"),
    ("UEBA", "U E B A"), ("NRT", "N R T"), ("IoC", "I O C"), ("RBAC", "R BACK"),
]


def speech_text(text):
    for src, dst in SPEECH_SUBS:
        text = text.replace(src, dst)
    return text


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"episodes": {}}


async def tts_turn(communicate_cls, text, voice, out: Path, sem):
    async with sem:
        for attempt in range(3):
            try:
                await communicate_cls(text, voice, rate="+8%").save(str(out))
                if out.stat().st_size > 0:
                    return
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    raise
                print(f"    ⚠️ TTS 重試 {attempt + 1}：{str(e)[:100]}")
                await asyncio.sleep(3 * (attempt + 1))


async def synth_episode(script, tmp: Path):
    import edge_tts
    sem = asyncio.Semaphore(4)
    tasks = []
    for i, turn in enumerate(script["dialogue"]):
        voice = VOICES.get(turn["speaker"])
        if voice is None:
            raise ValueError(f"未知 speaker：{turn['speaker']}")
        out = tmp / f"seg_{i:03d}.mp3"
        tasks.append(tts_turn(edge_tts.Communicate, speech_text(turn["text"]), voice, out, sem))
    await asyncio.gather(*tasks)


def make_silence(tmp: Path) -> Path:
    """turn 之間 350ms 靜音，銜接自然。"""
    sil = tmp / "silence.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
         "-t", "0.35", "-c:a", "libmp3lame", "-b:a", CONFIG["bitrate"], str(sil)],
        check=True, capture_output=True)
    return sil


def stitch(script, tmp: Path, out_mp3: Path, use_ffmpeg=True):
    n = len(script["dialogue"])
    segs = [tmp / f"seg_{i:03d}.mp3" for i in range(n)]
    if use_ffmpeg:
        sil = make_silence(tmp)
        lst = tmp / "list.txt"
        lines = []
        for i, s in enumerate(segs):
            lines.append(f"file '{s}'")
            if i < n - 1:
                lines.append(f"file '{sil}'")
        lst.write_text("\n".join(lines), encoding="utf-8")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c:a", "libmp3lame", "-b:a", CONFIG["bitrate"],
             "-ac", "1", "-ar", str(CONFIG["sample_rate"]),
             "-metadata", f"title=EP{script['episode']}｜{script['title_zh']}",
             "-metadata", f"album={CONFIG['title']}",
             "-metadata", f"artist={CONFIG['author']}",
             "-metadata", f"track={script['episode']}",
             str(out_mp3)],
            check=True, capture_output=True)
    else:
        # 後備：同編碼 mp3 直接串接（時長 metadata 可能不準）
        with out_mp3.open("wb") as f:
            for s in segs:
                f.write(s.read_bytes())


def probe_duration(mp3: Path) -> int:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(mp3)],
            check=True, capture_output=True, text=True)
        return round(float(r.stdout.strip()))
    except Exception:  # noqa: BLE001
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", nargs="*", type=int, help="集數（如 1 2 3）；空＝全部缺漏")
    ap.add_argument("--force", action="store_true", help="忽略 manifest hash 全部重做")
    ap.add_argument("--no-ffmpeg", action="store_true", help="無 ffmpeg 時的直接串接後備")
    ap.add_argument("--project", default="sc200", help="sc200 或 cissp")
    args = ap.parse_args()

    try:
        import edge_tts  # noqa: F401
    except ImportError:
        sys.exit("✗ 找不到 edge-tts。請先：pip install edge-tts")
    if not args.no_ffmpeg and not shutil.which("ffmpeg"):
        sys.exit("✗ 找不到 ffmpeg（或改用 --no-ffmpeg）")

    manifest = load_manifest()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_scripts = sorted(SCRIPTS.glob("ep-*.json"))
    if args.episodes:
        wanted = {f"ep-{n:03d}" for n in args.episodes}
        all_scripts = [p for p in all_scripts if p.stem in wanted]
    if not all_scripts:
        print("ℹ️ 沒有符合的腳本檔。")
        return

    done = skipped = failed = 0
    for sp in all_scripts:
        script = json.loads(sp.read_text(encoding="utf-8"))
        ep = script["episode"]
        key = f"{ep:03d}"
        out_mp3 = OUT_DIR / f"ep-{key}.mp3"
        h = sha256_file(sp)
        rec = manifest["episodes"].get(key)
        if not args.force and rec and rec.get("script_sha256") == h and out_mp3.exists():
            skipped += 1
            print(f"[EP{ep}] 略過（腳本未變更）")
            continue
        print(f"[EP{ep}] {script['title_zh']}（{len(script['dialogue'])} turns）合成中…")
        try:
            with tempfile.TemporaryDirectory(prefix=f"sc200-ep{key}-") as td:
                tmp = Path(td)
                asyncio.run(synth_episode(script, tmp))
                stitch(script, tmp, out_mp3, use_ffmpeg=not args.no_ffmpeg)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"    ✗ 失敗：{str(e)[:200]}")
            continue
        dur = probe_duration(out_mp3)
        manifest["episodes"][key] = {
            "episode": ep, "unit": script.get("unit"), "title_zh": script["title_zh"],
            "file": f"ep-{key}.mp3", "bytes": out_mp3.stat().st_size,
            "duration_sec": dur, "script_sha256": h,
        }
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        done += 1
        print(f"    ✅ {out_mp3.name}：{out_mp3.stat().st_size/1e6:.1f} MB，{dur//60}:{dur%60:02d}")

    print(f"\n完成 {done}、略過 {skipped}、失敗 {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
