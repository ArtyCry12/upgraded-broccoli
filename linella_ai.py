"""
Linella AI Integration — GPT-4o через OpenAI API.
Используется для:
  - авто-генерации текстов акций
  - классификации тикетов поддержки
  - подбора персональных рекомендаций клиентам
"""
import frappe
from openai import OpenAI

SYSTEM_PROMPT = """
Ты — AI-ассистент компании Moldretail Group SRL (бренд Linella).
Отвечай кратко и профессионально. Используй язык пользователя (RO/RU/EN).
Linella — крупнейшая розничная сеть Молдовы: 190+ магазинов, 6000+ сотрудников.
Программа лояльности: Linella Card (Bronze/Silver/Gold/Platinum).
Инициативы: Produs Local, Linella Forest.
""".strip()


def _get_client():
    api_key = frappe.conf.get("openai_api_key") or frappe.db.get_single_value(
        "Linella CRM Settings", "openai_api_key"
    )
    if not api_key:
        frappe.throw(frappe._("OpenAI API Key не настроен в Linella CRM Settings"))
    return OpenAI(api_key=api_key)


@frappe.whitelist()
def generate_promotion_copy(promotion_name: str) -> dict:
    """Генерирует тексты для акции на RO и RU."""
    promo = frappe.get_doc("Promotion", promotion_name)
    items_summary = ", ".join(
        [f"{i.item_name} (-{promo.discount_pct}%)" for i in (promo.items or [])]
    ) or "товары по акции"

    prompt = (
        f"Напиши привлекательный пост для Instagram и TikTok об акции Linella.\n"
        f"Тип: {promo.promotion_type}\n"
        f"Товары: {items_summary}\n"
        f"Скидка: {promo.discount_pct or 0}%\n"
        f"Действует до: {promo.end_date}\n\n"
        f"Верни JSON: {{\"caption_ro\": \"...\", \"caption_ru\": \"...\", "
        f"\"hashtags\": \"...\", \"tiktok_hook\": \"...\"}}"
    )
    client = _get_client()
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=600,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    import json
    return json.loads(resp.choices[0].message.content)


@frappe.whitelist()
def classify_ticket(ticket_name: str) -> dict:
    """Авто-классифицирует тикет: определяет категорию и приоритет."""
    ticket = frappe.get_doc("Support Ticket", ticket_name)
    prompt = (
        f"Тема тикета: {ticket.subject}\n"
        f"Описание: {ticket.description or '—'}\n\n"
        f"Верни JSON: {{\"category\": \"...\", \"priority\": \"Низкий|Средний|Высокий|Критический\", "
        f"\"suggested_response\": \"краткий ответ клиенту\"}}\n"
        f"Категории: Качество товара, Цена / Акция, Обслуживание, Доставка / Онлайн заказ, "
        f"Linella Card, Мобильное приложение, Возврат товара, Ошибка на кассе, Другое"
    )
    client = _get_client()
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=400,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    import json
    result = json.loads(resp.choices[0].message.content)
    # Авто-применяем результат
    frappe.db.set_value("Support Ticket", ticket_name, {
        "category": result.get("category"),
        "priority":  result.get("priority", "Средний"),
    })
    return result


@frappe.whitelist()
def get_customer_recommendations(card_name: str) -> dict:
    """Персональные рекомендации для держателя Linella Card."""
    card = frappe.get_doc("Loyalty Card", card_name)
    txns = frappe.get_all(
        "Loyalty Transaction",
        filters={"card": card_name, "transaction_type": "Earn"},
        fields=["store", "purchase_amount", "promotion"],
        limit=20,
        order_by="creation desc",
    )
    stores = list({t.store for t in txns if t.store})
    promos_used = list({t.promotion for t in txns if t.promotion})

    prompt = (
        f"Клиент Linella:\n"
        f"Имя: {card.customer_name}\n"
        f"Уровень карты: {card.tier}\n"
        f"Баланс: {card.points_balance} баллов\n"
        f"Средний чек: {card.avg_basket_mdl} MDL\n"
        f"Любимые магазины: {', '.join(stores) or 'нет данных'}\n"
        f"Использованные акции: {', '.join(promos_used) or 'нет'}\n\n"
        f"Предложи 3 персональные рекомендации.\n"
        f"Верни JSON: {{\"recommendations\": [{{\"title\": \"...\", \"description\": \"...\", "
        f"\"action\": \"...\"}}]}}"
    )
    client = _get_client()
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    import json
    return json.loads(resp.choices[0].message.content)
