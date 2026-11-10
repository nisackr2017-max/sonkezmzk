# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of KumsalTR


from functools import wraps

from pyrogram import enums, types

from KumsalTR import app, db


def _lang_text(update, key: str, fallback: str) -> str:
    lang = getattr(update, "lang", None)
    if isinstance(lang, dict):
        return lang.get(key, fallback)
    return fallback


def admin_check(func):
    @wraps(func)
    async def wrapper(_, update: types.Message | types.CallbackQuery, *args, **kwargs):
        async def reply(text):
            if isinstance(update, types.Message):
                return await update.reply_text(text)
            return await update.answer(text, show_alert=True)

        chat_id = (
            update.chat.id
            if isinstance(update, types.Message)
            else update.message.chat.id
        )
        if not getattr(update, "from_user", None):
            return await reply(_lang_text(update, "user_no_perms", "Yetkin yok."))
        user_id = update.from_user.id
        admins = await db.get_admins(chat_id)

        if user_id in app.sudoers:
            return await func(_, update, *args, **kwargs)

        if user_id not in admins:
            return await reply(_lang_text(update, "user_no_perms", "Yetkin yok."))

        return await func(_, update, *args, **kwargs)

    return wrapper


def can_manage_vc(func):
    @wraps(func)
    async def wrapper(_, update: types.Message | types.CallbackQuery, *args, **kwargs):
        chat_id = (
            update.chat.id
            if isinstance(update, types.Message)
            else update.message.chat.id
        )
        if not getattr(update, "from_user", None):
            text = _lang_text(update, "user_no_perms", "Yetkin yok.")
            if isinstance(update, types.Message):
                return await update.reply_text(text)
            return await update.answer(text, show_alert=True)
        user_id = update.from_user.id

        if user_id in app.sudoers:
            return await func(_, update, *args, **kwargs)

        if await db.is_auth(chat_id, user_id):
            return await func(_, update, *args, **kwargs)

        admins = await db.get_admins(chat_id)
        if user_id in admins:
            return await func(_, update, *args, **kwargs)

        text = _lang_text(update, "user_no_perms", "Yetkin yok.")
        if isinstance(update, types.Message):
            return await update.reply_text(text)
        return await update.answer(text, show_alert=True)

    return wrapper


async def is_admin(chat_id: int, user_id: int) -> bool:
    if user_id in await db.get_admins(chat_id):
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        ]
    except Exception:
        return False


async def reload_admins(chat_id: int) -> list[int]:
    try:
        admins = [
            admin
            async for admin in app.get_chat_members(
                chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS
            )
            if getattr(admin, "user", None) and not admin.user.is_bot
        ]
        return [admin.user.id for admin in admins]
    except Exception:
        return []
