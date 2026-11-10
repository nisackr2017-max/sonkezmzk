# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of KumsalTR


import json
from functools import wraps
from pathlib import Path

from pyrogram import errors

from KumsalTR import db, logger

lang_codes = {
    "ar": "Arabic",
    "de": "German",
    "en": "Türkçe",
    "es": "Spanish",
    "fr": "French",
    "hi": "Hindi",
    "ja": "Japanese",
    "my": "Burmese",
    "pa": "Punjabi",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
}


class SafeLangDict(dict):
    """Dictionary that falls back to default language or key name instead of raising KeyError."""

    def __init__(self, data: dict, fallback: dict | None = None):
        super().__init__(data)
        self._fallback = fallback or {}

    def __missing__(self, key: str) -> str:
        if key in self._fallback:
            return self._fallback[key]
        return str(key)


class Language:
    """
    Language class for managing multilingual support using JSON language files.
    """

    def __init__(self):
        self.lang_codes = lang_codes
        self.lang_dir = Path("KumsalTR/locales")
        self.languages = self.load_files()

    def load_files(self):
        raw_languages = {}
        lang_files = {file.stem: file for file in self.lang_dir.glob("*.json")}
        for lang_code, lang_file in lang_files.items():
            with open(lang_file, "r", encoding="utf-8") as file:
                raw_languages[lang_code] = json.load(file)

        base_lang = raw_languages.get("en", {})
        languages = {}
        for lang_code, data in raw_languages.items():
            merged = {**base_lang, **data}
            languages[lang_code] = SafeLangDict(merged, fallback=base_lang)

        logger.info(f"Loaded languages: {', '.join(languages.keys())}")
        return languages

    async def get_lang(self, chat_id: int) -> dict:
        lang_code = await db.get_lang(chat_id)
        return self.languages.get(lang_code) or self.languages.get("en")

    def get_languages(self) -> dict:
        files = {f.stem for f in self.lang_dir.glob("*.json")}
        return {code: self.lang_codes.get(code, code) for code in sorted(files)}

    def language(self):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                fallen = next(
                    (
                        arg
                        for arg in args
                        if hasattr(arg, "chat") or hasattr(arg, "message")
                    ),
                    None,
                )
                if fallen is None:
                    return await func(*args, **kwargs)

                if hasattr(fallen, "chat") and fallen.chat:
                    chat = fallen.chat
                elif getattr(fallen, "message", None) is not None:
                    chat = fallen.message.chat
                else:
                    return await func(*args, **kwargs)

                if chat.id in db.blacklisted:
                    logger.warning(f"Chat {chat.id} is blacklisted, leaving...")
                    try:
                        return await chat.leave()
                    except Exception:
                        return

                lang_code = await db.get_lang(chat.id)
                lang_dict = self.languages.get(lang_code) or self.languages.get("en")
                setattr(fallen, "lang", lang_dict)
                if getattr(fallen, "message", None) is not None:
                    setattr(fallen.message, "lang", lang_dict)
                try:
                    return await func(*args, **kwargs)
                except (errors.MessageNotModified, errors.QueryIdInvalid):
                    return
                except Exception as exc:
                    if "Forbidden" not in type(exc).__name__:
                        raise
                    logger.warning(f"Cannot write to chat {chat.id}, leaving...")
                    try:
                        return await chat.leave()
                    except Exception:
                        return

            return wrapper

        return decorator
