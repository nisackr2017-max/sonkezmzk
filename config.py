# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
import re
from os import getenv

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ══════════════════════════════════════════════════════════
#  AYARLARI BURAYA YAZ
#  Railway Variables doldurmana gerek yok.
#  GitHub reposu KAPALI (private) olsun — token/session burada durur.
# ══════════════════════════════════════════════════════════

API_ID = 31567558                                                                                      # my.telegram.org
API_HASH = "7abd506b1fc7b9a191d7e188180e7194"                                                          # my.telegram.org
BOT_TOKEN = "9117443366:AAF9jHCWxmymR3A_Blos2XpWyY5r59NI9KA"                                           # @BotFather
MONGO_URL = "mongodb+srv://mongoguess:guessmongo@cluster0.zcwklzz.mongodb.net/?retryWrites=true&w=majority"  # mongodb+srv://...
LOGGER_ID = -1003826733145                                                                             # log grubu id  (-100...)
OWNER_ID = 8259875589                                                                                  # senin Telegram user id
SESSION = "BAHhrsYAbSk63OhLJfb2o7_XOZeqsb6JCFP-fyulDeFA7w_UYB-Vs-vimqtU610Ytdd9ZUAm8M6rn4JJpi353mdjQOD5GH03X2qvcnF3XvwII-m07kWPBWTKrS7-1-_MZfKJQJ7Rd2aNdea1ngl1Zfh_ACHiNOD3rtn-sCpv0wn2vyTZh9ZYtFABqGGwHMneyxlG-rKv4FDk4ug_MYIva6fJV7Q_f57Y1GLWDBVqS8fC81SX6353BtfDaHtZegxZkL6HY4rlHHaF44OUbGHdpd53jEj9gaZnkiDqcqf0Kq8GXE2Gs06cfMOCEB9Rs0oyBO6VDkOFae6jWXsd8MIKjqB-dBuAdwAAAAIauV9-AQ"  # session_al.bat çıktısı (otomatik de yazılır)

# isteğe bağlı
SESSION2 = ""
SESSION3 = ""
SUPPORT_CHANNEL = "https://t.me/loncamusic"
SUPPORT_CHAT = "https://t.me/loncamusic"
DURATION_LIMIT = 180                # dakika
QUEUE_LIMIT = 50
PLAYLIST_LIMIT = 20
AUTO_END = False
AUTO_LEAVE = False
VIDEO_PLAY = True

# YouTube — BOŞ BIRAK. Token otomatik üretilir, cookie gerekmez.
PO_TOKEN = ""
VISITOR_DATA = ""
POT_PROVIDER_URL = ""
# Railway IP'si YouTube tarafından engellenirse: residential proxy (ör. http://kullanici:sifre@host:port)
PROXY = ""
DEFAULT_THUMB = "https://te.legra.ph/file/3e40a408286d4eda24191.jpg"
PING_IMG = ""
START_IMG = ""

# ══════════════════════════════════════════════════════════
#  Aşağıyı değiştirme
#  config.py doluysa o kullanılır. Env / .env sadece boş alanları doldurur.
# ══════════════════════════════════════════════════════════


def _clean(val) -> str:
    if val is None:
        return ""
    return str(val).strip().strip('"').strip("'")


def _env(key: str, default: str = "") -> str:
    val = getenv(key)
    if val is None or not str(val).strip():
        return _clean(default)
    return _clean(val)


def _str(file_val, env_key: str, default: str = "") -> str:
    v = _clean(file_val)
    return v if v else _env(env_key, default)


def _env_int(key: str, default: int = 0) -> int:
    raw = re.sub(r"[^\d-]", "", _env(key, str(default)))
    try:
        return int(raw) if raw not in ("", "-", "+") else int(default or 0)
    except ValueError:
        return int(default or 0)


def _int(file_val, env_key: str, default: int = 0) -> int:
    if isinstance(file_val, int) and file_val != 0:
        return file_val
    raw = re.sub(r"[^\d-]", "", _clean(file_val))
    if raw not in ("", "-", "+"):
        try:
            return int(raw)
        except ValueError:
            pass
    return _env_int(env_key, default)


def _bool(file_val, env_key: str) -> bool:
    if isinstance(file_val, bool):
        return file_val
    val = getenv(env_key)
    if val is None or not str(val).strip():
        return bool(file_val)
    return str(val).strip().lower() in ("true", "1", "yes", "on")


def _session(file_val, env_key: str) -> str:
    return re.sub(r"\s+", "", _str(file_val, env_key))


class Config:
    REQUIRED = ("API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL", "LOGGER_ID", "OWNER_ID")

    def __init__(self):
        self.API_ID = _int(API_ID, "API_ID")
        self.API_HASH = _str(API_HASH, "API_HASH")

        self.BOT_TOKEN = _str(BOT_TOKEN, "BOT_TOKEN")
        self.MONGO_URL = _str(MONGO_URL, "MONGO_URL") or _env("MONGO_DB_URI")

        self.LOGGER_ID = _int(LOGGER_ID, "LOGGER_ID")
        self.OWNER_ID = _int(OWNER_ID, "OWNER_ID")

        self.DURATION_LIMIT = _int(DURATION_LIMIT, "DURATION_LIMIT", 180) * 60
        self.QUEUE_LIMIT = _int(QUEUE_LIMIT, "QUEUE_LIMIT", 50)
        self.PLAYLIST_LIMIT = _int(PLAYLIST_LIMIT, "PLAYLIST_LIMIT", 20)

        self.SESSION1 = _session(SESSION, "SESSION")
        self.SESSION2 = _session(SESSION2, "SESSION2") or None
        self.SESSION3 = _session(SESSION3, "SESSION3") or None

        self.SUPPORT_CHANNEL = _str(SUPPORT_CHANNEL, "SUPPORT_CHANNEL", SUPPORT_CHANNEL)
        self.SUPPORT_CHAT = _str(SUPPORT_CHAT, "SUPPORT_CHAT", SUPPORT_CHAT)

        self.AUTO_END: bool = _bool(AUTO_END, "AUTO_END")
        self.AUTO_LEAVE: bool = _bool(AUTO_LEAVE, "AUTO_LEAVE")
        self.VIDEO_PLAY: bool = _bool(VIDEO_PLAY, "VIDEO_PLAY")

        self.PO_TOKEN = [t for t in _str(PO_TOKEN, "PO_TOKEN").split(" ") if t]
        self.VISITOR_DATA = _str(VISITOR_DATA, "VISITOR_DATA")
        self.POT_PROVIDER_URL = _str(POT_PROVIDER_URL, "POT_PROVIDER_URL")
        self.PROXY = _str(PROXY, "PROXY")
        self.DEFAULT_THUMB = _str(DEFAULT_THUMB, "DEFAULT_THUMB", DEFAULT_THUMB) or DEFAULT_THUMB
        self.PING_IMG = _str(PING_IMG, "PING_IMG") or self.DEFAULT_THUMB
        self.START_IMG = _str(START_IMG, "START_IMG") or self.DEFAULT_THUMB

    def missing(self) -> list:
        return [var for var in self.REQUIRED if not getattr(self, var)]

    def check(self):
        missing = self.missing()
        if missing:
            raise SystemExit(
                f"Eksik ayarlar: {', '.join(missing)}\n"
                "config.py dosyasının üst kısmına yaz (SESSION için session_al.bat).\n"
                "Railway Variables kullanmana gerek yok."
            )
        if self.MONGO_URL and not self.MONGO_URL.startswith(("mongodb://", "mongodb+srv://")):
            raise SystemExit("MONGO_URL mongodb:// veya mongodb+srv:// ile başlamalı.")
