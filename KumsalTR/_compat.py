# Kütüphane uyumluluk kontrolü.
# Yanlış kütüphane (eski pyrogram) kuruluysa anlaşılır bir mesaj verir,
# renkli buton desteği olmayan kurigram sürümlerinde botun çökmesini engeller.

import enum
import inspect
import logging

log = logging.getLogger("KumsalTR.compat")

COZUM = (
    "\n\nÇÖZÜM (terminale sırayla yazın):\n"
    "  pip uninstall -y pyrogram\n"
    "  pip install -U -r requirements.txt\n"
    "  pip install -U kurigram\n"
)

try:
    import pyrogram
    from pyrogram import enums, types
except ImportError as e:
    raise SystemExit(
        "❌ Telegram kütüphanesi (kurigram) yüklenemedi.\n"
        f"Asıl hata: {type(e).__name__}: {e}" + COZUM
    )

# Eski/orijinal pyrogram'da LinkPreviewOptions yoktur -> bot.py çöker
if not hasattr(types, "LinkPreviewOptions"):
    raise SystemExit(
        f"❌ Yanlış kütüphane kurulu: pyrogram {getattr(pyrogram, '__version__', '?')}.\n"
        "Bu bot 'kurigram' ister; eski 'pyrogram' paketi onu eziyor." + COZUM
    )

# Renkli buton enum'u yoksa sahte bir tane ekle (butonlar renksiz görünür ama çalışır)
if not hasattr(enums, "ButtonStyle"):
    class ButtonStyle(enum.Enum):
        DEFAULT = "default"
        PRIMARY = "primary"
        SUCCESS = "success"
        DANGER = "danger"

    enums.ButtonStyle = ButtonStyle
    log.warning("Bu kurigram sürümünde renkli buton yok; butonlar renksiz gösterilecek.")

# InlineKeyboardButton 'style' / 'icon_custom_emoji_id' desteklemiyorsa bu argümanları sessizce at
_params = inspect.signature(types.InlineKeyboardButton.__init__).parameters
_has_style = "style" in _params
_has_icon = "icon_custom_emoji_id" in _params

if not (_has_style and _has_icon):
    _orig_init = types.InlineKeyboardButton.__init__

    def _patched_init(self, *args, style=None, icon_custom_emoji_id=None, **kwargs):
        if _has_style and style is not None:
            kwargs["style"] = style
        if _has_icon and icon_custom_emoji_id is not None:
            kwargs["icon_custom_emoji_id"] = icon_custom_emoji_id
        _orig_init(self, *args, **kwargs)

    types.InlineKeyboardButton.__init__ = _patched_init
    log.warning(
        "Bu kurigram sürümü buton renk/emoji özelliğini tam desteklemiyor; "
        "butonlar normal görünecek. Güncellemek için: pip install -U kurigram"
    )

# kurigram 2.2.17+ sürümlerinde Message.reply / reply_text içinden 'quote' ve
# 'disable_web_page_preview' kaldırıldı. Eski çağrıların çökmemesi için uyumluluk yaması:
_reply_params = inspect.signature(types.Message.reply_text).parameters
if "quote" not in _reply_params or "disable_web_page_preview" not in _reply_params:
    for _method_name in ("reply", "reply_text", "reply_photo", "reply_audio", "reply_video", "edit_text", "edit"):
        _orig_method = getattr(types.Message, _method_name, None)
        if _orig_method is None:
            continue
        _m_params = inspect.signature(_orig_method).parameters

        def _make_msg_wrapper(orig, params):
            async def _wrapped(self, *args, **kwargs):
                if "quote" in kwargs and "quote" not in params:
                    kwargs.pop("quote", None)
                if "disable_web_page_preview" in kwargs and "disable_web_page_preview" not in params:
                    disabled = kwargs.pop("disable_web_page_preview", None)
                    if disabled and "link_preview_options" in params and "link_preview_options" not in kwargs:
                        kwargs["link_preview_options"] = types.LinkPreviewOptions(is_disabled=True)
                return await orig(self, *args, **kwargs)
            return _wrapped

        setattr(types.Message, _method_name, _make_msg_wrapper(_orig_method, _m_params))

_send_params = inspect.signature(pyrogram.Client.send_message).parameters
if "disable_web_page_preview" not in _send_params:
    _orig_send = pyrogram.Client.send_message

    async def _patched_send_message(self, *args, **kwargs):
        if "disable_web_page_preview" in kwargs:
            disabled = kwargs.pop("disable_web_page_preview", None)
            if disabled and "link_preview_options" not in kwargs:
                kwargs["link_preview_options"] = types.LinkPreviewOptions(is_disabled=True)
        return await _orig_send(self, *args, **kwargs)

    pyrogram.Client.send_message = _patched_send_message
