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
    # 注意：這是依序套用的字串取代，長的要排在短的前面
    # （例如 DDoS 必須在 DoS 之前，否則會被切成 "D DoS"）。
    # 只有「以非英數字相接」的複合詞需要這樣手動排序——夾在英數字中間的
    # 不會被咬到（IPv6 裡的 IP、CISSP 裡的 CIS 都靠邊界判斷自動免疫）。
    ("ISO 27001", "I S O 二七零零一"), ("ISO 27034", "I S O 二七零三四"),
    ("ISO 27037", "I S O 二七零三七"), ("SW-CMM", "S W C M M"),
    ("SC-200", "S C 二零零"), ("ISO 27002", "I S O 二七零零二"),
    # SOC 1/2/3 的數字若留給中文 TTS 會唸成「SOCK 二 Type two」，前後語言打架
    ("SOC 1", "SOCK one"), ("SOC 2", "SOCK two"), ("SOC 3", "SOCK three"),
    ("FIPS 203", "FIPS 二零三"), ("FIPS 204", "FIPS 二零四"),
    ("FIPS 205", "FIPS 二零五"), ("S/MIME", "S MIME"),
    # NIST SP 800 系列：連字號通則會把它變成「八百 八十八」，
    # 明列成「八零零之八八」才是這份標準平常被唸出來的樣子。
    ("800-18", "八零零之一八"), ("800-53", "八零零之五三"),
    ("800-60", "八零零之六零"), ("800-86", "八零零之八六"),
    ("800-63", "八零零之六三"), ("800-88", "八零零之八八"),
    ("800-207", "八零零之二零七"),
    # 第二次提到時常省略 ISO 前綴，光一串數字會被唸成「兩萬七千零二」
    ("27001", "二七零零一"), ("27002", "二七零零二"),
    ("27034", "二七零三四"), ("27037", "二七零三七"),
    ("DDoS", "D DOS"), ("(ISC)²", "I S C squared"), ("ISC2", "I S C squared"),
    ("DAD", "D A D"), ("AAA", "triple A"), ("NDA", "N D A"), ("AUP", "A U P"),
    ("DBA", "D B A"), ("CEO", "C E O"), ("CIO", "C I O"), ("CSO", "C S O"),
    ("CISO", "C I S O"), ("COO", "C O O"),
    # Domain 8 軟體開發安全
    # CI/CD 必須排在 CI 之前：斜線不是英數字，邊界判斷會放行，
    # 所以 CI 規則若先套用會把 CI/CD 切成「C I /CD」。
    ("CI/CD", "C I C D"), ("CI", "C I"),
    ("DevSecOps", "Dev Sec Ops"), ("DevOps", "Dev Ops"),
    ("SBOM", "S BOM"), ("SCA", "S C A"), ("XSS", "X S S"),
    ("CSRF", "C S R F"), ("CSP", "C S P"), ("SameSite", "Same Site"),
    ("Log4Shell", "Log four Shell"), ("Log4j", "Log four J"),
    # Domain 6 評估與稽核
    ("KPI", "K P I"), ("KRI", "K R I"), ("ROE", "R O E"), ("EOL", "E O L"),
    ("PDCA", "P D C A"), ("SSAE", "S S A E"), ("ISAE", "I S A E"), ("ISO", "I S O"),
    ("Type I", "Type one"), ("Type II", "Type two"),
    # Domain 3 密碼學與實體安全
    ("HSM", "H S M"), ("ICS", "I C S"), ("UPS", "U P S"), ("CA", "C A"),
    ("AES", "A E S"), ("DES", "D E S"), ("TB", "T B"), ("CPTED", "C P T E D"),
    ("MD5", "M D five"), ("SHA-1", "SHA one"), ("SHA-2", "SHA two"),
    # Domain 5 身分與存取管理
    ("IAAA", "I triple A"), ("MFA", "M F A"), ("OTP", "O T P"), ("SSO", "S S O"),
    ("PAM", "P A M"), ("JIT", "J I T"), ("ABAC", "A BACK"),
    ("FAR", "F A R"), ("FRR", "F R R"), ("CER", "C E R"),
    ("IdP", "I D P"), ("SCIM", "S C I M"), ("OIDC", "O I D C"), ("SAML", "SAM L"),
    ("API", "A P I"), ("HR", "H R"), ("AuthN", "Auth N"), ("AuthZ", "Auth Z"),
    ("FIDO2", "FIDO two"), ("TACACS+", "TACACS plus"),
    # Domain 2 資產安全
    ("CASB", "C A S B"), ("DLP", "D L P"), ("DRM", "D R M"), ("DPA", "D P A"),
    ("DPO", "D P O"), ("SSD", "S S D"), ("CRM", "C R M"), ("SaaS", "SASS"),
    ("CISSP", "C I S S P"), ("IT", "I T"), ("SP", "S P"),
    # Domain 3/4 網路與密碼學
    ("OSI", "O S I"), ("TLS", "T L S"), ("SSL", "S S L"), ("SSH", "S S H"),
    ("DNSSEC", "D N S SEC"), ("DNS", "D N S"), ("DoH", "D O H"), ("DoT", "D O T"),
    ("IPsec", "I P sec"), ("AH", "A H"), ("ESP", "E S P"),
    ("IDS", "I D S"), ("IPS", "I P S"), ("NAC", "N A C"), ("NGFW", "N G F W"),
    ("VPN", "V P N"), ("VLAN", "V LAN"), ("DMZ", "D M Z"), ("DAI", "D A I"),
    ("SPF", "S P F"), ("DKIM", "D KIM"), ("DMARC", "D MARC"),
    ("ARP", "A R P"), ("ICMP", "I C M P"), ("SYN", "SIN"), ("PDU", "P D U"),
    ("TCP", "T C P"), ("UDP", "U D P"), ("SNMP", "S N M P"),
    ("FTPS", "F T P S"), ("SFTP", "S F T P"), ("FTP", "F T P"),
    ("WPA3", "W P A 3"), ("WPA2", "W P A 2"), ("SAE", "S A E"),
    ("802.1X", "八零二點一 X"), ("IoT", "I O T"), ("AP", "A P"),
    ("SQL", "S Q L"), ("DoS", "DOS"), ("SOC", "SOCK"),
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
    ("UEBA", "U E B A"), ("NRT", "N R T"), ("IoC", "I O C"),
    # 週更 Podcast 補收的縮寫（EP07 / EP10 / EP11）
    # 帶連字號的要排在這裡：連字號不是英數字，邊界判斷放行，
    # 若讓 TTS 自己唸會唸成減號（「三減二減一」）。
    ("MS17-010", "M S 十七之零一零"), ("3-2-1", "三 二 一"),
    ("CVSS", "C V S S"), ("NTP", "N T P"), ("RACI", "R A C I"),
    ("FIPS", "FIPS"), ("EOS", "E O S"),
    ("HMAC", "H MACK"), ("KMS", "K M S"), ("EAL", "E A L"),
    ("ECB", "E C B"), ("GCM", "G C M"), ("ECC", "E C C"),
    ("PLC", "P L C"), ("USB", "U S B"),
    # Common Criteria 三件套。兩個字母的 PP／ST 靠邊界判斷才敢收：
    # 只有前後都不是英數字才換，夾在英文字中間的不會被動到。
    ("TOE", "T O E"), ("PP", "P P"), ("ST", "S T"),
    # 網路（EP12）。IPv4／IPv6 不必排在 IP 之前——IP 後面接的 v 是英數字，
    # 邊界判斷本來就不會讓 IP 規則咬進去；VoIP、IPsec、IPS 同理。
    ("IPv4", "I P v four"), ("IPv6", "I P v six"), ("IP", "I P"),
    ("HTTPS", "H T T P S"), ("HTTP", "H T T P"), ("VoIP", "V O I P"),
    ("SSID", "S S I D"), ("PSK", "P S K"), ("EAP", "E A P"),
    ("BEC", "B E C"), ("SQLi", "S Q L i"),
    # 這兩個業界本來就當單字唸，維持原樣（與 SAST／DAST／NIST 同慣例）
    ("WAF", "WAF"), ("RADIUS", "RADIUS"),
    # 身分與存取（EP13）
    ("IAL", "I A L"), ("AAL", "A A L"), ("FAL", "F A L"), ("JWT", "J W T"),
    ("PKCE", "P K C E"), ("KDC", "K D C"), ("TGT", "T G T"), ("TGS", "T G S"),
    ("LSASS", "L SASS"), ("TOTP", "T O T P"), ("XML", "X M L"), ("ACL", "A C L"),
    ("PDP", "P D P"), ("PEP", "P E P"), ("AiTM", "A I T M"), ("OAuth", "O Auth"),
    # 評估、維運與開發（EP14–16）
    ("IAST", "I A S T"), ("BAS", "B A S"), ("RUM", "R U M"), ("KCI", "K C I"),
    ("CUEC", "C U E C"), ("MTTR", "M T T R"), ("MTTD", "M T T D"),
    ("TTP", "T T P"), ("CMDB", "C M D B"), ("CISA", "C I S A"), ("CIS", "C I S"),
    ("KEV", "K E V"), ("IaC", "I A C"), ("EDR", "E D R"), ("SCM", "S C M"),
    ("CMM", "C M M"), ("BSIMM", "B SIM"), ("CSF", "C S F"), ("RMF", "R M F"),
    ("ROSI", "R O S I"), ("ERP", "E R P"), ("SOP", "S O P"), ("POS", "P O S"),
    # 資產與治理（EP18）
    ("SCC", "S C C"), ("BCR", "B C R"),
    # 大小寫變體：腳本裡兩種寫法都有，兩種都要收
    ("SoD", "S O D"), ("IOC", "I O C"),
    # 其他掃描到的常見縮寫
    ("CCTV", "C C T V"), ("CDN", "C D N"), ("NAT", "N A T"), ("URL", "U R L"),
    ("HTML", "H T M L"), ("DOM", "D O M"), ("WEP", "W E P"), ("WPA", "W P A"),
    ("ACK", "A C K"), ("AV", "A V"), ("EF", "E F"), ("WRT", "W R T"),
    ("UI", "U I"), ("PC", "P C"), ("DR", "D R"), ("ID", "I D"),
    # 業界當單字唸的，明列成不變動，免得日後有人以為漏收了
    ("BOLA", "BOLA"), ("STIG", "STIG"), ("RASP", "RASP"), ("SLSA", "SLSA"),
    ("SAMM", "SAMM"), ("COTS", "COTS"), ("SCADA", "SCADA"), ("FedRAMP", "FedRAMP"),
    # 密碼學與 PKI（EP19、EP25）
    ("SHA-256", "SHA 二五六"), ("SHA-512", "SHA 五一二"),
    ("2DES", "two DES"), ("3DES", "three DES"),
    # 後量子那三支必須排在 DSA 之前：連字號不是英數字，邊界判斷會放行，
    # DSA 規則若先套用會把 ML-DSA 切成「ML D S A」。
    ("ML-KEM", "M L KEM"), ("ML-DSA", "M L D S A"), ("SLH-DSA", "S L H D S A"),
    ("ECDSA", "E C D S A"), ("DSA", "D S A"), ("RSA", "R S A"), ("DH", "D H"),
    ("OCSP", "O C S P"), ("CRL", "C R L"), ("BLP", "B L P"), ("RA", "R A"),
    ("PQC", "P Q C"), ("QKD", "Q K D"),
    # 網路（EP20）
    ("BGP", "B G P"), ("OSPF", "O S P F"), ("EIGRP", "E I G R P"),
    ("RIP", "R I P"), ("DHCP", "D H C P"), ("HIDS", "H I D S"),
    ("NIDS", "N I D S"), ("IKE", "I K E"), ("LDAPS", "L DAPS"),
    ("LDAP", "L DAP"), ("RDP", "R D P"), ("SMTP", "S M T P"), ("SA", "S A"),
    # 身分、開發與零信任（EP21、EP24、EP25）
    ("krbtgt", "K R B T G T"), ("WebAuthn", "Web Auth N"),
    ("HttpOnly", "H T T P Only"), ("IDOR", "I D O R"),
    ("ZTNA", "Z T N A"), ("ZTA", "Z T A"), ("C2", "C 二"),
    ("IaaS", "I A A S"), ("PaaS", "P A A S"),
    # 零信任的三個零件，兩個字母全靠邊界判斷
    ("PE", "P E"), ("PA", "P A"),
    # CAT 不明列會被唸成英文單字 cat
    ("CAT", "C A T"),
    # Kerberos 的鑑別伺服器。兩個字母，不明列會被唸成英文的 as
    ("AS", "A S"),
    # 羅馬數字比照既有的 Type II
    ("Schrems II", "Schrems two"),
    # 業界當單字唸的
    ("OWASP", "OWASP"), ("PIN", "PIN"),
]

# 集數、Domain 代號與 OSI 層數：直接唸 "EP12" 會變成「E P 一二」，
# 唸成「第十二集」才聽得懂。EP1 不會咬進 EP10——後面的 0 是英數字，
# 邊界判斷會擋下來。
_CN_NUM = ("", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
           "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八",
           "十九", "二十", "二十一", "二十二", "二十三", "二十四",
           "二十五", "二十六")
SPEECH_SUBS += [(f"EP{i:02d}", f"第{_CN_NUM[i]}集") for i in range(1, 27)]
SPEECH_SUBS += [(f"EP{i}", f"第{_CN_NUM[i]}集") for i in range(1, 10)]  # EP10 上一行已收
SPEECH_SUBS += [(f"D{i}", f"Domain {_CN_NUM[i]}") for i in range(1, 9)]
SPEECH_SUBS += [(f"L{i}", f"第{_CN_NUM[i]}層") for i in range(1, 8)]


# 邊界感知的替換樣式快取：只有前後不是英數字時才換，
# 才不會把 API 裡的 AP、SHA 裡的 AH、IPsec 裡的 IPS 誤換掉。
# 有了邊界判斷，DNS 也不會誤傷 DNSSEC，替換表就不必再依長度排序。
_SUB_PATTERNS = [
    (re.compile(r"(?<![A-Za-z0-9])" + re.escape(src) + r"(?![A-Za-z0-9])"), dst)
    for src, dst in SPEECH_SUBS
]


# 夾在英數字之間的連字號，中文語音會唸成「減」——AES-256 變「A E S 減 256」、
# SYN-ACK 變「SIN 減 A C K」、Wi-Fi 變「Wi 減 Fi」。替換完之後一律換成空白，
# 這樣 Bell-LaPadula、Pass-the-Hash、anti-CSRF 這些都不必逐一列進替換表。
_HYPHEN = re.compile(r"(?<=[A-Za-z0-9])-(?=[A-Za-z0-9])")


def speech_text(text):
    for pattern, dst in _SUB_PATTERNS:
        text = pattern.sub(dst, text)
    return _HYPHEN.sub(" ", text)


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
    # manifest 是專案的狀態檔，即使這次沒有任何集數要合成也要存在——
    # workflow 的 git add 會指名它，檔案不存在會直接 fatal。
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    if not MANIFEST.exists():
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                            encoding="utf-8")

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
