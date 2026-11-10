# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of KumsalTR

from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported)
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from KumsalTR import app, config, db, lang, logger, queue, userbot, yt
from KumsalTR.helpers import Media, Track, buttons, utils


EFFECTS: dict[str, tuple[str, str | None]] = {
    "normal": ("🔄 Normal", None),
    "bass": ("🔊 Bass Boost", "equalizer=f=60:width_type=h:width=50:g=10"),
    "nightcore": ("⚡ Nightcore", "asetrate=48000*1.22,aresample=48000,atempo=1.05"),
    "slowed": ("🌙 Slowed + Reverb", "asetrate=48000*0.85,aresample=48000,aecho=0.8:0.88:60:0.4"),
    "8d": ("🎧 8D Ses", "apulsator=hz=0.125"),
    "karaoke": ("🎤 Karaoke", "stereotools=mlev=0.03"),
}


class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []
        self._busy: set[int] = set()
        self._fail_streak: dict[int, int] = {}
        self.effects: dict[int, str] = {}
        self.sleep_timers: dict[int, object] = {}

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)
        try:
            return await client.pause(chat_id)
        except Exception as e:
            logger.warning(f"pause hatası ({chat_id}): {e}")
            return False

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)
        try:
            return await client.resume(chat_id)
        except Exception as e:
            logger.warning(f"resume hatası ({chat_id}): {e}")
            return False

    async def stop(self, chat_id: int) -> None:
        self._fail_streak.pop(chat_id, None)
        self.effects.pop(chat_id, None)
        timer_task = self.sleep_timers.pop(chat_id, None)
        if timer_task and hasattr(timer_task, "cancel"):
            try:
                timer_task.cancel()
            except Exception:
                pass
        try:
            queue.clear(chat_id)
            await db.remove_call(chat_id)
        except Exception:
            pass
        try:
            client = await db.get_assistant(chat_id)
            await client.leave_call(chat_id, close=False)
        except Exception:
            pass

    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: Media | Track,
        seek_time: int = 0,
    ) -> bool:
        """True: yayın başladı veya terminal hata (durduruldu). False: bu şarkı atlanmalı."""
        _lang = await lang.get_lang(chat_id)

        if not media.file_path:
            try:
                await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            except Exception:
                pass
            if chat_id not in self._busy:
                await self.play_next(chat_id, ended=True)
            return False

        try:
            client = await db.get_assistant(chat_id)
        except Exception as e:
            logger.error(f"Asistan yok ({chat_id}): {e}")
            try:
                await message.edit_text(
                    "<b>❌ Asistan bağlı değil.</b> Özelden <code>/sessional</code> ile SESSION alın."
                )
            except Exception:
                pass
            return True

        ff_parts = []
        if seek_time > 1:
            ff_parts.append(f"-ss {seek_time}")
        effect_key = self.effects.get(chat_id, "normal")
        effect_filter = EFFECTS.get(effect_key, ("", None))[1]
        if effect_filter:
            ff_parts.append(f"--audio -_end -af {effect_filter}")
        ffmpeg_params = " ".join(ff_parts) if ff_parts else None

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if media.video
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=ffmpeg_params,
        )
        play_kw = {"chat_id": chat_id, "stream": stream}
        try:
            play_kw["config"] = types.GroupCallConfig(auto_start=True)
        except Exception:
            pass
        try:
            try:
                await client.play(**play_kw)
            except TypeError:
                play_kw.pop("config", None)
                await client.play(**play_kw)
            self._fail_streak[chat_id] = 0
            if not seek_time:
                media.time = 1
                await db.add_call(chat_id)
                text = _lang["play_media"].format(
                    media.url,
                    media.title,
                    media.duration,
                    media.user,
                )
                keyboard = buttons.controls(chat_id)
                try:
                    await db.update_song_stats(media.id, media.title, media.url)
                    if media.user_id:
                        await db.update_stats(media.user_id, media.title)
                        partner_id = await db.get_soulmate(media.user_id)
                        if partner_id:
                            try:
                                await app.send_message(
                                    partner_id,
                                    f"<b><tg-emoji emoji-id=\"5470135030393090150\">💖</tg-emoji> 𝐑𝐮𝐡 𝐄𝐬̧𝐢𝐧 𝐒̧𝐮 𝐀𝐧 𝐌𝐮̈𝐳𝐢𝐤 𝐃𝐢𝐧𝐥𝐢𝐲𝐨𝐫!</b>\n\n• <b>Şarkı:</b> {media.title}\n• <b>Grup:</b> {message.chat.title or 'Özel'}"
                                )
                            except Exception:
                                pass

                    await message.edit_text(
                        text=text,
                        reply_markup=keyboard,
                        **utils.preview_off(),
                    )
                except MessageIdInvalid:
                    media.message_id = (await app.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=keyboard,
                        **utils.preview_off(),
                    )).id
            return True
        except FileNotFoundError:
            try:
                await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            except Exception:
                pass
            if chat_id not in self._busy:
                await self.play_next(chat_id, ended=True)
            return False
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            try:
                await message.edit_text(_lang["error_no_call"])
            except Exception:
                pass
            return True
        except exceptions.NoAudioSourceFound:
            try:
                await message.edit_text(_lang["error_no_audio"])
            except Exception:
                pass
            if chat_id not in self._busy:
                await self.play_next(chat_id, ended=True)
            return False
        except (ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            try:
                await message.edit_text(_lang["error_tg_server"])
            except Exception:
                pass
            return True
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            try:
                await message.edit_text(_lang["error_rtmp"])
            except Exception:
                pass
            return True
        except Exception as e:
            logger.error(f"play_media hatası ({chat_id}): {e}")
            try:
                await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            except Exception:
                pass
            if chat_id not in self._busy:
                await self.play_next(chat_id, ended=True)
            return False

    async def replay(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        if not media:
            return
        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_again"])
        await self.play_media(chat_id, msg, media)

    async def change_volume(self, chat_id: int, volume: int) -> None:
        client = await db.get_assistant(chat_id)
        await client.change_volume_call(chat_id, volume)

    async def apply_effect(self, chat_id: int, effect_key: str, message: Message) -> tuple[bool, str]:
        if effect_key not in EFFECTS:
            return False, "Geçersiz efekt."
        media = queue.get_current(chat_id)
        if not media or not await db.get_call(chat_id):
            return False, "Şu an çalan bir şarkı yok."
        if effect_key == "normal":
            self.effects.pop(chat_id, None)
        else:
            self.effects[chat_id] = effect_key
        label = EFFECTS[effect_key][0]
        seek_pos = max(0, int(media.time or 0)) if (media.duration_sec or 0) > 15 else 0
        ok = await self.play_media(chat_id, message, media, seek_time=seek_pos)
        return ok, label

    async def play_next(self, chat_id: int, ended: bool = False) -> None:
        if chat_id in self._busy:
            return
        self._busy.add(chat_id)
        try:
            await self._play_next_body(chat_id, ended)
        finally:
            self._busy.discard(chat_id)

    async def _play_next_body(self, chat_id: int, ended: bool) -> None:
        if ended and queue.use_loop(chat_id):
            media = queue.get_current(chat_id)
            if media:
                try:
                    if media.message_id:
                        await app.delete_messages(chat_id, media.message_id, revoke=True)
                except Exception:
                    pass
                left = queue.get_loop(chat_id)
                info = "sonsuz" if left < 0 else f"kalan {left}"
                msg = await app.send_message(
                    chat_id, f"<b>🔁 Döngü: şarkı tekrar çalınıyor ({info})</b>"
                )
                media.message_id = msg.id
                if await self.play_media(chat_id, msg, media):
                    return

        if not ended:
            queue.set_loop(chat_id, 0)

        _lang = await lang.get_lang(chat_id)
        fails = self._fail_streak.get(chat_id, 0)

        while True:
            prev = queue.get_current(chat_id)
            media = queue.get_next(chat_id)

            if not media and chat_id in queue.autoplay and isinstance(prev, Track):
                try:
                    media = await yt.related(prev, exclude=set(queue.history[chat_id]))
                except Exception as e:
                    logger.warning(f"Otomatik oynatma hatası: {e}")
                    media = None
                if media:
                    queue.add(chat_id, media)

            if not media:
                return await self.stop(chat_id)

            try:
                if media.message_id:
                    await app.delete_messages(
                        chat_id=chat_id,
                        message_ids=media.message_id,
                        revoke=True,
                    )
                    media.message_id = 0
            except Exception:
                pass

            msg = await app.send_message(chat_id=chat_id, text=_lang["play_next"])
            if not media.file_path:
                media.file_path = await yt.download(media.id, video=media.video)
            if not media.file_path:
                fails += 1
                self._fail_streak[chat_id] = fails
                logger.warning(f"Şarkı atlandı (indirilemedi): {media.id}")
                try:
                    await msg.edit_text("⚠️ Şarkı alınamadı, sıradakine geçiliyor...")
                except Exception:
                    pass
                if fails >= 5:
                    await self.stop(chat_id)
                    try:
                        await msg.edit_text(
                            _lang["error_no_file"].format(config.SUPPORT_CHAT)
                        )
                    except Exception:
                        pass
                    return
                continue

            media.message_id = msg.id
            ok = await self.play_media(chat_id, msg, media)
            if ok:
                return
            fails += 1
            self._fail_streak[chat_id] = fails
            if fails >= 5:
                await self.stop(chat_id)
                return

    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        if not pings:
            return 0.0
        return round(sum(pings) / len(pings), 2)

    async def decorators(self, client: PyTgCalls) -> None:
        @client.on_update()
        async def update_handler(_, update: types.Update) -> None:
            if isinstance(update, types.StreamEnded):
                stream_type = getattr(update, "stream_type", None) or getattr(update, "type", None)
                audio = getattr(getattr(types, "StreamEnded", None), "Type", None)
                is_audio = (
                    audio is not None and stream_type == getattr(audio, "AUDIO", stream_type)
                ) or str(stream_type).lower().endswith("audio")
                if is_audio or stream_type is None:
                    await self.play_next(update.chat_id, ended=True)
            elif isinstance(update, types.ChatUpdate):
                if update.status in [
                    types.ChatUpdate.Status.KICKED,
                    types.ChatUpdate.Status.LEFT_GROUP,
                    types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                ]:
                    await self.stop(update.chat_id)

    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
        logger.info("PyTgCalls client(s) started without thumbnails.")
