# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of KumsalTR


from pyrogram import filters, types

from KumsalTR import anon, app, db, lang
from KumsalTR.helpers import can_manage_vc


@app.on_message(filters.command(["son", "bitir", "durdur", "stop"]) & filters.group & ~app.blacklist_filter)
@lang.language()
@can_manage_vc
async def _stop(_, m: types.Message):
    if len(m.command) > 1:
        return
    chat_id = m.chat.id
    from KumsalTR.plugins.quiz import QUIZ_STATE, end_quiz_logic

    quiz_stopped = False
    if chat_id in QUIZ_STATE and QUIZ_STATE[chat_id].get("active"):
        QUIZ_STATE[chat_id]["active"] = False
        QUIZ_STATE[chat_id]["winner_found"].set()
        await end_quiz_logic(chat_id)
        quiz_stopped = True

    if await db.get_call(chat_id):
        await anon.stop(chat_id)
        return await m.reply_text(m.lang["play_stopped"].format(m.from_user.mention))

    if quiz_stopped:
        return await m.reply_text("<b>🛑 Aᴋᴛɪғ ʏᴀʀɪşᴍᴀ sᴏɴʟᴀɴᴅɪʀɪʟᴅɪ!</b>")

    await m.reply_text(m.lang["not_playing"])
