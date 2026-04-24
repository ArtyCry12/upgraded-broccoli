import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime, time_diff_in_hours, add_to_date

# SLA в часах по приоритету
SLA_HOURS = {
    "Критический": 2,
    "Высокий":     8,
    "Средний":     24,
    "Низкий":      72,
}


class SupportTicket(Document):

    def before_insert(self):
        self._set_due_date()

    def validate(self):
        self._check_sla_breach()

    def on_submit(self):
        self.status = "В работе"
        notify_customer(self)

    # ── Бизнес-логика ────────────────────────────────────

    def _set_due_date(self):
        hours = SLA_HOURS.get(self.priority, 24)
        self.due_date = add_to_date(now_datetime(), hours=hours)

    def _check_sla_breach(self):
        if self.due_date and now_datetime() > self.due_date:
            if self.status not in ("Решён", "Закрыт"):
                self.sla_breach = 1

    def mark_resolved(self, notes: str = ""):
        self.status         = "Решён"
        self.resolved_by    = frappe.session.user
        self.resolved_on    = now_datetime()
        self.resolution_notes = notes
        self.response_time_hrs = time_diff_in_hours(
            self.resolved_on, self.creation
        )
        self.save(ignore_permissions=True)


# ── Хуки событий ─────────────────────────────────────────

def auto_assign(doc, method=None):
    """Автоматически назначает тикет свободному агенту."""
    if doc.assigned_to or doc.status == "Закрыт":
        return
    agent = _find_available_agent(doc.category)
    if agent:
        doc.assigned_to = agent
        doc.db_set("assigned_to", agent)


def notify_customer(doc, method=None):
    """Уведомляет клиента об обновлении тикета."""
    if isinstance(doc, str):
        doc = frappe.get_doc("Support Ticket", doc)
    frappe.logger().info(
        f"[Linella Support] Уведомление клиента {doc.customer_name} "
        f"по тикету {doc.name} — статус: {doc.status}"
    )


def _find_available_agent(category: str):
    """Находит наименее загруженного агента поддержки."""
    agents = frappe.get_all(
        "Support Ticket",
        filters={"status": ["in", ["Открыт", "В работе"]]},
        fields=["assigned_to", "count(*) as cnt"],
        group_by="assigned_to",
        order_by="cnt asc",
        limit=1,
    )
    if agents and agents[0].assigned_to:
        return agents[0].assigned_to
    return None


# ── API ──────────────────────────────────────────────────

@frappe.whitelist()
def get_ticket_dashboard():
    """Статистика тикетов для дашборда поддержки."""
    return {
        "by_status": frappe.db.sql("""
            SELECT status, COUNT(*) as count
            FROM `tabSupport Ticket`
            WHERE docstatus < 2
            GROUP BY status
        """, as_dict=True),
        "by_priority": frappe.db.sql("""
            SELECT priority, COUNT(*) as count
            FROM `tabSupport Ticket`
            WHERE status NOT IN ('Решён','Закрыт') AND docstatus < 2
            GROUP BY priority
        """, as_dict=True),
        "avg_response_hrs": frappe.db.sql("""
            SELECT AVG(response_time_hrs) as avg_hrs
            FROM `tabSupport Ticket`
            WHERE status='Решён' AND response_time_hrs IS NOT NULL
        """, as_dict=True),
        "sla_breached": frappe.db.count("Support Ticket", {"sla_breach": 1}),
    }
