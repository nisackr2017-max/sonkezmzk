# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of KumsalTR


import asyncio
import os
import time

from pyrogram import types

from KumsalTR import config
from KumsalTR.helpers import Media, buttons, utils


class Telegram:
    def __init__(self):
        self.active = []
        self.events = {}
        self.last_edit = {}
        self.active_tasks = {}
        self.sleep = 5

    def get_media(self, msg: types.Message) -> bool:
        return any([msg.video, msg.audio, msg.document, msg.voice])

    async def download(self, msg: types.Message, sent: types.Message) -> Media | None:
        lang = getattr(sent, "lang", None) or getattr(msg, "lang", None) or {}
        if not isinstance(lang, dict):
            lang = {}
        msg_id = sent.id
        event = asyncio.Event()
        self.events[msg_id] = event
        self.last_edit[msg_id] = 0
        start_time = time.time()

        media = msg.audio or msg.voice or msg.video or msg.document
        if not media:
            await sent.edit_text(lang.get("play_usage", "Medya bulunamadı."))
            return None
        file_id = getattr(media, "file_unique_id", None) or "tgfile"
        name = getattr(media, "file_name", None) or ""
        if not name:
            if msg.voice:
                name = "voice.ogg"
            elif msg.audio:
                name = "audio.mp3"
            elif msg.video:
                name = "video.mp4"
            else:
                name = "file.bin"
        file_ext = (name.rsplit(".", 1)[-1] or "bin")[:8]
        file_size = getattr(media, "file_size", 0) or 0
        file_title = getattr(media, "title", None) or getattr(media, "file_name", None) or "Telegram File"
        duration = int(getattr(media, "duration", 0) or 0)
        mime = getattr(media, "mime_type", "") or ""
        video = bool(msg.video or mime.startswith("video/"))

        if duration > config.DURATION_LIMIT:
            await sent.edit_text(lang.get("play_duration_limit", "Song too long").format(config.DURATION_LIMIT // 60))
            return None

        if file_size > 2048 * 1024 * 1024:
            await sent.edit_text(lang.get("dl_limit", "File too large"))
            return None

        async def progress(current, total):
            if event.is_set():
                return

            now = time.time()
            if now - self.last_edit[msg_id] < self.sleep:
                return

            self.last_edit[msg_id] = now
            percent = (current * 100 / total) if total else 0
            speed = current / max(now - start_time, 1e-6)
            remain = ((total - current) / speed) if speed else 0
            eta = utils.format_eta(int(remain))
            text = lang.get("dl_progress", "Downloading...").format(
                utils.format_size(current),
                utils.format_size(total),
                percent,
                utils.format_size(speed),
                eta,
            )

            try:
                await sent.edit_text(
                    text, reply_markup=buttons.cancel_dl(lang.get("cancel", "Cancel"))
                )
            except Exception:
                pass

        try:
            file_path = f"downloads/{file_id}.{file_ext}"
            if not os.path.exists(file_path):
                if file_id in self.active:
                    await sent.edit_text(lang.get("dl_active", "Download already active"))
                    return None

                self.active.append(file_id)
                task = asyncio.create_task(
                    msg.download(file_name=file_path, progress=progress)
                )
                self.active_tasks[msg_id] = task
                await task
                self.active.remove(file_id)
                self.active_tasks.pop(msg_id, None)
                await sent.edit_text(
                    lang.get("dl_complete", "Download complete").format(round(time.time() - start_time, 2))
                )

            return Media(
                id=file_id,
                duration=time.strftime("%M:%S", time.gmtime(duration)),
                duration_sec=duration,
                file_path=file_path,
                message_id=sent.id,
                url=msg.link,
                title=file_title[:25],
                video=video,
            )
        except asyncio.CancelledError:
            return None
        finally:
            self.events.pop(msg_id, None)
            self.last_edit.pop(msg_id, None)
            self.active = [f for f in self.active if f != file_id]

    async def cancel(self, query: types.CallbackQuery):
        lang = getattr(query, "lang", {})
        event = self.events.get(query.message.id)
        task = self.active_tasks.pop(query.message.id, None)
        if event:
            event.set()

        if task and not task.done():
            task.cancel()
        if event or task:
            await query.edit_message_text(
                lang.get("dl_cancel", "Cancelled").format(query.from_user.mention)
            )
        else:
            await query.answer(lang.get("dl_not_found", "Not found"), show_alert=True)
