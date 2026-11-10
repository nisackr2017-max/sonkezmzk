# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam

import os
import time
import asyncio
from pyrogram import filters, types, enums
from KumsalTR import app, db, lang, yt, logger, config
from KumsalTR.helpers import buttons, utils
from PIL import Image, ImageDraw, ImageFont
import re

PENDING_GIFTS = {}

# /bul [söz/video]
@app.on_message(filters.command(["bul"]) & ~app.blacklist_filter)
@lang.language()
async def bul_cmd(_, m: types.Message):
    replied = m.reply_to_message
    if replied and (replied.video or replied.document or replied.audio or replied.voice):
        file = replied.video or replied.document or replied.audio or replied.voice
        if getattr(file, "file_size", 0) > 10 * 1024 * 1024:
            return await m.reply_text(m.lang["bul_video_error"])
        
        sent = await m.reply_text(m.lang["bul_searching"])
        
        # Shazamio integration
        try:
            from shazamio import Shazam
            file_path = await replied.download("downloads/")
            shazam = Shazam()
            out = await shazam.recognize_song(file_path)
            
            if out.get('track'):
                title = out['track'].get('title', '')
                subtitle = out['track'].get('subtitle', '')
                query = f"{title} {subtitle}"
                await sent.edit_text(f"<b>🎵 Şᴀʀᴋɪ ᴛᴀɴɪɴᴅɪ: {query}</b>\n\n🔍 YᴏᴜTᴜʙᴇ ᴜ̈ᴢᴇʀɪɴᴅᴇ ᴀʀᴀɴɪʏᴏʀ...")
            else:
                query = getattr(file, "file_name", "Müzik")
            
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Shazam error: {e}")
            query = getattr(file, "file_name", "Müzik")

        track = await yt.search(query, sent.id)
    elif len(m.command) > 1:
        query = " ".join(m.command[1:])
        sent = await m.reply_text(m.lang["bul_searching"])
        track = await yt.search(query, sent.id)
    else:
        return await m.reply_text("<b>𝐊ᴜʟʟᴀɴɪᴍ:</b>\n\n• <code>/bul [şarkı sözleri]</code>\n• Vɪᴅᴇᴏʏᴜ/sᴇsɪ ʏᴀɴɪᴛʟᴀʏᴀʀᴀᴋ <code>/bul</code> ʏᴀᴢɪɴ.")

    if not track:
        return await sent.edit_text(m.lang["play_not_found"].format(config.SUPPORT_CHAT))
    
    try:
        await sent.edit_text(
            f"<b>🔍 Şᴀʀᴋɪ ʙᴜʟᴜɴᴅᴜ!</b>\n\n• <b>Bᴀşʟɪᴋ:</b> {track.title}\n• <b>Kᴀɴᴀʟ:</b> {track.channel_name}\n• <b>Sᴜ̈ʀᴇ:</b> {track.duration}",
            reply_markup=buttons.play_markup(m.chat.id, track.id, track.duration, "video" if track.video else "audio")
        )
    except Exception as e:
        logger.error(f"bul_cmd edit error: {e}")
        await sent.edit_text(f"<b>🔍 Şᴀʀᴋɪ ʙᴜʟᴜɴᴅᴜ!</b>\n\n• <b>Bᴀşʟɪᴋ:</b> {track.title}")

# /ruhesi [yanıtla]
@app.on_message(filters.command(["ruhesi"]) & filters.group & ~app.blacklist_filter)
@lang.language()
async def ruhesi_cmd(_, m: types.Message):
    if not m.reply_to_message:
        return await m.reply_text("<b>💖 Bɪʀɪɴɪɴ ᴍᴇsᴀᴊɪɴɪ ʏᴀɴɪᴛʟᴀʏᴀʀᴀᴋ ʀᴜʜ ᴇşɪɴɪ ʙᴜʟ!</b>")
    
    user1 = m.from_user
    user2 = m.reply_to_message.from_user
    
    if not user1 or not user2:
        return await m.reply_text("<b>❌ Kᴜʟʟᴀɴɪᴄɪ ʙɪʟɢɪsɪ ᴀʟɪɴᴀᴍᴀᴅɪ.</b>")
    
    if user1.id == user2.id:
        return await m.reply_text("<b>😅 Kᴇɴᴅɪ ᴋᴇɴᴅɪɴᴇ ʀᴜʜ ᴇşɪ ᴏʟᴀᴍᴀᴢsɪɴ!</b>")
    
    try:
        current = await db.get_soulmate(user1.id)
        if current:
            return await m.reply_text(m.lang["soulmate_already"])
        
        await db.set_soulmate(user1.id, user2.id)
        await m.reply_text(m.lang["soulmate_looking"].format(user2.mention))
    except Exception as e:
        logger.error(f"ruhesi error: {e}")
        await m.reply_text("<b>❌ Hᴀᴛᴀ ᴏʟᴜşᴛᴜ, ᴛᴇᴋʀᴀʀ ᴅᴇɴᴇʏɪɴ.</b>")

# /ayril
@app.on_message(filters.command(["ayril"]) & filters.group & ~app.blacklist_filter)
@lang.language()
async def ayril_cmd(_, m: types.Message):
    try:
        current = await db.get_soulmate(m.from_user.id)
        if not current:
            return await m.reply_text(m.lang["soulmate_not_found"])
        
        await db.rm_soulmate(m.from_user.id)
        await m.reply_text(m.lang["soulmate_separated"])
    except Exception as e:
        logger.error(f"ayril error: {e}")
        await m.reply_text("<b>❌ Hᴀᴛᴀ ᴏʟᴜşᴛᴜ.</b>")

# /hediye
@app.on_message(filters.command(["hediye"]) & ~app.blacklist_filter)
@lang.language()
async def hediye_cmd(_, m: types.Message):
    if len(m.command) < 3:
        return await m.reply_text("<b>🎁 Kᴜʟʟᴀɴɪᴍ:</b>\n\n<code>/hediye [kullanıcı_id/username] [şarkı adı]</code>")
    
    target_id = m.command[1]
    song_name = " ".join(m.command[2:])
    
    PENDING_GIFTS[m.from_user.id] = {"target": target_id, "song": song_name, "mention": m.from_user.mention}
    
    keyboard = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("👁️ Aᴄ̧ɪᴋ (İsᴍɪᴍ Gᴏ̈ʀᴜ̈ɴsᴜ̈ɴ)", callback_data="gift_public"),
            types.InlineKeyboardButton("🕵️ Gɪᴢʟɪ (İsᴍɪᴍ Gᴏ̈ʀᴜ̈ɴᴍᴇsɪɴ)", callback_data="gift_anon")
        ],
        [types.InlineKeyboardButton("❌ İᴘᴛᴀʟ", callback_data="gift_cancel")]
    ])
    
    await m.reply_text("<b>🎁 Hᴇᴅɪʏᴇ ɢᴏ̈ɴᴅᴇʀɪᴄɪ sᴇᴄ̧ᴇɴᴇɢɢɪ:</b>\n\nİsᴍɪɴɪᴢ ɢᴏ̈ʀᴜ̈ɴsᴜ̈ɴ ᴍᴜ̈?", reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^gift_") & ~app.blacklist_filter)
async def gift_callback(_, cb: types.CallbackQuery):
    if cb.data == "gift_cancel":
        PENDING_GIFTS.pop(cb.from_user.id, None)
        return await cb.message.edit_text("<b>❌ Hᴇᴅɪʏᴇ ɪᴘᴛᴀʟ ᴇᴅɪʟᴅɪ.</b>")
    
    pending = PENDING_GIFTS.get(cb.from_user.id)
    if not pending:
        return await cb.answer("Sᴜ̈ʀᴇ ᴅᴏʟᴍᴜş ᴠᴇʏᴀ ʙᴜ ʜᴇᴅɪʏᴇ sᴀɴᴀ ᴀɪᴛ ᴅᴇɢɢɪʟ!", show_alert=True)
    
    try:
        user = await app.get_users(pending["target"])
        sender_name = pending["mention"] if cb.data == "gift_public" else "<b>Gɪᴢᴇᴍʟɪ Bɪʀɪ</b>"
        
        await app.send_message(
            user.id,
            f"<b>🎁 Hᴇᴅɪʏᴇ Şᴀʀᴋɪ!</b>\n\n{sender_name} sᴀɴᴀ şᴜ şᴀʀᴋɪʏɪ ʜᴇᴅɪʏᴇ ᴇᴛᴛɪ: <b>{pending['song']}</b>\n\nBᴜɴᴜ ɢʀᴜʙᴜɴᴅᴀ <code>/oynat {pending['song']}</code> ʏᴀᴢᴀʀᴀᴋ ᴅɪɴʟᴇʏᴇʙɪʟɪʀsɪɴ!"
        )
        await cb.message.edit_text(f"<b>✅ Hᴇᴅɪʏᴇ ʙᴀşᴀʀɪʏʟᴀ {user.mention} ᴋɪşɪsɪɴᴇ ɪʟᴇᴛɪʟᴅɪ!</b>")
        PENDING_GIFTS.pop(cb.from_user.id, None)
    except Exception as e:
        logger.error(f"hediye error: {e}")
        await cb.message.edit_text(f"<b>❌ Kᴜʟʟᴀɴɪᴄɪ ʙᴜʟᴜɴᴀᴍᴀᴅɪ ᴠᴇʏᴀ ʙᴏᴛᴜ ʙᴀşʟᴀᴛᴍᴀᴍɪş.</b>")
        PENDING_GIFTS.pop(cb.from_user.id, None)

# /stat
@app.on_message(filters.command(["stat"]) & ~app.blacklist_filter)
@lang.language()
async def stat_cmd(_, m: types.Message):
    try:
        stats = await db.get_stats(m.from_user.id)
        total = stats.get("total_plays", 0)
        history = stats.get("history", [])
        
        text = f"<b>📊 Dɪɴʟᴇᴍᴇ İsᴛᴀᴛɪsᴛɪᴋʟᴇʀɪɴ:</b>\n\n• <b>Tᴏᴘʟᴀᴍ Dɪɴʟᴇᴍᴇ:</b> {total}\n"
        if history:
            text += "\n<b>Sᴏɴ Dɪɴʟᴇɴᴇɴʟᴇʀ:</b>\n"
            for i, s in enumerate(history[-5:][::-1], 1):
                text += f"{i}. {s['title'][:30]}\n"
        
        await m.reply_text(text)
    except Exception as e:
        logger.error(f"stat error: {e}")
        await m.reply_text("<b>❌ İsᴛᴀᴛɪsᴛɪᴋʟᴇʀ ʏᴜ̈ᴋʟᴇɴᴇᴍᴇᴅɪ.</b>")

# /kart (Pillow ile Resim Oluşturma)
@app.on_message(filters.command(["kart"]) & ~app.blacklist_filter)
@lang.language()
async def kart_cmd(_, m: types.Message):
    sent = await m.reply_text("<b>🎨 Kᴀʀᴛɪɴɪᴢ ʜᴀᴢɪʀʟᴀɴɪʏᴏʀ...</b>")
    
    try:
        stats = await db.get_stats(m.from_user.id)
        
        width, height = 600, 400
        img = Image.new('RGB', (width, height), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)
        
        font_path = "KumsalTR/helpers/Raleway-Bold.ttf"
        try:
            font_large = ImageFont.truetype(font_path, 40)
            font_small = ImageFont.truetype(font_path, 25)
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            
        draw.text((50, 50), "LONCA MUSIC KARTIN", fill=(255, 215, 0), font=font_large)
        draw.text((50, 150), f"Kullanıcı: {m.from_user.first_name}", fill=(255, 255, 255), font=font_small)
        draw.text((50, 200), f"Toplam Dinleme: {stats.get('total_plays', 0)}", fill=(255, 255, 255), font=font_small)
        
        if stats.get("history"):
            last = stats["history"][-1]["title"][:25]
            draw.text((50, 250), f"Son Dinlenen: {last}", fill=(200, 200, 255), font=font_small)

        os.makedirs("downloads", exist_ok=True)
        path = f"downloads/card_{m.from_user.id}.png"
        img.save(path)
        
        await m.reply_photo(
            path,
            caption=m.lang["stats_card_caption"].format(
                stats.get("total_plays", 0),
                "Yok" if not stats.get("history") else stats["history"][-1]["title"]
            )
        )
        await sent.delete()
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.error(f"kart error: {e}")
        await sent.edit_text("<b>❌ Kᴀʀᴛ ᴏʟᴜşᴛᴜʀᴜʟᴀᴍᴀᴅɪ.</b>")

# /oneri ve /rastgele (Kategorili Müzik Öneri & Keşif)
import random
from KumsalTR.plugins.quiz import TR_POP, TR_ARABESK, TR_ROCK, TR_RAP, EN_POP

ONERI_POOLS = {
    "tr_pop": ("🔥 Türkçe Pop Trend", TR_POP),
    "arabesk": ("💔 Arabesk & Damar", TR_ARABESK),
    "rock": ("🎸 Türkçe Rock", TR_ROCK),
    "rap": ("🎤 Türkçe Rap", TR_RAP),
    "en_pop": ("🌍 Yabancı Hit", EN_POP),
}


def _oneri_menu_keyboard() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton("🔥 Türkçe Pop", callback_data="oneri_cat tr_pop"),
                types.InlineKeyboardButton("💔 Arabesk", callback_data="oneri_cat arabesk"),
            ],
            [
                types.InlineKeyboardButton("🎸 Türkçe Rock", callback_data="oneri_cat rock"),
                types.InlineKeyboardButton("🎤 Türkçe Rap", callback_data="oneri_cat rap"),
            ],
            [
                types.InlineKeyboardButton("🌍 Yabancı Hit", callback_data="oneri_cat en_pop"),
                types.InlineKeyboardButton("🎲 Şansımı Dene", callback_data="oneri_lucky"),
            ],
            [
                types.InlineKeyboardButton("⌯ Kapat ⌯", callback_data="help close"),
            ],
        ]
    )


@app.on_message(filters.command(["oneri", "rastgele", "kesfet"]) & ~app.blacklist_filter)
@lang.language()
async def oneri_cmd(_, m: types.Message):
    await m.reply_text(
        "<b>🔥 Lonca Music — Müzik Keşif & Öneri Merkezi</b>\n\n"
        "<i>Hangi tarzda şarkı önerileri görmek istersiniz?</i>",
        reply_markup=_oneri_menu_keyboard(),
    )


@app.on_callback_query(filters.regex(r"^oneri_") & ~app.blacklist_filter)
@lang.language()
async def oneri_callback(_, cb: types.CallbackQuery):
    data = cb.data
    if data == "oneri_back":
        return await cb.message.edit_text(
            "<b>🔥 Lonca Music — Müzik Keşif & Öneri Merkezi</b>\n\n"
            "<i>Hangi tarzda şarkı önerileri görmek istersiniz?</i>",
            reply_markup=_oneri_menu_keyboard(),
        )

    if data == "oneri_lucky":
        all_songs = TR_POP + TR_ARABESK + TR_ROCK + TR_RAP + EN_POP
        title, vid = random.choice(all_songs)
        await cb.answer(f"🎲 Seçilen: {title}")
        return await cb.message.edit_text(
            f"<b>🎲 Şansına Çıkan Şarkı:</b>\n\n🎵 <b>{title}</b>",
            reply_markup=types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton("▶️ Hemen Oynat", callback_data=f"play_track oynat {vid}"),
                        types.InlineKeyboardButton("📥 İndir", callback_data=f"play_track indir {vid}"),
                    ],
                    [
                        types.InlineKeyboardButton("🎲 Başka Seç", callback_data="oneri_lucky"),
                        types.InlineKeyboardButton("⬅️ Kategoriler", callback_data="oneri_back"),
                    ],
                ]
            ),
        )

    cat_key = data.replace("oneri_cat ", "").strip()
    label, pool = ONERI_POOLS.get(cat_key, ("🔥 Türkçe Pop Trend", TR_POP))
    sample = random.sample(pool, min(6, len(pool)))
    rows = [
        [types.InlineKeyboardButton(f"▶️ {title}", callback_data=f"play_track oynat {vid}")]
        for title, vid in sample
    ]
    rows.append(
        [
            types.InlineKeyboardButton("🔄 Yenile", callback_data=f"oneri_cat {cat_key}"),
            types.InlineKeyboardButton("⬅️ Geri", callback_data="oneri_back"),
        ]
    )
    await cb.message.edit_text(
        f"<b>{label} — Önerilen Şarkılar:</b>\n\n"
        "<i>Dinlemek istediğiniz şarkının üzerine tıklayın:</i>",
        reply_markup=types.InlineKeyboardMarkup(rows),
    )


# ─── GLOBAL LİDERLİK TABLOSU (/top, /liderler, /siralamalar) ───

def _top_keyboard(active_tab: str) -> types.InlineKeyboardMarkup:
    def _t(tab: str, label: str) -> str:
        return f"• {label} •" if active_tab == tab else label

    return types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(_t("users", "🎧 Dinleyiciler"), callback_data="top_tab users"),
                types.InlineKeyboardButton(_t("songs", "🎵 Şarkılar"), callback_data="top_tab songs"),
                types.InlineKeyboardButton(_t("quiz", "🎮 Yarışma"), callback_data="top_tab quiz"),
            ],
            [
                types.InlineKeyboardButton("⌯ Kapat ⌯", callback_data="help close"),
            ],
        ]
    )


async def _build_top_text(tab: str) -> str:
    medals = ["🥇", "🥈", "🥉"]
    if tab == "songs":
        docs = await db.get_top_songs(10)
        if not docs:
            return "<b>🎵 En Çok Çalınan Şarkılar</b>\n\n<i>Henüz istatistik oluşmadı.</i>"
        lines = ["<b>🎵 Lonca Music — En Çok Çalınan 10 Şarkı</b>\n"]
        for i, doc in enumerate(docs, 1):
            badge = medals[i - 1] if i <= 3 else f"<b>{i}.</b>"
            title = doc.get("title") or "Bilinmeyen Şarkı"
            plays = doc.get("plays", 0)
            url = doc.get("url") or ""
            item = f"<a href=\"{url}\">{title}</a>" if url.startswith("http") else title
            lines.append(f"{badge} {item} — <code>{plays} kez</code>")
        return "\n".join(lines)

    if tab == "quiz":
        docs = await db.get_top_quiz(10)
        if not docs:
            return "<b>🎮 Yarışma Şampiyonları</b>\n\n<i>Henüz yarışma puanı kazanılmadı. (/yarisma)</i>"
        lines = ["<b>🎮 Lonca Music — Yarışma Şampiyonları</b>\n"]
        for i, doc in enumerate(docs, 1):
            badge = medals[i - 1] if i <= 3 else f"<b>{i}.</b>"
            uid = doc.get("_id")
            score = doc.get("score", 0)
            try:
                u = await app.get_users(uid)
                name = u.first_name
            except Exception:
                name = f"Kullanıcı ({uid})"
            lines.append(f"{badge} {name} — <code>{score} puan</code>")
        return "\n".join(lines)

    docs = await db.get_top_listeners(10)
    if not docs:
        return "<b>🎧 En Çok Müzik Dinleyenler</b>\n\n<i>Henüz dinleme istatistiği yok.</i>"
    lines = ["<b>🎧 Lonca Music — En Çok Müzik Dinleyenler</b>\n"]
    for i, doc in enumerate(docs, 1):
        badge = medals[i - 1] if i <= 3 else f"<b>{i}.</b>"
        uid = doc.get("_id")
        total = doc.get("total_plays", 0)
        try:
            u = await app.get_users(uid)
            name = u.first_name
        except Exception:
            name = f"Kullanıcı ({uid})"
        lines.append(f"{badge} {name} — <code>{total} şarkı</code>")
    return "\n".join(lines)


@app.on_message(filters.command(["top", "liderler", "siralamalar"]) & ~app.blacklist_filter)
@lang.language()
async def top_cmd(_, m: types.Message):
    sent = await m.reply_text("<b>🏆 Liderlik tablosu yükleniyor...</b>")
    text = await _build_top_text("users")
    await sent.edit_text(text, reply_markup=_top_keyboard("users"), **utils.preview_off())


@app.on_callback_query(filters.regex(r"^top_tab ") & ~app.blacklist_filter)
async def top_tab_cb(_, cb: types.CallbackQuery):
    tab = cb.data.split()[1]
    await cb.answer("Güncelleniyor...")
    text = await _build_top_text(tab)
    try:
        await cb.message.edit_text(text, reply_markup=_top_keyboard(tab), **utils.preview_off())
    except Exception:
        pass
