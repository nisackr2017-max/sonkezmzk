# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Asistan SESSION'ını bilgisayara Python kurmadan, doğrudan bot üzerinden alma.
# Sadece bot sahibi (OWNER_ID), sadece botun özel sohbetinde kullanabilir.

import re

from pyrogram import Client, filters, types
try:
    from pyrogram.dispatcher import StopPropagation
except ImportError:
    try:
        from pyrogram import StopPropagation
    except ImportError:
        class StopPropagation(Exception):
            pass
from pyrogram.errors import (
    FloodWait,
    PasswordHashInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    PhoneNumberInvalid,
    SessionPasswordNeeded,
)

from KumsalTR import app, config, logger

# user_id -> {"step": "phone"|"code"|"password", "client": Client, "phone": str, "hash": str}
STATE: dict[int, dict] = {}

_owner_private = filters.private & filters.user(config.OWNER_ID)


async def _cleanup(user_id: int) -> None:
    st = STATE.pop(user_id, None)
    if st:
        try:
            await st["client"].disconnect()
        except Exception:
            pass


async def _delete(m: types.Message) -> None:
    try:
        await m.delete()
    except Exception:
        pass


@app.on_message(filters.command(["sessional", "session"]) & _owner_private)
async def _session_start(_, m: types.Message):
    await _cleanup(m.from_user.id)

    client = Client(
        name=f"sessional_{m.from_user.id}",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        in_memory=True,
    )
    try:
        await client.connect()
    except Exception as e:
        return await m.reply_text(f"<b>❌ Telegram'a bağlanılamadı:</b> <code>{e}</code>")

    STATE[m.from_user.id] = {"step": "phone", "client": client}
    await m.reply_text(
        "<b>🔑 Asistan SESSION Oluşturucu</b>\n\n"
        "Asistan olarak kullanılacak hesabın <b>telefon numarasını</b> gönder:\n"
        "<code>+905xxxxxxxxx</code>\n\n"
        "<i>İptal etmek için:</i> <code>/iptal</code>"
    )


@app.on_message(filters.command(["iptal", "cancelsession"]) & _owner_private)
async def _session_cancel(_, m: types.Message):
    if m.from_user.id not in STATE:
        return
    await _cleanup(m.from_user.id)
    await m.reply_text("<b>❎ Session oluşturma iptal edildi.</b>")


@app.on_message(_owner_private & filters.text & ~filters.regex(r"^/"), group=-1)
async def _session_flow(_, m: types.Message):
    uid = m.from_user.id
    st = STATE.get(uid)
    if not st:
        return

    client: Client = st["client"]
    text = m.text.strip()

    try:
        # 1) Telefon numarası
        if st["step"] == "phone":
            phone = re.sub(r"[^\d+]", "", text)
            if not phone.startswith("+"):
                phone = "+" + phone
            sent = await client.send_code(phone)
            st.update(step="code", phone=phone, hash=sent.phone_code_hash)
            await m.reply_text(
                "<b>📩 Telegram'dan kod gönderildi.</b>\n\n"
                "Kodu <b>rakamların arasına boşluk koyarak</b> gönder, örneğin:\n"
                "<code>1 2 3 4 5</code>\n\n"
                "<i>Boşluksuz gönderirsen Telegram kodu iptal eder!</i>"
            )
            raise StopPropagation

        # 2) Doğrulama kodu
        if st["step"] == "code":
            code = re.sub(r"\D", "", text)
            await _delete(m)
            try:
                signed = await client.sign_in(st["phone"], st["hash"], code)
            except SessionPasswordNeeded:
                st["step"] = "password"
                await m.reply_text(
                    "<b>🔒 Bu hesapta iki adımlı doğrulama açık.</b>\n"
                    "Şifreni gönder (mesajın hemen silinecek)."
                )
                raise StopPropagation
            if getattr(signed, "is_bot", False):
                await _cleanup(uid)
                await m.reply_text(
                    "<b>❌ Bot hesabı asistan olamaz.</b> Normal bir kullanıcı hesabı kullanın.\n"
                    "Baştan: /sessional"
                )
                raise StopPropagation
            await _finish(m, uid)
            raise StopPropagation

        # 3) İki adımlı doğrulama şifresi
        if st["step"] == "password":
            await _delete(m)
            await client.check_password(text)
            await _finish(m, uid)
            raise StopPropagation

    except StopPropagation:
        raise
    except PhoneNumberInvalid:
        await m.reply_text("<b>❌ Telefon numarası geçersiz.</b> Tekrar gönder: <code>+905xxxxxxxxx</code>")
    except PhoneCodeInvalid:
        await m.reply_text("<b>❌ Kod yanlış.</b> Tekrar gönder (rakamlar arasına boşluk koy).")
    except PhoneCodeExpired:
        await _cleanup(uid)
        await m.reply_text("<b>⌛ Kodun süresi doldu.</b> Baştan başlamak için: /sessional")
    except PasswordHashInvalid:
        await m.reply_text("<b>❌ Şifre yanlış.</b> Tekrar gönder.")
    except FloodWait as e:
        await _cleanup(uid)
        await m.reply_text(f"<b>⏳ Telegram çok fazla deneme yapıldığını söylüyor.</b> {e.value} saniye sonra tekrar dene.")
    except Exception as e:
        logger.error(f"Session oluşturma hatası: {e}")
        await _cleanup(uid)
        await m.reply_text(f"<b>❌ Hata:</b> <code>{type(e).__name__}: {e}</code>\nBaştan başlamak için: /sessional")
    raise StopPropagation


async def _finish(m: types.Message, uid: int) -> None:
    client: Client = STATE[uid]["client"]
    me = await client.get_me()
    if getattr(me, "is_bot", False):
        await _cleanup(uid)
        return await m.reply_text(
            "<b>❌ Bot hesabı asistan olamaz.</b> Normal bir kullanıcı hesabı kullanın.\n"
            "Baştan: /sessional"
        )
    session = await client.export_session_string()
    await _cleanup(uid)

    await m.reply_text(
        f"<b>✅ SESSION oluşturuldu!</b>\n"
        f"<b>Hesap:</b> {me.first_name} (<code>{me.id}</code>)\n\n"
        f"<code>{session}</code>\n\n"
        "<b>Şimdi:</b> Bu yazıyı kopyala → <code>config.py</code> içinde <b>SESSION = \"...\"</b> "
        "satırına yapıştır → GitHub'a push → Railway Redeploy.\n\n"
        "⚠️ <b>Kimseyle paylaşma</b>. İşin bitince bu mesajı sil."
    )
