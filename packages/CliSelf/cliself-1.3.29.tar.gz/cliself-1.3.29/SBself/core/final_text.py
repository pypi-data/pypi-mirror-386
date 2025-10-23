# SBself/core/final_text.py

import random
from typing import List, Optional, Union

from ..config import AllConfig
from ..core.utils import make_mention_html  # <a href="tg://user?id=...">label</a>

try:
    from pyrogram.types import Message as _PyroMessage  # type: ignore
except Exception:
    _PyroMessage = None  # type: ignore


def get_random_text() -> str:
    lines = AllConfig.setdefault("text", {}).setdefault("lines", [])
    clean = [str(x).strip() for x in lines if str(x).strip()]
    return random.choice(clean) if clean else ""


def _caption_from_config() -> str:
    text_cfg = AllConfig.setdefault("text", {}) 
    """
    کپشن از کانفیگ اسپمر، فقط وقتی پیام نداریم/نداده‌ایم.
    """
    scfg = AllConfig.setdefault("spammer", {})
    caption = (text_cfg.get("caption") or "").strip()
    use_caption = bool(scfg.get("caption_on", False)) or bool(caption)
    return f"\n{caption}" if (use_caption and caption) else ""

def _normalize_user_id(val) -> Optional[int]:
    try:
        return int(str(val).strip().lstrip("@"))
    except Exception:
        return None


def build_mentions() -> str:
    mcfg = AllConfig.setdefault("mention", {})
    parts: List[str] = []

    label = (mcfg.get("textMen") or "mention").strip() or "mention"

    if mcfg.get("is_menshen") and mcfg.get("useridMen"):
        uid = _normalize_user_id(mcfg.get("useridMen"))
        if uid:
            parts.append(make_mention_html(uid, label))

    if mcfg.get("group_menshen") and mcfg.get("group_ids"):
        for gid in mcfg.get("group_ids", []):
            g = _normalize_user_id(gid)
            if g:
                parts.append(make_mention_html(g, label))

    return ("\n" + " ".join(parts)) if parts else ""


def _extract_from_message(msg) -> tuple[str, str]:
    """
    از Message، متن پایه و کپشنِ پیام را استخراج می‌کند.
    base_text: caption اگر بود؛ وگرنه text؛ وگرنه ""
    msg_caption: کپشن پیام (اگر رسانه‌ای بود). این همان cap است و
                 جدا برنمی‌گردانیم که تکرار نشود؛ همان cap را در base می‌گذاریم.
    """
    base_text = ""
    msg_caption = ""
    try:
        cap = (getattr(msg, "caption", None) or "").strip()
        txt = (getattr(msg, "text", None) or "").strip()
        base_text = cap or txt or ""
        # اگر بخواهی کپشن پیام جدا اضافه شود، می‌توانی این‌جا:
        # msg_caption = f"\n{cap}" if cap and base_text != cap else ""
        msg_caption = ""  # تکرار نکنیم؛ cap را همان‌جا در base گذاشتیم
    except Exception:
        pass
    return base_text, msg_caption


def build_final_text(base: Optional[Union[str, object]] = None) -> str:
    """
    ترتیب: متن پایه → (کپشنِ پیام اگر Message باشد، وگرنه کپشن کانفیگ) → منشن‌ها
    - اگر base = Message: از caption/text پیام استفاده می‌شود و کپشنِ پیام لحاظ می‌گردد.
      (کپشن کانفیگ در این حالت اضافه نمی‌شود تا دوگانه نشود)
    - اگر base = str یا None: از همان رشته (یا متن تصادفی) استفاده می‌شود و
      کپشن کانفیگ (در صورت فعال بودن) اضافه می‌شود.
    - در هر دو حالت، منشن‌ها در انتها اضافه می‌شوند.
    """
    msg_given = (_PyroMessage is not None and isinstance(base, _PyroMessage))

    if msg_given:
        base_text, msg_caption = _extract_from_message(base)
        # در حالت پیام، کپشن پیام در base_text ادغام شده؛ msg_caption خالی است.
        caption_part = msg_caption  # عمداً خالی می‌ماند تا دوباره‌کاری نشود
    else:
        base_text = (str(base).strip() if isinstance(base, str) else "") or get_random_text()
        caption_part = _caption_from_config()

    if not base_text:
        return ""

    mentions_part = build_mentions()
    return "".join([base_text, caption_part, mentions_part])
