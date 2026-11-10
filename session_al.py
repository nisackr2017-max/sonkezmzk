# Asistan hesabı için Pyrogram (kurigram) SESSION string'i oluşturur.
# Çalıştırma:  session_al.bat   veya   python session_al.py
# Çıktı config.py içindeki SESSION satırına yazılır.

import asyncio
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _die(msg: str, code: int = 1) -> None:
    print(f"\nHATA: {msg}")
    raise SystemExit(code)


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default


def _load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except Exception:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def _from_config_py() -> tuple:
    cfg = ROOT / "config.py"
    if not cfg.is_file():
        return 0, ""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_bot_config_session", cfg)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        api_id = int(getattr(mod, "API_ID", 0) or 0)
        api_hash = str(getattr(mod, "API_HASH", "") or "").strip()
        return api_id, api_hash
    except Exception:
        return 0, ""


def _write_session_to_config(session: str) -> bool:
    path = ROOT / "config.py"
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    out = []
    done = False
    assignment = f"SESSION = {json.dumps(session)}  # session_al.bat çıktısı\n"
    for line in lines:
        raw = line.lstrip(" \t")
        if (
            not done
            and re.match(r"^SESSION\s*=", raw)
            and not raw.startswith("SESSION2")
            and not raw.startswith("SESSION3")
            and not raw.startswith("SESSION1")
        ):
            indent = line[: len(line) - len(raw)]
            nl = "\n" if line.endswith("\n") else ""
            out.append(f"{indent}{assignment.rstrip()}{nl}")
            done = True
        else:
            out.append(line)
    if not done:
        return False
    path.write_text("".join(out), encoding="utf-8")
    return True


def _clipboard(text: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import subprocess
        r = subprocess.run(
            ["clip"],
            input=text,
            text=True,
            encoding="utf-16",
            check=False,
        )
        return r.returncode == 0
    except Exception:
        return False


async def main() -> None:
    print("=== LONCA MUSIC - ASISTAN SESSION ===")
    print("Cikti config.py -> SESSION satirina yazilacak.\n")
    _load_env()

    cfg_id, cfg_hash = _from_config_py()
    api_id_raw = (os.getenv("API_ID") or "").strip() or (str(cfg_id) if cfg_id else "")
    api_hash = (os.getenv("API_HASH") or "").strip() or cfg_hash
    if api_id_raw and api_hash:
        kaynak = ".env" if os.getenv("API_ID") and os.getenv("API_HASH") else "config.py"
        print(f"API_ID / API_HASH {kaynak} dosyasindan alindi.")
    if not api_id_raw:
        api_id_raw = _ask("API_ID (my.telegram.org)")
    if not api_hash:
        api_hash = _ask("API_HASH")

    try:
        api_id = int(re.sub(r"[^\d-]", "", api_id_raw) or "0")
    except ValueError:
        _die("API_ID sadece rakam olmali.")
    if api_id <= 0 or not api_hash:
        _die("API_ID ve API_HASH bos olamaz. config.py veya my.telegram.org")

    try:
        from pyrogram import Client
        from pyrogram import types as pg_types
    except ImportError:
        _die("kurigram yok. Once kurulum.bat calistir veya: pip install -U kurigram")
    if not hasattr(pg_types, "LinkPreviewOptions"):
        _die("Yanlis pyrogram surumu. kurulum.bat calistir (eski pyrogram kaldirilip kurigram kurulur).")

    print("\nTelefon numarasini +90... seklinde gir.")
    print("Telegram kodunu yaz. Iki adimli dogrulama varsa sifreni de soracak.\n")

    async with Client(
        name="session_al",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
    ) as app:
        me = await app.get_me()
        if getattr(me, "is_bot", False):
            _die("Bot hesabi asistan olamaz. Normal bir kullanici hesabi ile giris yap.")
        session = await app.export_session_string()
        try:
            await app.send_message(
                "me",
                "🔑 <b>Lonca Music SESSION</b> (kimseyle paylaşma!)\n\n"
                f"<code>{session}</code>\n\n"
                "Bu yazı <b>config.py</b> → SESSION satırına yazıldı.",
            )
            kayit = " Ayrica Telegram Kayitli Mesajlarina gonderildi."
        except Exception:
            kayit = ""

    out = ROOT / "session_cikti.txt"
    out.write_text(session + "\n", encoding="utf-8")
    clipped = _clipboard(session)
    yazildi = _write_session_to_config(session)

    print(f"\nHesap: {me.first_name} (ID: {me.id})")
    print("\n===== SESSION =====")
    print(session)
    print("===================")
    print(f"\nDosyaya yazildi: {out}")
    if yazildi:
        print("config.py icindeki SESSION satiri guncellendi.")
    else:
        print("UYARI: config.py SESSION satiri bulunamadi. session_cikti.txt icinden yapistir.")
    if clipped:
        print("Panoya da kopyalandi.")
    print(kayit)
    print("\nSiradaki: config.py'de BOT_TOKEN, MONGO_URL, LOGGER_ID, OWNER_ID dolu olsun.")
    print("Sonra GitHub'a push + Railway Redeploy. Variables doldurmana gerek yok.")
    print("PO_TOKEN doldurma. Cookie gerekmez.")
    print("SESSION'i kimseyle paylasma. Isin bitince session_cikti.txt dosyasini sil.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nIptal edildi.")
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:
        print(f"\nHATA: {type(e).__name__}: {e}")
        print("kurulum.bat calistirip tekrar dene.")
        raise SystemExit(1)
