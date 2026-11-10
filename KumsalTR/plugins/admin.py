# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam

import os
from pyrogram import filters, types
from KumsalTR import app, yt, config, db, userbot

@app.on_message(filters.command(["pottest", "tokentest"]) & filters.user(config.OWNER_ID))
async def pot_test(_, m: types.Message):
    """PO token sağlayıcısının, asistanın ve YouTube bağlantısının çalıştığını test eder."""
    sent = await m.reply_text("<b>🔄 Lonca Music — Sistem ve PO Token testi yapılıyor...</b>")

    if userbot.clients:
        ub = userbot.clients[0]
        assistant = f"✅ {ub.mention} (<code>{ub.id}</code>)"
    else:
        assistant = "❌ Bağlı değil — özelden <code>/sessional</code> ile yeni SESSION alın"

    ping_info = await yt._ping_provider_info()
    if ping_info:
        ver = ping_info.get("version", "2.0.2")
        up = int(float(ping_info.get("server_uptime", 0) or 0))
        provider = f"✅ Çalışıyor (bgutil v{ver}, {up}sn aktif)"
    else:
        provider = "❌ Ulaşılamadı (otomatik yeniden başlatılıyor...)"
        await yt.ensure_provider()
        ping_info2 = await yt._ping_provider_info()
        if ping_info2:
            provider = f"✅ Yeniden başlatıldı (v{ping_info2.get('version', '2.0.2')})"

    res_path = await yt.download("dQw4w9WgXcQ")
    if res_path and os.path.exists(res_path):
        size_kb = os.path.getsize(res_path) // 1024
        youtube = f"✅ Cookiesiz indirildi ({size_kb} KB yerel dosya hazır)"
    elif res_path:
        youtube = "✅ Cookiesiz akış bağlantısı alındı"
    else:
        youtube = "❌ Başarısız (loglara bakın)"

    await sent.edit_text(
        f"<b>🔑 Lonca Music — Durum Testi</b>\n\n"
        f"<b>Asistan SESSION:</b> {assistant}\n"
        f"<b>PO Token Sağlayıcısı:</b> {provider}\n"
        f"<b>YouTube (Cookiesiz):</b> {youtube}\n"
        f"<b>Yedek Cookie:</b> {'✅ Yüklü (yalnızca yedek)' if yt.has_cookie() else '— Yok, gerekmez'}"
    )

@app.on_message(filters.command(["cookie", "cerezkoy"]) & filters.user(config.OWNER_ID))
async def cookie_cmd(_, m: types.Message):
    """cookies.txt dosyasına yanıt verilerek yedek YouTube cookie'si yüklenir (isteğe bağlı)."""
    r = m.reply_to_message
    if not r or not (r.document or r.text):
        return await m.reply_text(
            "<b>🍪 Kullanım:</b> cookies.txt dosyasını gönder, sonra ona yanıt vererek <code>/cookie</code> yaz.\n"
            "<i>Zorunlu değil; bot PO token ile cookiesiz çalışır. Cookie yalnızca YouTube IP'yi engellerse yedektir.</i>"
        )
    try:
        if r.document:
            f = await r.download(in_memory=True)
            text = bytes(f.getbuffer()).decode("utf-8", errors="ignore")
        else:
            text = r.text
        count = await yt.save_cookie(db, text)
    except Exception as e:
        return await m.reply_text(f"<b>❌ Hata:</b> <code>{e}</code>")
    if not count:
        return await m.reply_text("<b>❌ Dosyada YouTube cookie'si bulunamadı.</b> Netscape formatında cookies.txt olmalı.")
    try:
        await r.delete()
    except Exception:
        pass
    await m.reply_text(f"<b>✅ Cookie kaydedildi ({count} satır).</b> Yalnızca PO token yetmezse yedek olarak kullanılır.\nTest: /pottest")


@app.on_message(filters.command(["cookiesil"]) & filters.user(config.OWNER_ID))
async def cookie_del(_, m: types.Message):
    await yt.delete_cookie(db)
    await m.reply_text("<b>🗑 Cookie silindi.</b> Bot cookiesiz, PO token ile çalışacak.")


@app.on_message(filters.command(["clearcache"]) & filters.user(config.OWNER_ID))
async def clear_cache_cmd(_, m: types.Message):
    count = 0
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    for file in os.listdir("downloads"):
        try:
            os.remove(f"downloads/{file}")
            count += 1
        except:
            continue
    await m.reply_text(f"<b>🧹 {count} ᴀᴅᴇᴛ ᴏ̈ɴʙᴇʟʟᴇᴋ ᴅᴏsʏᴀsɪ ᴛᴇᴍɪᴢʟᴇɴᴅɪ.</b>")
