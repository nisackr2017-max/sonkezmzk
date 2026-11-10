# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam

import asyncio
import importlib
import os
import signal

from aiohttp import web
from pyrogram import idle

from KumsalTR import anon, app, config, db, logger, stop, tasks, userbot, yt
from KumsalTR.core.dir import cleanup_downloads
from KumsalTR.plugins import all_modules

READY = False


def load_plugins() -> None:
    for module in all_modules:
        importlib.import_module(f"KumsalTR.plugins.{module}")

    # Ek modüller
    for extra in ("KumsalTR.Utah", "KumsalTR.av"):
        try:
            importlib.import_module(extra)
        except Exception as exc:
            logger.warning(f"Ek modül yüklenemedi: {extra} -> {exc}")


async def start_webserver():
    """Railway PORT'u hemen bağla; aksi halde sağlık kontrolü container'ı öldürür."""
    webapp = web.Application()

    async def handle_ping(_request):
        text = "ok" if READY else "starting"
        return web.Response(text=text)

    webapp.router.add_get("/", handle_ping)
    webapp.router.add_get("/health", handle_ping)
    runner = web.AppRunner(webapp)
    await runner.setup()
    port = int(os.environ.get("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Sağlık sunucusu dinliyor: 0.0.0.0:{port}")


async def watch_runtime() -> None:
    while True:
        await asyncio.sleep(90)
        if not await yt._ping_provider():
            logger.warning("PO token sağlayıcısı düştü, yeniden başlatılıyor...")
            await yt.ensure_provider()
        removed = cleanup_downloads()
        if removed:
            logger.info(f"İndirme önbelleği temizlendi ({removed} dosya).")


async def main() -> None:
    global READY
    # PORT'u Telegram/Mongo'dan önce aç — Railway 60sn kuralı
    await start_webserver()
    load_plugins()

    await db.connect()
    await yt.load_cookie(db)

    app.bl_users.update(await db.get_blacklisted())
    app.sudoers.update(await db.get_sudoers())
    app.sudoers.add(app.owner)

    await app.boot()
    await userbot.boot()
    await anon.boot()

    pot_ok = await yt.ensure_provider()
    if pot_ok:
        logger.info("YouTube: cookiesiz PO token (bgutil) hazır.")
    else:
        logger.warning("YouTube: PO token sağlayıcısı yok; cookiesiz indirme başarısız olabilir.")

    tasks.append(asyncio.create_task(watch_runtime()))

    loop = asyncio.get_running_loop()

    def _on_signal():
        logger.info("Kapatma sinyali alındı (Railway deploy/stop).")
        asyncio.create_task(stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _on_signal)
        except (NotImplementedError, RuntimeError):
            pass

    READY = True
    logger.info("Lonca Music tamamen başlatıldı ve sağlık sunucusu aktifleştirildi.")
    await idle()
    await stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
