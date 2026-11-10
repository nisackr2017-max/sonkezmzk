# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Gelişmiş müzik komutları: döngü, karıştır, sıradan sil, sırayı temizle, ses

import asyncio
from pyrogram import filters, types

from KumsalTR import anon, app, db, lang, logger, queue
from KumsalTR.core.calls import EFFECTS
from KumsalTR.helpers import Media, can_manage_vc, utils


async def _check_call(m: types.Message) -> bool:
    if not await db.get_call(m.chat.id):
        await m.reply_text(m.lang["not_playing"])
        return False
    return True


@app.on_message(filters.command(["dongu", "loop", "tekrarla"]) & filters.group & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _loop(_, m: types.Message):
    """
    /dongu          -> sonsuz döngüyü aç/kapat
    /dongu 3        -> şarkıyı 3 kez daha çal
    /dongu kapat    -> döngüyü kapat
    """
    if not await _check_call(m):
        return

    chat_id = m.chat.id
    arg = m.command[1].lower() if len(m.command) > 1 else ""

    if arg in ("kapat", "off", "0", "dur"):
        queue.set_loop(chat_id, 0)
        return await m.reply_text("<b>➡️ Döngü kapatıldı.</b>")

    if arg.isdigit():
        count = max(1, min(int(arg), 20))
        queue.set_loop(chat_id, count)
        return await m.reply_text(
            f"<b>🔁 Şarkı {count} kez daha çalınacak.</b>\n<i>Kapatmak için:</i> <code>/dongu kapat</code>"
        )

    # Argümansız: aç/kapat
    if queue.get_loop(chat_id):
        queue.set_loop(chat_id, 0)
        return await m.reply_text("<b>➡️ Döngü kapatıldı.</b>")

    queue.set_loop(chat_id, -1)
    await m.reply_text(
        "<b>🔁 Sonsuz döngü açıldı.</b> Şarkı bitince tekrar başlayacak.\n"
        "<i>Kapatmak için:</i> <code>/dongu kapat</code>"
    )


@app.on_message(filters.command(["karistir", "shuffle"]) & filters.group & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _shuffle(_, m: types.Message):
    if not await _check_call(m):
        return

    count = queue.shuffle(m.chat.id)
    if not count:
        return await m.reply_text("<b>❌ Karıştırmak için sırada en az 2 şarkı olmalı.</b>")
    await m.reply_text(f"<b>🔀 Sıradaki {count} şarkı karıştırıldı.</b> Görmek için: /sira")


@app.on_message(filters.command(["sil", "remove"]) & filters.group & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _remove(_, m: types.Message):
    if not await _check_call(m):
        return

    if len(m.command) < 2 or not m.command[1].isdigit():
        return await m.reply_text(
            "<b>Kullanım:</b> <code>/sil 2</code>\n<i>Numaraları /sira komutuyla görebilirsin.</i>"
        )

    # /sira listesinde çalan şarkı 1, sıradakiler 2'den başlar
    pos = int(m.command[1]) - 1
    removed = queue.remove_at(m.chat.id, pos)
    if not removed:
        return await m.reply_text("<b>❌ Bu numarada sırada şarkı yok.</b>")
    await m.reply_text(f"<b>🗑 Sıradan silindi:</b> {removed.title}")


@app.on_message(filters.command(["temizle", "clearqueue"]) & filters.group & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _clear(_, m: types.Message):
    if not await _check_call(m):
        return

    count = queue.clear_upcoming(m.chat.id)
    if not count:
        return await m.reply_text("<b>Sırada bekleyen şarkı yok.</b>")
    await m.reply_text(f"<b>🧹 Sıradaki {count} şarkı silindi.</b> Çalan şarkı devam ediyor.")


@app.on_message(filters.command(["ses", "volume", "vol"]) & filters.group & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _volume(_, m: types.Message):
    if not await _check_call(m):
        return

    if len(m.command) < 2 or not m.command[1].isdigit():
        return await m.reply_text("<b>Kullanım:</b> <code>/ses 80</code> <i>(1-200 arası)</i>")

    volume = max(1, min(int(m.command[1]), 200))
    try:
        await anon.change_volume(m.chat.id, volume)
    except Exception as e:
        logger.error(f"Ses ayarlanamadı: {e}")
        return await m.reply_text(
            "<b>❌ Ses ayarlanamadı.</b> Asistan hesabın sesli sohbette yönetici olması gerekebilir."
        )
    await m.reply_text(f"<b>🔊 Ses seviyesi: %{volume}</b>")


def _bar(played: int, total: int, size: int = 12) -> str:
    if not total:
        return "▬" * size
    pos = min(int(played / total * size), size - 1)
    return "▬" * pos + "🔘" + "▬" * (size - pos - 1)


def _fmt(sec: int) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


@app.on_message(filters.command(["simdi", "np", "nowplaying"]) & filters.group & ~app.blacklist_filter)
@lang.language()
async def _now_playing(_, m: types.Message):
    """Çalan şarkıyı ilerleme çubuğuyla gösterir."""
    if not await _check_call(m):
        return

    chat_id = m.chat.id
    items = queue.get_queue(chat_id)
    if not items:
        return await m.reply_text(m.lang["not_playing"])

    media = items[0]
    played = media.time or 0
    total = media.duration_sec or 0
    loop = queue.get_loop(chat_id)
    loop_txt = "kapalı" if not loop else ("sonsuz" if loop < 0 else f"{loop} kez")
    paused = not await db.playing(chat_id)

    text = (
        f"<b>{'⏸' if paused else '▶️'} Şu an çalıyor</b>\n\n"
        f"<b>🎵</b> <a href=\"{media.url}\">{media.title}</a>\n"
        f"<code>{_fmt(played)} {_bar(played, total)} {media.duration or _fmt(total)}</code>\n\n"
        f"<b>👤 İsteyen:</b> {media.user or '-'}\n"
        f"<b>🔁 Döngü:</b> {loop_txt}\n"
        f"<b>📜 Sırada:</b> {len(items) - 1} şarkı"
    )
    await m.reply_text(text, **utils.preview_off())


@app.on_message(filters.command(["otomatik", "autoplay"]) & filters.group & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _autoplay(_, m: types.Message):
    """Sıra bitince benzer şarkıları otomatik çalar (aç/kapat)."""
    on = queue.toggle_autoplay(m.chat.id)
    if on:
        return await m.reply_text(
            "<b>📻 Otomatik oynatma açıldı.</b>\n"
            "Sıra bitince son şarkıya benzer şarkılar kendiliğinden çalınacak.\n"
            "<i>Kapatmak için tekrar</i> <code>/otomatik</code>"
        )
    await m.reply_text("<b>📻 Otomatik oynatma kapatıldı.</b>")


# ─── SES EFEKTLERİ (/efekt, /bass, /nightcore, /yavas, /8d, /karaoke, /normal) ───

def _efekt_keyboard(chat_id: int) -> types.InlineKeyboardMarkup:
    active = anon.effects.get(chat_id, "normal")
    def _lbl(key: str, text: str) -> str:
        return f"✅ {text}" if active == key else text

    return types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(_lbl("bass", "🔊 Bass Boost"), callback_data=f"efekt_set {chat_id} bass"),
                types.InlineKeyboardButton(_lbl("nightcore", "⚡ Nightcore"), callback_data=f"efekt_set {chat_id} nightcore"),
            ],
            [
                types.InlineKeyboardButton(_lbl("slowed", "🌙 Slowed+Reverb"), callback_data=f"efekt_set {chat_id} slowed"),
                types.InlineKeyboardButton(_lbl("8d", "🎧 8D Ses"), callback_data=f"efekt_set {chat_id} 8d"),
            ],
            [
                types.InlineKeyboardButton(_lbl("karaoke", "🎤 Karaoke"), callback_data=f"efekt_set {chat_id} karaoke"),
                types.InlineKeyboardButton(_lbl("normal", "🔄 Normal"), callback_data=f"efekt_set {chat_id} normal"),
            ],
            [
                types.InlineKeyboardButton("⌯ Kapat ⌯", callback_data="help close"),
            ],
        ]
    )


@app.on_message(
    filters.command(["efekt", "bass", "nightcore", "yavas", "slowed", "8d", "karaoke", "normal"])
    & filters.group
    & ~app.blacklist_filter
)
@lang.language()
@can_manage_vc
async def _efekt_cmd(_, m: types.Message):
    if not await _check_call(m):
        return

    cmd = m.command[0].lower()
    arg = m.command[1].lower() if len(m.command) > 1 else ""
    alias_map = {
        "bass": "bass",
        "nightcore": "nightcore",
        "yavas": "slowed",
        "slowed": "slowed",
        "8d": "8d",
        "karaoke": "karaoke",
        "normal": "normal",
        "kapat": "normal",
        "off": "normal",
    }
    chosen = alias_map.get(cmd) or alias_map.get(arg)

    if not chosen:
        cur = EFFECTS.get(anon.effects.get(m.chat.id, "normal"), ("🔄 Normal", None))[0]
        return await m.reply_text(
            f"<b>🎛️ Lonca Music — Ses Efektleri Paneli</b>\n\n"
            f"<b>Aktif Efekt:</b> {cur}\n"
            f"<i>Uygulamak istediğiniz ses efektini aşağıdan seçin:</i>",
            reply_markup=_efekt_keyboard(m.chat.id),
        )

    sent = await m.reply_text("<b>🎛️ Ses efekti uygulanıyor...</b>")
    ok, label = await anon.apply_effect(m.chat.id, chosen, sent)
    if ok:
        await sent.edit_text(f"<b>🎛️ Ses efekti değiştirildi:</b> {label}")
    else:
        await sent.edit_text(f"<b>❌ {label}</b>")


@app.on_callback_query(filters.regex(r"^efekt_menu ") & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _efekt_menu_cb(_, cb: types.CallbackQuery):
    chat_id = int(cb.data.split()[1])
    if not await db.get_call(chat_id):
        return await cb.answer("Şu an çalan bir şarkı yok!", show_alert=True)
    cur = EFFECTS.get(anon.effects.get(chat_id, "normal"), ("🔄 Normal", None))[0]
    await cb.answer()
    await cb.message.reply_text(
        f"<b>🎛️ Lonca Music — Ses Efektleri Paneli</b>\n\n"
        f"<b>Aktif Efekt:</b> {cur}\n"
        f"<i>Uygulamak istediğiniz ses efektini aşağıdan seçin:</i>",
        reply_markup=_efekt_keyboard(chat_id),
    )


@app.on_callback_query(filters.regex(r"^efekt_set ") & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _efekt_set_cb(_, cb: types.CallbackQuery):
    parts = cb.data.split()
    chat_id, chosen = int(parts[1]), parts[2]
    if not await db.get_call(chat_id):
        return await cb.answer("Şu an çalan bir şarkı yok!", show_alert=True)
    await cb.answer("🎛️ Efekt uygulanıyor...")
    ok, label = await anon.apply_effect(chat_id, chosen, cb.message)
    if ok:
        try:
            await cb.message.edit_text(
                f"<b>🎛️ Lonca Music — Ses Efektleri Paneli</b>\n\n"
                f"<b>Aktif Efekt:</b> {label}\n"
                f"<i>Efekt anında sesli sohbete uygulandı!</i>",
                reply_markup=_efekt_keyboard(chat_id),
            )
        except Exception:
            pass
    else:
        await cb.answer(f"❌ {label}", show_alert=True)


# ─── FAVORİLERE HIZLI EKLE BUTONU (fav_add) ───

@app.on_callback_query(filters.regex(r"^fav_add ") & ~app.blacklist_filter)
async def _fav_add_cb(_, cb: types.CallbackQuery):
    chat_id = int(cb.data.split()[1])
    media = queue.get_current(chat_id)
    if not media:
        return await cb.answer("❌ Şu an çalan bir şarkı yok!", show_alert=True)
    song = {
        "id": media.id,
        "title": media.title,
        "url": media.url,
        "duration": media.duration or "0:00",
    }
    await db.add_playlist(cb.from_user.id, song)
    await cb.answer(f"❤️ '{media.title}' favori playlistine eklendi! (/playlist)", show_alert=True)


# ─── UYKU ZAMANLAYICISI (/uyku, /zamanlayici, /timer) ───

def _sleep_keyboard(chat_id: int) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton("⏱️ 15 dk", callback_data=f"uyku_set {chat_id} 15"),
                types.InlineKeyboardButton("⏱️ 30 dk", callback_data=f"uyku_set {chat_id} 30"),
                types.InlineKeyboardButton("⏱️ 60 dk", callback_data=f"uyku_set {chat_id} 60"),
            ],
            [
                types.InlineKeyboardButton("⏱️ 90 dk", callback_data=f"uyku_set {chat_id} 90"),
                types.InlineKeyboardButton("❌ Zamanlayıcıyı İptal Et", callback_data=f"uyku_set {chat_id} 0"),
            ],
        ]
    )


async def _set_sleep_timer(chat_id: int, minutes: int) -> None:
    old = anon.sleep_timers.pop(chat_id, None)
    if old and hasattr(old, "cancel"):
        try:
            old.cancel()
        except Exception:
            pass
    if minutes <= 0:
        return

    async def _runner():
        try:
            await asyncio.sleep(minutes * 60)
            if await db.get_call(chat_id):
                await anon.stop(chat_id)
                await app.send_message(
                    chat_id,
                    f"<b>💤 Uyku zamanlayıcısı ({minutes} dk) doldu!</b>\n"
                    "Müzik otomatik olarak durduruldu. İyi geceler! 🌙",
                )
        except asyncio.CancelledError:
            pass
        finally:
            anon.sleep_timers.pop(chat_id, None)

    anon.sleep_timers[chat_id] = asyncio.create_task(_runner())


@app.on_message(filters.command(["uyku", "zamanlayici", "timer"]) & filters.group & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _sleep_cmd(_, m: types.Message):
    if not await _check_call(m):
        return

    if len(m.command) > 1:
        arg = m.command[1].lower()
        if arg in ("iptal", "kapat", "off", "0"):
            await _set_sleep_timer(m.chat.id, 0)
            return await m.reply_text("<b>❎ Uyku zamanlayıcısı iptal edildi.</b>")
        if arg.isdigit():
            mins = max(1, min(int(arg), 360))
            await _set_sleep_timer(m.chat.id, mins)
            return await m.reply_text(
                f"<b>💤 Uyku zamanlayıcısı {mins} dakikaya ayarlandı!</b>\n"
                f"<i>{mins} dakika sonra yayın otomatik olarak kapatılacak.</i>"
            )

    active = "Акtif" if m.chat.id in anon.sleep_timers else "Kapalı"
    await m.reply_text(
        f"<b>💤 Lonca Music — Uyku Zamanlayıcısı</b>\n\n"
        f"<b>Durum:</b> {active}\n"
        "<i>Müziğin kaç dakika sonra otomatik kapanacağını seçin:</i>",
        reply_markup=_sleep_keyboard(m.chat.id),
    )


@app.on_callback_query(filters.regex(r"^uyku_set ") & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _sleep_set_cb(_, cb: types.CallbackQuery):
    parts = cb.data.split()
    chat_id, mins = int(parts[1]), int(parts[2])
    await _set_sleep_timer(chat_id, mins)
    if mins <= 0:
        await cb.answer("❎ Zamanlayıcı iptal edildi.", show_alert=True)
        return await cb.message.edit_text("<b>❎ Uyku zamanlayıcısı iptal edildi.</b>")
    await cb.answer(f"💤 {mins} dakika ayarlandı!", show_alert=True)
    await cb.message.edit_text(
        f"<b>💤 Uyku zamanlayıcısı {mins} dakikaya ayarlandı!</b>\n"
        f"<i>{mins} dakika sonra yayın otomatik olarak sonlandırılacak.</i>"
    )


# ─── CANLI RADYO İSTASYONLARI (/radyo, /radio) ───

RADIO_STATIONS: dict[str, tuple[str, str]] = {
    "powerturk": ("🇹🇷 PowerTürk FM", "https://listen.powerapp.com.tr/powerturk/mpeg/icecast.audio"),
    "kralpop": ("🎤 Kral Pop Radyo", "https://dygedge2.radyotvonline.net/kralpop/playlist.m3u8"),
    "slowturk": ("💔 Slow Türk", "https://radyo.duhnet.tv/ak_dtvh_slowturk"),
    "fenomen": ("🔥 Radyo Fenomen", "https://listen.radyofenomen.com/fenomen/128/icecast.audio"),
    "metrofm": ("🌍 Metro FM", "https://playerservices.streamtheworld.com/api/livestream-redirect/METRO_FM128AAC.aac"),
    "virgin": ("⚡ Virgin Radio Türkiye", "https://playerservices.streamtheworld.com/api/livestream-redirect/VIRGIN_RADIO128AAC.aac"),
    "alemfm": ("🎶 Alem FM", "https://turkmedya.radyotvonline.net/turkmedya/alemfm.stream/playlist.m3u8"),
    "viva": ("🎻 Radyo Viva (Arabesk)", "https://listen.radyoviva.com.tr/viva/128/icecast.audio"),
    "lofi": ("☕ Lofi Hip Hop 24/7", "https://streams.ilovemusic.de/iloveradio17.mp3"),
}


def _radio_keyboard(chat_id: int) -> types.InlineKeyboardMarkup:
    buttons_list = [
        types.InlineKeyboardButton(title, callback_data=f"radyo_play {chat_id} {key}")
        for key, (title, _) in RADIO_STATIONS.items()
    ]
    rows = [buttons_list[i : i + 2] for i in range(0, len(buttons_list), 2)]
    rows.append([types.InlineKeyboardButton("⌯ Kapat ⌯", callback_data="help close")])
    return types.InlineKeyboardMarkup(rows)


@app.on_message(filters.command(["radyo", "radio"]) & filters.group & ~app.blacklist_filter)
@lang.language()
async def _radio_cmd(_, m: types.Message):
    await m.reply_text(
        "<b>📻 Lonca Music — 7/24 Canlı Radyo İstasyonları</b>\n\n"
        "<i>Sesli sohbette canlı dinlemek istediğiniz radyo istasyonunu seçin:</i>",
        reply_markup=_radio_keyboard(m.chat.id),
    )


@app.on_callback_query(filters.regex(r"^radyo_play ") & ~app.blacklist_filter)
@lang.language()
async def _radio_play_cb(_, cb: types.CallbackQuery):
    parts = cb.data.split()
    chat_id, station_key = int(parts[1]), parts[2]
    station = RADIO_STATIONS.get(station_key)
    if not station:
        return await cb.answer("Radyo istasyonu bulunamadı!", show_alert=True)

    title, stream_url = station
    await cb.answer(f"📻 {title} bağlanıyor...")
    sent = await cb.message.edit_text(f"<b>📻 {title} canlı yayınına bağlanılıyor...</b>")

    # Asistanın grupta olduğundan emin ol
    client = await db.get_client(chat_id)
    if client is None or not getattr(client, "id", None):
        return await sent.edit_text("<b>❌ Asistan bağlı değil.</b>")
    try:
        await app.get_chat_member(chat_id, client.id)
    except Exception:
        try:
            chat = await app.get_chat(chat_id)
            inv = chat.username or chat.invite_link or await app.export_chat_invite_link(chat_id)
            await client.join_chat(inv)
        except Exception:
            pass

    media = Media(
        id=f"radio_{station_key}",
        duration="CANLI 🔴",
        duration_sec=0,
        file_path=stream_url,
        message_id=sent.id,
        title=title,
        url=stream_url,
        user=cb.from_user.mention,
        user_id=cb.from_user.id,
        video=False,
    )
    queue.force_add(chat_id, media)
    await anon.play_media(chat_id, sent, media)
