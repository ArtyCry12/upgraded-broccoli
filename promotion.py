import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, today


class Promotion(Document):

    def validate(self):
        validate_dates(self)
        self._validate_discount()

    def before_submit(self):
        self.status = "Активна"

    def on_submit(self):
        publish_to_channels(self)

    def on_cancel(self):
        self.status = "Отменена"

    def _validate_discount(self):
        if not self.discount_pct and not self.discount_mdl:
            frappe.throw(_("Укажите скидку в процентах или в MDL"))
        if self.discount_pct and float(self.discount_pct) > 90:
            frappe.throw(_("Скидка не может превышать 90%"))


# ── Хуки событий (вызываются из hooks.py) ───────────────

def validate_dates(doc):
    """Проверяет корректность дат акции."""
    if isinstance(doc, str):
        doc = frappe.get_doc("Promotion", doc)
    if getdate(doc.end_date) < getdate(doc.start_date):
        frappe.throw(_("Дата окончания не может быть раньше даты начала"))
    if getdate(doc.end_date) < getdate(today()):
        frappe.throw(_("Дата окончания акции уже прошла"))


def publish_to_channels(doc):
    """Публикует акцию во все подключённые каналы."""
    if isinstance(doc, str):
        doc = frappe.get_doc("Promotion", doc)
    for channel in (doc.channels or []):
        if channel.channel_type == "Сайт Linella":
            _publish_to_website(doc)
        elif channel.channel_type == "Telegram Bot":
            _publish_to_telegram(doc)
        elif channel.channel_type == "Email":
            _publish_to_email(doc)
        elif channel.channel_type == "Push":
            _publish_push_notification(doc)
    frappe.logger().info(f"[Linella Promotion] {doc.name} опубликована")


def _publish_to_website(doc):
    frappe.logger().info(f"[Website] Публикация акции {doc.name}")


def _publish_to_telegram(doc):
    frappe.logger().info(f"[Telegram] Отправка акции {doc.name}")


def _publish_to_email(doc):
    frappe.logger().info(f"[Email] Рассылка акции {doc.name}")


def _publish_push_notification(doc):
    frappe.logger().info(f"[Push] Push-уведомление о {doc.name}")


# ── API ──────────────────────────────────────────────────

@frappe.whitelist()
def get_active_promotions(segment=None, store=None):
    """Возвращает активные акции с опциональной фильтрацией."""
    filters = {
        "status": "Активна",
        "start_date": ["<=", today()],
        "end_date":   [">=", today()],
    }
    if segment:
        filters["target_segment"] = segment
    if store and store != "Все магазины":
        filters["target_stores"] = ["in", [store, "Все магазины"]]

    return frappe.get_all(
        "Promotion",
        filters=filters,
        fields=[
            "name", "promotion_name", "promotion_type",
            "discount_pct", "discount_mdl", "end_date",
            "banner_url", "description_ro", "description_ru",
        ],
        order_by="end_date asc",
    )
