import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import today, getdate


TIER_THRESHOLDS = {
    "Bronze":   0,
    "Silver":   500,
    "Gold":     2000,
    "Platinum": 10000,
}


class LoyaltyCard(Document):

    def before_insert(self):
        self.registered_on = frappe.utils.now()
        self._assign_tier()

    def validate(self):
        self._validate_phone()
        self._assign_tier()
        self._calculate_rfm()

    def after_insert(self):
        send_welcome_sms(self)

    # ── Tier Logic ───────────────────────────────────────

    def _assign_tier(self):
        balance = float(self.points_balance or 0)
        new_tier = "Bronze"
        for tier, threshold in sorted(TIER_THRESHOLDS.items(), key=lambda x: -x[1]):
            if balance >= threshold:
                new_tier = tier
                break
        if self.tier != new_tier:
            self.tier = new_tier
            if not self.is_new():
                self._notify_tier_change(new_tier)

    def _notify_tier_change(self, new_tier: str):
        frappe.publish_realtime(
            "loyalty_tier_changed",
            {"card": self.name, "tier": new_tier},
            user=frappe.session.user,
        )

    # ── RFM Scoring ──────────────────────────────────────

    def _calculate_rfm(self):
        """Простой RFM: Recency + Frequency + Monetary."""
        recency = self._recency_score()
        frequency = min(float(self.visit_frequency or 0) / 4.0, 5)
        monetary = min(float(self.avg_basket_mdl or 0) / 200.0, 5)
        self.rfm_score = round((recency + frequency + monetary) / 3, 2)

    def _recency_score(self) -> float:
        if not self.last_purchase:
            return 0
        days_ago = (getdate(today()) - getdate(self.last_purchase)).days
        if days_ago <= 7:    return 5
        if days_ago <= 14:   return 4
        if days_ago <= 30:   return 3
        if days_ago <= 90:   return 2
        return 1

    # ── Validation ───────────────────────────────────────

    def _validate_phone(self):
        phone = (self.phone or "").strip()
        if phone and not (phone.startswith("+373") or phone.startswith("0")):
            frappe.throw(_("Телефон должен начинаться с +373 или 0"))


# ── Whitelisted API ───────────────────────────────────────

@frappe.whitelist()
def send_welcome_sms(doc):
    """Отправляет приветственное SMS при создании карты."""
    if isinstance(doc, str):
        doc = frappe.get_doc("Loyalty Card", doc)
    # Интеграция с SMS-шлюзом (заменить на реальный провайдер)
    frappe.logger().info(
        f"[Linella SMS] Отправка на {doc.phone}: "
        f"Добро пожаловать в Linella, {doc.customer_name}! "
        f"Ваша карта: {doc.name}"
    )
    return {"status": "sent", "card": doc.name}


@frappe.whitelist()
def add_points(card_name: str, points: float, purchase_amount: float, store: str):
    """Начислить баллы за покупку."""
    card = frappe.get_doc("Loyalty Card", card_name)
    if card.card_status != "Активна":
        frappe.throw(_("Карта не активна"))

    card.points_balance = float(card.points_balance or 0) + float(points)
    card.total_spent_mdl = float(card.total_spent_mdl or 0) + float(purchase_amount)
    card.last_purchase = today()
    card.save(ignore_permissions=True)

    # Создаём транзакцию
    frappe.get_doc({
        "doctype":        "Loyalty Transaction",
        "card":           card_name,
        "transaction_type": "Earn",
        "points":         points,
        "purchase_amount": purchase_amount,
        "store":          store,
        "balance_after":  card.points_balance,
    }).insert(ignore_permissions=True)

    return {"new_balance": card.points_balance, "tier": card.tier}


@frappe.whitelist()
def redeem_points(card_name: str, points_to_redeem: float, store: str):
    """Списать баллы при оплате."""
    card = frappe.get_doc("Loyalty Card", card_name)
    if card.card_status != "Активна":
        frappe.throw(_("Карта не активна"))
    if float(card.points_balance or 0) < float(points_to_redeem):
        frappe.throw(_("Недостаточно баллов. Доступно: {0}").format(card.points_balance))

    card.points_balance = float(card.points_balance) - float(points_to_redeem)
    card.save(ignore_permissions=True)

    frappe.get_doc({
        "doctype":        "Loyalty Transaction",
        "card":           card_name,
        "transaction_type": "Redeem",
        "points":         -float(points_to_redeem),
        "store":          store,
        "balance_after":  card.points_balance,
    }).insert(ignore_permissions=True)

    return {
        "redeemed": points_to_redeem,
        "new_balance": card.points_balance,
        "mdl_equivalent": float(points_to_redeem) * 0.1,
    }
