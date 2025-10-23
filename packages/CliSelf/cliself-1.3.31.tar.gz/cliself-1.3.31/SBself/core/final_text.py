# -*- coding: utf-8 -*-
# File: SBself/core/final_text.py
#
# نسخه‌ی سازگار با همه‌ی محیط‌ها:
# - مسیر HTML: build_final_text(base)  → رشته (برای parse_mode=HTML)
# - مسیر بدون parse_mode: build_final_text_entities(base, resolver) → (text, entities|None)
#   * برای username ها: فقط @username در متن می‌آید (تلگرام خودکار لینک می‌کند)
#   * برای ID عددی: اگر resolver(int)->User بدهی، TEXT_MENTION ساخته می‌شود

from __future__ import annotations

import random
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ..config import AllConfig
from ..core.utils import make_mention_html  # <a href="tg://user?id=...">label</a>

# --- Imports اختیاری Pyrogram ---
try:
    from pyrogram.types import Message as _PyroMessage  # type: ignore
except Exception:
    _PyroMessage = None  # type: ignore

try:
    from pyrogram.types import MessageEntity, User  # type: ignore
except Exception:
    MessageEntity = None  # type: ignore
    User = None  # type: ignore

try:
    from pyrogram.enums import MessageEntityType as _METype  # type: ignore
except Exception:
    _METype = None  # type: ignore


# =========================
# متنِ تصادفی
# =========================
def get_random_text() -> str:
    lines = AllConfig.setdefault("text", {}).setdefault("lines", [])
    clean = [str(x).strip() for x in lines if str(x).strip()]
    return random.choice(clean) if clean else ""


# =========================
# کپشن از کانفیگ (وقتی base=Message نیست)
# =========================
def _caption_from_config() -> str:
    """
    کپشن از کانفیگ (فقط وقتی base=Message نباشد)
    منبع: AllConfig["text"]["caption"] + سوییچ: AllConfig["spammer"]["caption_on"]
    """
    text_cfg = AllConfig.setdefault("text", {})
    scfg = AllConfig.setdefault("spammer", {})
    caption = (text_cfg.get("caption") or "").strip()
    use_caption = bool(scfg.get("caption_on", False)) or bool(caption)
    return f"\n{caption}" if (use_caption and caption) else ""


# =========================
# نرمال‌سازی ورودی‌های منشن
# =========================
_USERNAME_RE = re.compile(r"[A-Za-z0-9_]{3,}")

def _normalize_user_id(val: Any) -> Optional[int]:
    """اگر ورودی به عدد تبدیل شود (ID تلگرام)، آن را برمی‌گرداند؛ وگرنه None."""
    try:
        s = str(val).strip().lstrip("@")
        return int(s)
    except Exception:
        return None

def _normalize_username(val: Any) -> Optional[str]:
    """اگر ورودی username معتبر باشد (با/بی‌@)، برمی‌گرداند؛ وگرنه None."""
    try:
        s = str(val).strip().lstrip("@")
        if not s:
            return None
        return s if _USERNAME_RE.fullmatch(s) else None
    except Exception:
        return None


# =========================
# HTML-based mentions (برای parse_mode=HTML)
# =========================
def _make_username_link_html(username: str, label: str) -> str:
    return f'<a href="https://t.me/{username}">{label}</a>'

def build_mentions() -> str:
    """
    ساخت رشته‌ی منشن‌ها به صورت HTML.
    - برای ID عددی: tg://user?id=...
    - برای username: https://t.me/username
    خروجی: "" یا "\n<label/username> <label/username> ..."
    """
    mcfg = AllConfig.setdefault("mention", {})
    parts: List[str] = []

    label = (mcfg.get("textMen") or "mention").strip() or "mention"

    # تک
    single_val = mcfg.get("useridMen")
    if mcfg.get("is_menshen") and single_val:
        uid = _normalize_user_id(single_val)
        if uid:
            parts.append(make_mention_html(uid, label))
        else:
            uname = _normalize_username(single_val)
            if uname:
                parts.append(_make_username_link_html(uname, label))

    # گروهی
    if mcfg.get("group_menshen") and mcfg.get("group_ids"):
        for gid in mcfg.get("group_ids", []):
            uid = _normalize_user_id(gid)
            if uid:
                parts.append(make_mention_html(uid, label))
            else:
                uname = _normalize_username(gid)
                if uname:
                    parts.append(_make_username_link_html(uname, label))

    return ("\n" + " ".join(parts)) if parts else ""


# =========================
# استخراجِ base/caption از Message
# =========================
def _extract_from_message(msg: Any) -> Tuple[str, str]:
    """
    از Message، متن پایه و کپشنِ پیام را استخراج می‌کند.
    base_text: caption اگر بود؛ وگرنه text؛ وگرنه ""
    msg_caption: معمولاً خالی (چون cap را در base_text قرار می‌دهیم)
    """
    base_text = ""
    msg_caption = ""
    try:
        cap = (getattr(msg, "caption", None) or "").strip()
        txt = (getattr(msg, "text", None) or "").strip()
        base_text = cap or txt or ""
        msg_caption = ""
    except Exception:
        pass
    return base_text, msg_caption


# =========================
# HTML-based Final Text
# =========================
def build_final_text(base: Optional[Union[str, object]] = None) -> str:
    """
    ترتیب: base → (caption پیام اگر Message بود، وگرنه caption کانفیگ) → mentions(HTML)
    خروجی: رشتهٔ HTML (برای ارسال با parse_mode=HTML)
    """
    msg_given = (_PyroMessage is not None and isinstance(base, _PyroMessage))

    if msg_given:
        base_text, msg_caption = _extract_from_message(base)
        caption_part = msg_caption  # عمداً خالی است؛ cap در base_text اد شده
    else:
        base_text = (str(base).strip() if isinstance(base, str) else "") or get_random_text()
        caption_part = _caption_from_config()

    if not base_text:
        return ""

    mentions_part = build_mentions()
    return "".join([base_text, caption_part, mentions_part])


# =====================================================================
# Entities-based (بدون نیاز به parse_mode): TEXT_MENTION + @username
# =====================================================================
def _extract_base_and_caption_for_entities(base: Optional[Union[str, object]]) -> Tuple[str, str]:
    msg_given = (_PyroMessage is not None and isinstance(base, _PyroMessage))
    if msg_given:
        bt, _ = _extract_from_message(base)
        return bt, ""  # کپشن پیام داخل base است
    else:
        bt = (str(base).strip() if isinstance(base, str) else "") or get_random_text()
        return bt, _caption_from_config()

def _make_text_mention_entity(offset: int, length: int, user: Any) -> Optional[Any]:
    """
    ساخت ایمن MessageEntity از نوع TEXT_MENTION.
    اگر کلاس/enum در محیط در دسترس نباشد، None برمی‌گرداند تا از entity صرف‌نظر کنیم.
    """
    if MessageEntity is None:
        return None
    ent_type = _METype.TEXT_MENTION if _METype is not None else "text_mention"
    try:
        return MessageEntity(type=ent_type, offset=offset, length=length, user=user)  # type: ignore
    except Exception:
        # بعضی نسخه‌ها پارامترها را محدودتر می‌خواهند
        try:
            return MessageEntity(type=ent_type, offset=offset, length=length, user=user)  # type: ignore
        except Exception:
            return None

def build_mentions_entities(
    resolver: Optional[Callable[[int], Any]] = None
) -> Tuple[str, List[Any]]:
    """
    ساخت mentions بدون parse_mode:
      - اگر username باشد → فقط '@username' در متن (entity لازم نیست؛ تلگرام auto-link می‌کند)
      - اگر ID عددی باشد و resolver(User) بدهید → TEXT_MENTION واقعی ساخته می‌شود
      - اگر ID عددی باشد و resolver ندهید → فعلاً نادیده گرفته می‌شود
    خروجی: (mention_text, entities)
    """
    mcfg = AllConfig.setdefault("mention", {})
    label = (mcfg.get("textMen") or "mention").strip() or "mention"

    items: List[Tuple[str, Optional[Any]]] = []

    # تک
    single_val = mcfg.get("useridMen")
    if mcfg.get("is_menshen") and single_val:
        uid = _normalize_user_id(single_val)
        if uid is not None and resolver is not None:
            try:
                u = resolver(uid)  # باید pyrogram.types.User برگرداند
                if u:
                    items.append((label, u))
            except Exception:
                pass
        else:
            uname = _normalize_username(single_val)
            if uname:
                items.append((f"@{uname}", None))

    # گروهی
    if mcfg.get("group_menshen") and mcfg.get("group_ids"):
        for gid in mcfg.get("group_ids", []):
            uid = _normalize_user_id(gid)
            if uid is not None and resolver is not None:
                try:
                    u = resolver(uid)
                    if u:
                        items.append((label, u))
                except Exception:
                    pass
            else:
                uname = _normalize_username(gid)
                if uname:
                    items.append((f"@{uname}", None))

    if not items:
        return "", []

    # مونتاژ mention_text و entities محلی
    segments: List[str] = []
    entities: List[Any] = []
    offset = 0
    for idx, (segment, maybe_user) in enumerate(items):
        if idx == 0:
            segments.append("\n" + segment)
            seg_offset = offset + 1  # \n
        else:
            segments.append(" " + segment)
            seg_offset = offset + 1  # فاصله

        seg_len = len(segment)
        if maybe_user is not None:
            ent = _make_text_mention_entity(seg_offset, seg_len, maybe_user)
            if ent is not None:
                entities.append(ent)

        offset = seg_offset + seg_len

    mention_text = "".join(segments)
    return mention_text, entities


def build_final_text_entities(
    base: Optional[Union[str, object]] = None,
    resolver: Optional[Callable[[int], Any]] = None,
) -> Tuple[str, Optional[List[Any]]]:
    """
    خروجی نهایی بدون نیاز به parse_mode:
      text = base + caption + mention_text
      entities = TEXT_MENTION فقط برای آیتم‌هایی که User داشتند
    """
    base_text, cap = _extract_base_and_caption_for_entities(base)
    if not base_text:
        return "", None

    mention_text, local_entities = build_mentions_entities(resolver)
    final_text = f"{base_text}{cap}{mention_text}"

    if not local_entities:
        return final_text, None

    # entities را به انتهای متن منتقل می‌کنیم (offset کلّی)
    base_len = len(base_text + cap)
    adjusted: List[Any] = []
    for ent in local_entities:
        try:
            # کپی entity با offset جابه‌جا شده
            adjusted.append(
                MessageEntity(
                    type=getattr(ent, "type", "text_mention"),
                    offset=base_len + int(getattr(ent, "offset", 0)),
                    length=int(getattr(ent, "length", 0)),
                    user=getattr(ent, "user", None)  # type: ignore
                )
            )
        except Exception:
            # اگر سازندهٔ MessageEntity در محیط نبود، بی‌خیال entities می‌شویم
            adjusted = []
            break

    return final_text, (adjusted or None)


def build_final_text_or_entities(
    base: Optional[Union[str, object]] = None,
    resolver: Optional[Callable[[int], Any]] = None,
) -> Tuple[str, Optional[List[Any]]]:
    """
    مهاجرت نرم:
      - اگر resolver بدهید → خروجی مثل build_final_text_entities
      - اگر resolver ندهید → رشتهٔ HTML مثل build_final_text و entities=None
    """
    if resolver:
        return build_final_text_entities(base, resolver)
    else:
        return build_final_text(base), None
