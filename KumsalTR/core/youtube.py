import os
import re
import yt_dlp
import random
import asyncio
import aiohttp
from typing import Optional
from pathlib import Path

from py_yt import Playlist, VideosSearch

from KumsalTR import logger, config
from KumsalTR.helpers import Track, utils


class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.warned = False
        # Cookie: bota /cookie ile yüklenir, MongoDB'de saklanır (Railway yeniden başlasa da kaybolmaz)
        self.cookie_file = "KumsalTR/cookies/yt_cookie.txt"
        self.cookie_dead = False   # cookie de engellendiyse tekrar tekrar denenmesin
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.search_cache = {} # Cache for search results
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        ]
        # Cookiesiz çalışan istemciler: mweb, tv ve web_safari bgutil PO token ile çalışır;
        # android_vr ise ek cookiesiz yedek istemcidir.
        self.pot_clients = ["mweb", "tv", "web_safari", "android_vr"]
        # YouTube engellerse SoundCloud yedeği için şarkı bilgisi: id -> (tam başlık, kanal, süre sn)
        self.meta: dict[str, tuple[str, str, int]] = {}
        # YouTube IP'yi engellediğinde bir süre doğrudan yedeğe geç (her şarkıda dakikalarca bekletmesin)
        self.blocked_until = 0.0

    def remember(self, vid: str, title: str, channel: str, duration_sec) -> None:
        if not vid:
            return
        if len(self.meta) > 2000:
            for old in list(self.meta.keys())[:1000]:
                self.meta.pop(old, None)
        try:
            dur = int(duration_sec or 0)
        except (TypeError, ValueError):
            dur = 0
        self.meta[vid] = (title or "", channel or "", dur)

    def pot_base(self) -> str:
        return (config.POT_PROVIDER_URL or "").strip() or "http://127.0.0.1:4416"

    def extractor_args(self, clients: list[str] | None = None, use_pot: bool = True) -> dict:
        """
        Cookiesiz YouTube: bgutil eklentisi her video için PO token üretir.
        Cookie bu ayarlara karıştırılmaz — ayrı denemede kullanılır.
        """
        yt_args: dict[str, list[str]] = {
            "player_client": list(clients or self.pot_clients),
        }
        if config.PO_TOKEN:
            yt_args["po_token"] = list(config.PO_TOKEN)
        if config.VISITOR_DATA:
            yt_args["visitor_data"] = [config.VISITOR_DATA]

        args: dict[str, dict] = {"youtube": yt_args}
        if use_pot:
            args["youtubepot-bgutilhttp"] = {"base_url": [self.pot_base()]}
            for candidate in (
                os.path.expanduser("~/bgutil-ytdlp-pot-provider/server"),
                "/root/bgutil-ytdlp-pot-provider/server",
            ):
                if os.path.isdir(candidate):
                    args["youtubepot-bgutilscript"] = {"server_home": [candidate]}
                    break
        return args

    def ydl_opts(
        self,
        *,
        cookie: bool = False,
        clients: list[str] | None = None,
        fmt: str = "bestaudio/best",
        extra: dict | None = None,
    ) -> dict:
        import shutil

        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "format": fmt,
            "socket_timeout": 15,
            "extractor_args": self.extractor_args(clients),
            "http_headers": {
                "User-Agent": random.choice(self.user_agents),
                "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
                "Connection": "keep-alive",
            },
        }
        deno = shutil.which("deno")
        node = shutil.which("node")
        if deno:
            opts["js_runtimes"] = {"deno": {"path": deno}}
        elif node:
            opts["js_runtimes"] = {"node": {"path": node}}
        if cookie and self.has_cookie():
            opts["cookiefile"] = self.cookie_file
        proxy = getattr(config, "PROXY", "")
        if proxy:
            opts["proxy"] = proxy
        if extra:
            opts.update(extra)
        return opts

    async def _ping_provider_info(self, base: str | None = None) -> dict | None:
        url = f"{(base or self.pot_base()).rstrip('/')}/ping"
        try:
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                async with s.get(url) as r:
                    if r.status < 500:
                        try:
                            return await r.json()
                        except Exception:
                            return {"status": r.status}
        except Exception:
            pass
        return None

    async def _ping_provider(self, base: str | None = None) -> bool:
        return (await self._ping_provider_info(base)) is not None

    async def ensure_provider(self) -> bool:
        """bgutil HTTP sunucusu ayaktaysa kullan; değilse yerelde başlatmayı dene."""
        if await self._ping_provider():
            logger.info(f"PO token sağlayıcısı hazır: {self.pot_base()}")
            return True

        import shutil
        import subprocess

        node = shutil.which("node")
        candidates = [
            os.path.expanduser("~/bgutil-ytdlp-pot-provider/server/build/main.js"),
            "/root/bgutil-ytdlp-pot-provider/server/build/main.js",
            os.path.join(os.getcwd(), "bgutil-ytdlp-pot-provider", "server", "build", "main.js"),
        ]
        script = next((p for p in candidates if os.path.isfile(p)), None)
        if not node or not script:
            logger.warning(
                "PO token sağlayıcısı yok. YouTube cookiesiz çalışmayabilir "
                "(Docker/Railway'de start betiği bgutil'i açmalı)."
            )
            return False

        logger.info("PO token sağlayıcısı başlatılıyor...")
        try:
            logf = open("bgutil.log", "ab")
            subprocess.Popen(
                [node, script],
                stdout=logf,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except Exception as e:
            logger.warning(f"PO token sağlayıcısı başlatılamadı: {e}")
            return False

        for _ in range(15):
            await asyncio.sleep(1)
            if await self._ping_provider():
                logger.info("PO token sağlayıcısı hazır.")
                return True
        logger.warning("PO token sağlayıcısı zamanında ayağa kalkmadı.")
        return False

    # ─── Otomatik cookie yönetimi ───
    def has_cookie(self) -> bool:
        return (not self.cookie_dead) and os.path.isfile(self.cookie_file) and os.path.getsize(self.cookie_file) > 0

    @staticmethod
    def _normalize_cookie(text: str) -> str:
        """Kopyala-yapıştırda bozulan Netscape formatını (tab yerine boşluk) düzeltir."""
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                lines.append(line)
                continue
            parts = line.split(None, 6)
            lines.append("\t".join(parts) if len(parts) >= 7 else line)
        return "\n".join(lines) + "\n"

    async def load_cookie(self, db) -> bool:
        """Açılışta veritabanındaki cookie'yi dosyaya yazar."""
        try:
            doc = await db.cache.find_one({"_id": "yt_cookie"})
        except Exception as e:
            logger.warning(f"Cookie veritabanından okunamadı: {e}")
            return False
        if not doc or not doc.get("data"):
            return False
        if doc.get("dead"):
            # Daha önce YouTube tarafından reddedildi — her açılışta tekrar deneyip uyarı atmasın
            self.cookie_dead = True
            logger.info("Kayıtlı YouTube cookie'si daha önce reddedilmiş; kullanılmıyor.")
            return False
        os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
        with open(self.cookie_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(doc["data"])
        self.cookie_dead = False
        logger.info("YouTube cookie veritabanından yüklendi (yedek olarak kullanılacak).")
        return True

    async def save_cookie(self, db, text: str) -> int:
        """Cookie'yi doğrular, dosyaya ve veritabanına kaydeder. YouTube cookie satırı sayısını döner."""
        data = self._normalize_cookie(text)
        count = sum(1 for l in data.splitlines() if "youtube.com" in l and not l.startswith("#"))
        if not count:
            return 0
        os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
        with open(self.cookie_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
        await db.cache.update_one(
            {"_id": "yt_cookie"}, {"$set": {"data": data}, "$unset": {"dead": ""}}, upsert=True
        )
        self.cookie_dead = False
        self.warned = False
        return count

    async def delete_cookie(self, db) -> None:
        try:
            os.remove(self.cookie_file)
        except FileNotFoundError:
            pass
        await db.cache.delete_one({"_id": "yt_cookie"})
        self.cookie_dead = False
        self.warned = False

    async def _mark_cookie_dead(self) -> None:
        """Reddedilen cookie'yi kalıcı olarak devre dışı bırakır (yeniden başlatmada geri gelmez)."""
        self.cookie_dead = True
        try:
            os.remove(self.cookie_file)
        except OSError:
            pass
        try:
            from KumsalTR import db
            await db.cache.update_one({"_id": "yt_cookie"}, {"$set": {"dead": True}})
        except Exception as e:
            logger.warning(f"Cookie durumu veritabanına yazılamadı: {e}")

    def cookie_opts(self) -> dict:
        """İndirici yedek yolu — çalarken PO token denemesine karıştırılmaz."""
        return {"cookiefile": self.cookie_file} if self.has_cookie() else {}

    async def _notify_block(self, text: str) -> None:
        """YouTube engelini bot sahibine bir kez bildirir."""
        if self.warned:
            return
        self.warned = True
        try:
            from KumsalTR import app
            await app.send_message(config.LOGGER_ID, text)
        except Exception:
            pass

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    async def search(self, query: str, m_id: int, user: Optional[str] = None, user_id: int = 0, video: bool = False) -> Track | None:
        cache_key = f"{query}_{video}"
        if cache_key in self.search_cache:
            cached = self.search_cache[cache_key]
            # Create a new Track instance with updated user/message info
            return Track(
                id=cached.id,
                channel_name=cached.channel_name,
                duration=cached.duration,
                duration_sec=cached.duration_sec,
                message_id=m_id,
                title=cached.title,
                thumbnail=cached.thumbnail,
                url=cached.url,
                view_count=cached.view_count,
                user=user,
                user_id=user_id,
                video=video,
            )

        try:
            results = await VideosSearch(query, limit=1, with_live=False).next()
        except Exception as e:
            logger.warning(f"YouTube arama hatası: {e}")
            return None
        if results and results.get("result"):
            data = results["result"][0]
            vid = data.get("id")
            if not vid:
                return None
            self.remember(vid, data.get("title"), (data.get("channel") or {}).get("name"), utils.to_seconds(data.get("duration")))
            thumbs = data.get("thumbnails") or [{}]
            thumb = ((thumbs[-1] or {}).get("url") or "").split("?")[0]
            track = Track(
                id=vid,
                channel_name=(data.get("channel") or {}).get("name") or "",
                duration=data.get("duration") or "0:00",
                duration_sec=utils.to_seconds(data.get("duration")),
                message_id=m_id,
                title=(data.get("title") or "YouTube")[:25],
                thumbnail=thumb,
                url=data.get("link") or self.base + vid,
                view_count=(data.get("viewCount") or {}).get("short"),
                user=user,
                user_id=user_id,
                video=video,
            )
            if len(self.search_cache) > 200:
                for old in list(self.search_cache.keys())[:100]:
                    self.search_cache.pop(old, None)
            self.search_cache[cache_key] = track
            return track
        return None

    async def related(self, prev: Track, exclude: set | None = None) -> Track | None:
        """Otomatik oynatma için önceki şarkıya benzer bir şarkı bulur."""
        exclude = set(exclude or ()) | {prev.id}
        artist = (prev.channel_name or "")
        for junk in (" - Topic", "VEVO", "Official", "Music"):
            artist = artist.replace(junk, "")
        artist = artist.strip()
        queries = [
            f"{artist} şarkıları" if artist else prev.title,
            f"{prev.title} benzeri şarkılar",
            f"{artist} {random.choice(['mix', 'popüler', 'en iyi şarkılar'])}",
        ]
        random.shuffle(queries)
        for q in queries:
            try:
                results = await VideosSearch(q, limit=10, with_live=False).next()
            except Exception as e:
                logger.warning(f"Otomatik oynatma araması başarısız: {e}")
                continue
            candidates = []
            for data in (results or {}).get("result", []):
                vid = data.get("id")
                sec = int(utils.to_seconds(data.get("duration")) or 0)
                if not vid or vid in exclude or not (60 <= sec <= config.DURATION_LIMIT):
                    continue
                candidates.append((data, sec))
            if not candidates:
                continue
            data, sec = random.choice(candidates[:5])
            self.remember(data.get("id"), data.get("title"), (data.get("channel") or {}).get("name"), sec)
            thumbs = data.get("thumbnails") or [{}]
            thumb = ((thumbs[-1] or {}).get("url") or "").split("?")[0]
            return Track(
                id=data.get("id"),
                channel_name=(data.get("channel") or {}).get("name") or "",
                duration=data.get("duration") or "0:00",
                duration_sec=sec,
                title=(data.get("title") or "YouTube")[:25],
                thumbnail=thumb,
                url=data.get("link") or self.base + data.get("id"),
                view_count=(data.get("viewCount") or {}).get("short"),
                user="📻 Otomatik",
                user_id=0,
                video=prev.video,
            )
        return None

    async def playlist(self, limit: int, user: str, user_id: int, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in (plist or {}).get("videos", [])[:limit]:
                vid = data.get("id")
                if not vid:
                    continue
                self.remember(vid, data.get("title"), (data.get("channel") or {}).get("name"), utils.to_seconds(data.get("duration")))
                thumbs = data.get("thumbnails") or [{}]
                thumb = ((thumbs[-1] or {}).get("url") or "").split("?")[0]
                link = (data.get("link") or self.base + vid).split("&list=")[0]
                tracks.append(
                    Track(
                        id=vid,
                        channel_name=(data.get("channel") or {}).get("name") or "",
                        duration=data.get("duration") or "0:00",
                        duration_sec=utils.to_seconds(data.get("duration")),
                        title=(data.get("title") or "YouTube")[:25],
                        thumbnail=thumb,
                        url=link,
                        user=user,
                        user_id=user_id,
                        view_count="",
                        video=video,
                    )
                )
        except Exception as e:
            logger.warning(f"Playlist alınamadı: {e}")
        return tracks

    async def resolve_spotify(self, url: str) -> str | None:
        if "spotify.com/track/" in url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            if match := re.search(r"<title>(.*?) - song by (.*?) \| Spotify</title>", html):
                                return f"{match.group(1)} {match.group(2)}"
                            if match := re.search(r"<title>(.*?) \| Spotify</title>", html):
                                title = match.group(1).replace(" | Spotify", "")
                                return title
            except: pass
        return None


    async def _fallback_query(self, video_id: str) -> tuple[str, int]:
        """YouTube id'sinden SoundCloud'da aranacak metni bulur."""
        title, channel, dur = self.meta.get(video_id, ("", "", 0))
        if not title:
            try:
                res = await VideosSearch(video_id, limit=1, with_live=False).next()
                data = ((res or {}).get("result") or [{}])[0]
                if data.get("id") == video_id:
                    title = data.get("title") or ""
                    channel = (data.get("channel") or {}).get("name") or ""
                    dur = int(utils.to_seconds(data.get("duration")) or 0)
            except Exception as e:
                logger.warning(f"Yedek arama için başlık alınamadı: {e}")
        if not title:
            return "", 0
        q = re.sub(r"[\(\[][^\)\]]*(official|video|lyric|audio|clip|hd|4k|klip|sözleri)[^\)\]]*[\)\]]", "", title, flags=re.I)
        q = re.sub(r"\s+", " ", q).strip()
        artist = channel
        for junk in (" - Topic", "VEVO", "Official", "Music", "Records"):
            artist = artist.replace(junk, "")
        artist = artist.strip()
        if artist and artist.lower() not in q.lower() and "-" not in q:
            q = f"{artist} {q}"
        return q, dur

    async def soundcloud(self, video_id: str) -> str | None:
        """YouTube engelliyken aynı şarkıyı SoundCloud'dan indirir (cookie/IP sorunu yok)."""
        query, want = await self._fallback_query(video_id)
        if not query:
            return None
        base_path = f"downloads/{video_id}"

        def _dl():
            base = {
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 15,
                "noplaylist": True,
                "format": "bestaudio/best",
                "outtmpl": f"{base_path}.%(ext)s",
            }
            proxy = getattr(config, "PROXY", "")
            if proxy:
                base["proxy"] = proxy
            with yt_dlp.YoutubeDL({**base, "extract_flat": False}) as ydl:
                info = ydl.extract_info(f"scsearch5:{query}", download=False)
            pick = None
            for e in (info or {}).get("entries") or []:
                if not e:
                    continue
                d = int(e.get("duration") or 0)
                fmt_ids = " ".join(str(f.get("format_id", "")) for f in (e.get("formats") or []))
                if fmt_ids and all("preview" in x for x in fmt_ids.split()):
                    continue  # yalnızca 30 sn önizleme
                if d and d < 45:
                    continue
                if want and d and abs(d - want) > max(25, want * 0.15):
                    continue
                pick = e
                break
            if not pick:
                return None
            with yt_dlp.YoutubeDL(base) as ydl:
                got = ydl.extract_info(pick.get("webpage_url") or pick.get("url"), download=True)
                fn = ydl.prepare_filename(got)
            if fn and os.path.exists(fn) and os.path.getsize(fn) > 1024:
                return fn
            for ext in ["mp3", "opus", "m4a", "webm", "ogg"]:
                p = f"{base_path}.{ext}"
                if os.path.exists(p) and os.path.getsize(p) > 1024:
                    return p
            return None

        try:
            path = await asyncio.wait_for(asyncio.to_thread(_dl), timeout=90)
        except Exception as e:
            logger.warning(f"SoundCloud yedeği başarısız ({video_id}): {e}")
            return None
        if path:
            logger.info(f"{video_id} SoundCloud yedeğinden çalınıyor: {query}")
        return path

    async def download(self, video_id: str, video: bool = False) -> str | None:
        url = self.base + video_id
        os.makedirs("downloads", exist_ok=True)
        base_path = f"downloads/{video_id}"

        # Önbellekte varsa doğrudan yerel dosyayı döndür
        exts = ["mp4", "mkv", "webm"] if video else ["webm", "m4a", "mp3", "opus", "ogg", "mp4"]
        for ext in exts:
            candidate = f"{base_path}.{ext}"
            if os.path.exists(candidate) and os.path.getsize(candidate) > 1024:
                return candidate

        import time
        # YouTube kısa süre önce engellediyse önce SoundCloud'u dene (beklemeden çalsın)
        if time.time() < self.blocked_until:
            sc = await self.soundcloud(video_id)
            if sc:
                return sc

        # PO token sunucusu düşmüşse indirmeden önce uyandır
        if not await self._ping_provider():
            await self.ensure_provider()

        if video:
            fmt = "best[ext=mp4][height<=?720]/best[height<=?720]/best"
        else:
            fmt = "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best"

        # Önce cookiesiz (bgutil PO token: mweb, tv, web_safari + android_vr). Cookie yalnızca yedek.
        attempts: list[tuple[str, bool, list[str]]] = [
            ("pot", False, ["mweb", "tv", "web_safari", "android_vr"]),
            ("pot", False, ["tv_embedded", "web_embedded", "ios", "android_vr"]),
            ("pot", False, ["android_vr", "web_safari", "mweb"]),
        ]
        if self.has_cookie():
            attempts.append(("cookie", True, ["tv", "web", "mweb"]))

        blocked = False
        cookie_blocked = False
        last_err = ""
        skip_pot = False  # IP bot kontrolüne takıldıysa diğer PO denemeleri de takılır; boşuna bekleme

        for attempt, (mode, use_cookie, clients) in enumerate(attempts, start=1):
            if mode == "pot" and skip_pot:
                continue
            extra = {
                "outtmpl": f"downloads/{video_id}.%(ext)s",
                "concurrent_fragment_downloads": 8,
            }
            opts = self.ydl_opts(cookie=use_cookie, clients=clients, fmt=fmt, extra=extra)
            try:
                def _dl(_opts=opts):
                    with yt_dlp.YoutubeDL(_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        fn = ydl.prepare_filename(info)
                        if fn and os.path.exists(fn) and os.path.getsize(fn) > 1024:
                            return fn
                        for ext in ["webm", "m4a", "mp3", "opus", "ogg", "mp4", "mkv"]:
                            p = f"{base_path}.{ext}"
                            if os.path.exists(p) and os.path.getsize(p) > 1024:
                                return p
                        if info.get("url"):
                            return info["url"]
                        req = info.get("requested_formats") or [{}]
                        return req[0].get("url")

                res_path = await asyncio.wait_for(asyncio.to_thread(_dl), timeout=45)
                if res_path:
                    if mode == "pot":
                        self.warned = False
                    self.blocked_until = 0.0
                    return res_path
            except Exception as e:
                err = str(e).lower()
                last_err = str(e)
                logger.error(f"yt-dlp hatası ({mode}, deneme {attempt}/{len(attempts)}): {e}")
                bot_check = (
                    "sign in to confirm" in err
                    or "not a bot" in err
                    or "po token" in err
                    or "login required" in err
                )
                if bot_check:
                    if mode == "pot":
                        blocked = True
                        skip_pot = True
                    else:
                        cookie_blocked = True
                if bot_check or "403" in err or "429" in err or "timed out" in err or "format is not available" in err:
                    continue
                if mode == "pot":
                    continue
                break

        if blocked or cookie_blocked:
            self.blocked_until = time.time() + 15 * 60

        if cookie_blocked:
            await self._mark_cookie_dead()

        sc = await self.soundcloud(video_id)
        if sc:
            if blocked or cookie_blocked:
                await self._notify_block(
                    "<b>ℹ️ YouTube bu sunucunun IP'sini engelliyor.</b>\n"
                    "Bot şarkıları otomatik olarak <b>SoundCloud</b> yedeğinden çalmaya devam ediyor; "
                    "bir şey yapmanıza gerek yok. 15 dakikada bir YouTube yeniden denenir.\n"
                    "Tam YouTube desteği için config.py'de <code>PROXY</code> ayarlayabilirsiniz."
                )
            return sc

        reason = ""
        if last_err:
            short = re.sub(r"\x1b\[[0-9;]*m", "", last_err).replace("<", "&lt;").replace(">", "&gt;")[:300]
            reason = f"\n\n<b>Son hata:</b> <code>{short}</code>"
        if cookie_blocked:
            # Cookie denemesine yalnızca 3 PO token denemesi de başarısız olunca gelinir.
            await self._mark_cookie_dead()
            await self._notify_block(
                "<b>⚠️ YouTube bu sunucunun IP'sini engelliyor.</b>\n"
                "Cookiesiz PO token denemeleri başarısız oldu, yedek cookie de reddedildi "
                "(süresi dolmuş ya da YouTube cookie'yi Railway IP'si yüzünden geçersiz saymış).\n\n"
                "<b>Çözüm:</b>\n"
                "• Gizli sekmede YouTube'a girip <code>cookies.txt</code> alın, sekmeyi kapatın, "
                "dosyaya yanıt vererek <code>/cookie</code> yazın.\n"
                "• Kalıcı çözüm: config.py'de <code>PROXY</code> alanına residential proxy girin."
                + reason
            )
        elif blocked:
            await self._notify_block(
                "<b>⚠️ YouTube bu sunucunun IP'sini bot sandı.</b>\n"
                "Cookiesiz PO token denendi. Railway gibi datacenter IP'lerinde "
                "YouTube bazen yine de engeller; bot tekrar denemeye devam eder.\n"
                "Kalıcı çözüm için config.py'de <code>PROXY</code> ayarlayabilirsiniz."
                + reason
            )
        logger.warning(f"{video_id} için ses bağlantısı alınamadı.")
        return None
