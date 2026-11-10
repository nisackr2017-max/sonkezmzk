# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of KumsalTR

import asyncio

import pyrogram
from pyrogram import filters
from pyrogram.errors import FloodWait

from KumsalTR import config, logger


class Bot(pyrogram.Client):
    def __init__(self):
        _pm = pyrogram.enums.ParseMode
        parse_mode = getattr(_pm, "HTML", None) or getattr(_pm, "DEFAULT", None)
        super().__init__(
            name="LoncaMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=parse_mode,
            max_concurrent_transmissions=7,
            in_memory=True,
            link_preview_options=pyrogram.types.LinkPreviewOptions(is_disabled=True),
        )

        self.owner = config.OWNER_ID
        self.logger = config.LOGGER_ID

        # Dinamik kullanıcı listeleri
        self.bl_users: set[int] = set()
        self.sudoers: set[int] = {self.owner}

        # Dinamik filtreler
        self.blacklist_filter = filters.create(
            lambda _, __, update: bool(
                getattr(getattr(update, "from_user", None), "id", None) in self.bl_users
            )
        )
        self.sudo_filter = filters.create(
            lambda _, __, update: bool(
                getattr(getattr(update, "from_user", None), "id", None) in self.sudoers
            )
        )

    async def send_message(self, *args, **kwargs):
        """Telegram hız sınırına (FloodWait) takılınca bekleyip tekrar dener.
        Özellikle toplu etiketlemede mesajların kaybolmasını önler."""
        for _ in range(3):
            try:
                return await super().send_message(*args, **kwargs)
            except FloodWait as e:
                wait = int(getattr(e, "value", 5) or 5)
                if wait > 120:
                    raise
                logger.warning(f"FloodWait: {wait} sn bekleniyor...")
                await asyncio.sleep(wait + 1)
        return await super().send_message(*args, **kwargs)

    async def boot(self):
        last: Exception | None = None
        for attempt in range(1, 4):
            try:
                await super().start()
                last = None
                break
            except Exception as e:
                last = e
                logger.warning(
                    f"Bot Telegram'a bağlanamadı ({attempt}/3): {type(e).__name__}: {e}"
                )
                await asyncio.sleep(3 * attempt)
        if last:
            raise SystemExit(f"Telegram bot başlatılamadı: {last}") from last

        self.id = self.me.id
        self.name = "Lonca Music"
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(
                self.logger,
                "✨ <b>Lonca Music Bot Başlatıldı</b>\n\n"
                "⚡ Sistem Aktif\n"
                "🎧 Müzik Motoru Hazır\n"
                "🚀 Bot başarıyla çalışıyor.",
            )
        except Exception as ex:
            logger.warning(f"Log grubuna başlangıç mesajı gidemedi: {type(ex).__name__}: {ex}")

        try:
            get = await self.get_chat_member(self.logger, self.id)
            if get.status not in (
                pyrogram.enums.ChatMemberStatus.ADMINISTRATOR,
                pyrogram.enums.ChatMemberStatus.OWNER,
            ):
                logger.warning("⚠️ Bot log grubunda ADMIN değil! Lütfen botu log grubunda yönetici yapın.")
        except Exception as ex:
            logger.warning(
                f"⚠️ Log grubuna erişilemedi (LOG ID: {self.logger}): {ex}. "
                "Bot çalışmaya devam ediyor ancak log grubuna ekleyip admin yapmanız önerilir."
            )

        logger.info(f"✨ Lonca Music Bot başlatıldı → @{self.username}")

    async def exit(self):
        await super().stop()
        logger.info("⛔ Lonca Music Bot durduruldu.")
