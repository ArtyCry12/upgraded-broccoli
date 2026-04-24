# ─────────────────────────────────────────────────────────
#  Linella CRM — Frappe App Hooks
#  Следует структуре ERPNext: github.com/frappe/erpnext
# ─────────────────────────────────────────────────────────

app_name        = "linella_crm"
app_title       = "Linella CRM"
app_publisher   = "Moldretail Group SRL"
app_description = "Custom CRM system for Linella supermarket chain (190+ stores, Moldova)"
app_email       = "it@linella.md"
app_license     = "MIT"
app_version     = "1.0.0"
app_icon        = "🛒"
app_color       = "#e63946"   # Linella brand red

# ── Зависимости ────────────────────────────────────────────
required_apps = ["frappe"]

# ── Fixtures (данные, экспортируемые вместе с приложением) ─
fixtures = [
    {"dt": "Custom Field"},
    {"dt": "Property Setter"},
    {"dt": "Role", "filters": [["name", "in", [
        "Linella CRM Manager",
        "Linella Sales Rep",
        "Linella Support Agent",
        "Linella Marketing",
    ]]]},
    {"dt": "Workflow"},
]

# ── DocType классы ─────────────────────────────────────────
override_doctype_class = {}

# ── Документные события (хуки на сохранение/изменение) ────
doc_events = {
    "Linella Lead": {
        "on_submit":  "linella_crm.crm.doctype.linella_lead.linella_lead.on_submit",
        "on_update":  "linella_crm.crm.doctype.linella_lead.linella_lead.on_update",
    },
    "Loyalty Card": {
        "after_insert": "linella_crm.loyalty.doctype.loyalty_card.loyalty_card.send_welcome_sms",
    },
    "Support Ticket": {
        "on_update": "linella_crm.support.doctype.support_ticket.support_ticket.auto_assign",
        "on_submit": "linella_crm.support.doctype.support_ticket.support_ticket.notify_customer",
    },
    "Promotion": {
        "before_submit": "linella_crm.promotions.doctype.promotion.promotion.validate_dates",
        "on_submit":     "linella_crm.promotions.doctype.promotion.promotion.publish_to_channels",
    },
}

# ── Планировщик задач ──────────────────────────────────────
scheduler_events = {
    "daily": [
        "linella_crm.loyalty.tasks.expire_unused_points",
        "linella_crm.loyalty.tasks.recalculate_segments",
        "linella_crm.promotions.tasks.deactivate_expired_promotions",
    ],
    "weekly": [
        "linella_crm.analytics.tasks.generate_weekly_report",
        "linella_crm.crm.tasks.follow_up_stale_leads",
    ],
    "monthly": [
        "linella_crm.loyalty.tasks.send_loyalty_statements",
    ],
}

# ── Разрешения ─────────────────────────────────────────────
has_permission = {
    "Linella Lead":       "linella_crm.crm.permission.lead_permission",
    "Loyalty Card":       "linella_crm.loyalty.permission.card_permission",
    "Support Ticket":     "linella_crm.support.permission.ticket_permission",
    "Promotion":          "linella_crm.promotions.permission.promotion_permission",
}

# ── API endpoints (whitelist) ──────────────────────────────
# Регистрируются через @frappe.whitelist() в соответствующих модулях

# ── Веб-шаблоны ────────────────────────────────────────────
website_route_rules = [
    {"from_route": "/crm",       "to_route": "crm"},
    {"from_route": "/loyalty",   "to_route": "loyalty"},
    {"from_route": "/support",   "to_route": "support"},
]

# ── CSS / JS (подключаются ко всем страницам) ──────────────
app_include_css = ["/assets/linella_crm/css/linella.css"]
app_include_js  = ["/assets/linella_crm/js/linella.js"]

# ── Кастомные Dashboard Charts ─────────────────────────────
dashboards = {
    "linella_crm": "linella_crm.crm.dashboard.linella_dashboard"
}

# ── Уведомления ────────────────────────────────────────────
notification_config = "linella_crm.config.notifications.get_notification_config"
