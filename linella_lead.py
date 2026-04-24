import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import today, add_days


class LinellaLead(Document):
    """
    Модель лида Linella CRM.
    Структура следует паттерну ERPNext: каждый DocType —
    отдельный класс с валидацией и хуками событий.
    """

    def validate(self):
        self._validate_email()
        self._set_default_followup()
        self._auto_qualify()

    def on_submit(self):
        self._create_opportunity_if_qualified()
        self._log_activity("Лид подтверждён и передан в работу")

    def on_update(self):
        if self.status == "Выигран":
            self._create_contact()
            frappe.msgprint(_("🎉 Лид выигран! Контакт создан автоматически."))

    # ── Приватные методы ─────────────────────────────────

    def _validate_email(self):
        if self.email and "@" not in self.email:
            frappe.throw(_("Некорректный email: {0}").format(self.email))

    def _set_default_followup(self):
        if not self.next_followup and self.status in ("Новый", "Квалифицирован"):
            self.next_followup = add_days(today(), 3)

    def _auto_qualify(self):
        """Автоматически квалифицирует лид при наличии ключевых данных."""
        if (self.email and self.phone and
                self.annual_revenue and float(self.annual_revenue) > 500000 and
                self.status == "Новый"):
            self.status = "Квалифицирован"
            self.probability = 30

    def _create_opportunity(self):
        opp = frappe.get_doc({
            "doctype": "Linella Opportunity",
            "lead":        self.name,
            "company":     self.lead_name,
            "contact":     self.contact_person,
            "email":       self.email,
            "phone":       self.phone,
            "deal_value":  self.expected_deal_value,
            "stage":       "Квалификация",
            "assigned_to": self.assigned_to,
            "region":      self.region,
        })
        opp.insert(ignore_permissions=True)
        return opp.name

    def _create_opportunity_if_qualified(self):
        if self.status == "Квалифицирован":
            opp_name = self._create_opportunity()
            frappe.msgprint(
                _("Сделка {0} создана автоматически.").format(opp_name)
            )

    def _create_contact(self):
        if not frappe.db.exists("Linella Contact", {"email": self.email}):
            contact = frappe.get_doc({
                "doctype": "Linella Contact",
                "full_name":  self.contact_person or self.lead_name,
                "company":    self.lead_name,
                "email":      self.email,
                "phone":      self.phone,
                "lead":       self.name,
                "contact_type": "B2B",
            })
            contact.insert(ignore_permissions=True)

    def _log_activity(self, description: str):
        frappe.get_doc({
            "doctype":     "Linella Activity",
            "lead":        self.name,
            "activity_type": "Note",
            "description": description,
            "user":        frappe.session.user,
        }).insert(ignore_permissions=True)


# ── Whitelisted API endpoints ────────────────────────────

@frappe.whitelist()
def get_lead_stats():
    """Возвращает агрегированную статистику лидов для дашборда."""
    return frappe.db.sql("""
        SELECT
            status,
            COUNT(*) as count,
            SUM(expected_deal_value) as total_value
        FROM `tabLinella Lead`
        WHERE docstatus < 2
        GROUP BY status
        ORDER BY FIELD(status,
            'Новый','Квалифицирован','Переговоры',
            'Коммерческое предложение','Выигран','Проигран','Отложен')
    """, as_dict=True)


@frappe.whitelist()
def bulk_assign(lead_names: list, user: str):
    """Массовое назначение лидов на сотрудника."""
    for name in frappe.parse_json(lead_names):
        frappe.db.set_value("Linella Lead", name, "assigned_to", user)
    frappe.db.commit()
    return {"assigned": len(lead_names)}
