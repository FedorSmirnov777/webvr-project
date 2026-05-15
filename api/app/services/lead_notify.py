from __future__ import annotations

from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.config import settings
from app.models.commerce import Lead


def _safe(value: str | None) -> str:
    return (value or "").strip()


def _lead_type_label(lead_type: str) -> str:
    if lead_type == "test_drive":
        return "Тест-драйв"
    if lead_type == "quote":
        return "Запрос стоимости"
    return lead_type or "Не указан"


def send_lead_to_telegram(lead: Lead) -> None:
    token = _safe(settings.telegram_bot_token)
    chat_id = _safe(settings.telegram_chat_id)
    if not token or not chat_id:
        return

    payload = lead.payload or {}
    preferred_date = payload.get("preferred_date") or "-"
    preferred_time = payload.get("preferred_time") or "-"
    source = payload.get("source") or "site"

    text = (
        "Новая заявка\n\n"
        f"Тип: {_lead_type_label(lead.lead_type)}\n"
        f"Имя: {lead.full_name}\n"
        f"Email: {lead.email}\n"
        f"Телефон: {lead.phone or '-'}\n"
        f"Дата: {preferred_date}\n"
        f"Время: {preferred_time}\n"
        f"Источник: {source}\n"
        f"Сообщение: {lead.note or '-'}\n"
        f"Lead ID: {lead.id}"
    )
    params = urlencode({"chat_id": chat_id, "text": text})
    url = f"https://api.telegram.org/bot{token}/sendMessage?{params}"
    with urlopen(url, timeout=10):
        pass
