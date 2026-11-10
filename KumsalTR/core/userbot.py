# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of KumsalTR

from pyrogram import Client

from KumsalTR import config, logger


class Userbot:
    def __init__(self):
        """
        Asistan userbotları başlatır.
        Birden fazla yardımcı hesap çalıştırmak için kullanılır.
        """

        self.clients = []
        self.one = None
        self.two = None
        self.three = None
        self.bot_session_warning = None

        mapping = (
            ("one", "SESSION1", 1),
            ("two", "SESSION2", 2),
            ("three", "SESSION3", 3),
        )

        for attr, string_key, num in mapping:
            session = (getattr(config, string_key, None) or "").strip()
            if not session:
                continue
            if len(session) < 50:
                logger.error(
                    f"SESSION{'' if num == 1 else num} çok kısa — geçersiz string, atlanıyor."
                )
                continue
            client = Client(
                name=f"LoncaMusicUB{num}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=session,
                in_memory=True,
                no_updates=True,
            )
            setattr(self, attr, client)

    async def boot_client(self, num: int, ub: Client):
        """
        Asistanı başlatır ve ilk ayarları yapar.
        """
        if ub is None:
            return

        try:
            await ub.start()
        except Exception as e:
            kind = type(e).__name__
            logger.error(f"Asistan {num} başlatılamadı: {kind}: {e}")
            await self._notify_session_dead(num, kind)
            return

        if getattr(ub.me, "is_bot", False):
            bot_uname = f"@{ub.me.username}" if getattr(ub.me, "username", None) else str(ub.me.id)
            self.bot_session_warning = bot_uname
            logger.error(
                f"❌ HATA: Asistan {num} ({bot_uname}) bir BOT hesabı! "
                "Telegram'da botlar sesli sohbete katılamaz. "
                "Lütfen normal bir kullanıcı hesabı (telefon numarası) ile /sessional veya session_al.bat kullanarak SESSION alın."
            )
            try:
                await ub.stop()
            except Exception:
                pass
            await self._notify_session_dead(
                num,
                f"Bot hesabı ({bot_uname}) asistan olamaz! Normal telefon numaralı hesap ile /sessional kullanın.",
            )
            return

        ub.id = ub.me.id
        ub.name = ub.me.first_name
        ub.username = ub.me.username
        ub.mention = ub.me.mention

        try:
            await ub.send_message(config.LOGGER_ID, "✅ Asistan Başlatıldı")
        except Exception as e:
            logger.warning(
                f"Asistan {num} log grubuna yazamadı ({type(e).__name__}: {e}). "
                "Asistan çalışıyor; hesabı log grubuna ekleyin."
            )

        self.clients.append(ub)

        logger.info(f"Asistan {num} başarıyla başlatıldı → @{ub.username}")

    async def _notify_session_dead(self, num: int, err: str) -> None:
        try:
            from KumsalTR import app

            await app.send_message(
                config.LOGGER_ID,
                f"<b>❌ Asistan {num} başlatılamadı.</b>\n"
                f"<code>{err}</code>\n\n"
                "SESSION geçersiz ya da oturum sonlandırılmış.\n"
                "Bota özelden <code>/sessional</code> yazarak yenisini alın, "
                f"sonra <code>config.py</code> içindeki <b>SESSION{'' if num == 1 else num}</b> "
                "satırına yapıştırıp Railway'de yeniden deploy edin.",
            )
        except Exception:
            pass

    async def boot(self):
        """
        Asistanları başlatır.
        """

        if self.one:
            await self.boot_client(1, self.one)

        if self.two:
            await self.boot_client(2, self.two)

        if self.three:
            await self.boot_client(3, self.three)

        if not self.clients:
            logger.error(
                "Hiçbir asistan başlatılamadı! Bot açık ama müzik çalamaz. "
                "Bota özelden /sessional yazarak yeni SESSION alın."
            )

    async def exit(self):
        """
        Asistanları kapatır.
        """

        for client in self.clients:
            try:
                await client.stop()
            except Exception:
                pass

        logger.info("⛔ Asistanlar durduruldu.")
