# 🛒 Linella CRM

> Индивидуальная CRM-система для **Moldretail Group SRL** (бренд **Linella**).
> Построена на базе архитектуры [frappe/erpnext](https://github.com/frappe/erpnext).

---

## 📦 Модули системы

| Модуль | Описание | DocTypes |
|---|---|---|
| **CRM** | Лиды, контакты, воронка продаж, активности | Linella Lead, Linella Contact, Linella Opportunity, Linella Activity |
| **Loyalty** | Linella Card, баллы, тиры, RFM-сегментация | Loyalty Card, Loyalty Transaction, Loyalty Tier, Customer Segment |
| **Promotions** | Управление акциями, каналы публикации | Promotion, Promotion Item, Promotion Channel |
| **Support** | Тикеты, SLA, эскалации | Support Ticket, Ticket Comment, Ticket Escalation |
| **Analytics** | Отчёты, дашборды, AI-генерация | Reports × 4, Tasks, Linella AI |

---

## 🏗️ Архитектура (по ERPNext)

```
linella_crm/
├── linella_crm/
│   ├── hooks.py                    ← Точка входа Frappe (события, планировщик)
│   ├── install.py                  ← Скрипт установки + фикстуры
│   ├── config/
│   │   ├── desktop.py              ← Модули на главном экране
│   │   └── notifications.py        ← Счётчики уведомлений
│   ├── crm/
│   │   ├── doctype/
│   │   │   ├── linella_lead/       ← Лид с авто-квалификацией
│   │   │   ├── linella_contact/    ← B2B контакты
│   │   │   ├── linella_opportunity/← Воронка продаж (взвешенная стоимость)
│   │   │   └── linella_activity/   ← Лог звонков, встреч, писем
│   │   ├── report/lead_pipeline/   ← Отчёт по воронке
│   │   ├── dashboard/              ← Дашборд CRM
│   │   ├── tasks.py                ← Follow-up напоминания
│   │   └── permission.py           ← Контроль доступа
│   ├── loyalty/
│   │   ├── doctype/
│   │   │   ├── loyalty_card/       ← Linella Card (RFM, тиры, баллы)
│   │   │   ├── loyalty_transaction/← История начислений/списаний
│   │   │   ├── loyalty_tier/       ← Bronze/Silver/Gold/Platinum
│   │   │   └── customer_segment/   ← Сегменты для таргетинга
│   │   ├── report/loyalty_overview/← Обзор программы лояльности
│   │   ├── tasks.py                ← Сгорание, пересчёт RFM, выписки
│   │   └── permission.py
│   ├── promotions/
│   │   ├── doctype/
│   │   │   ├── promotion/          ← Акция с мульти-канальной публикацией
│   │   │   ├── promotion_item/     ← Товары акции (child table)
│   │   │   └── promotion_channel/  ← Каналы (Instagram, TikTok, Telegram…)
│   │   ├── report/promotion_roi/   ← ROI акций
│   │   ├── tasks.py                ← Деактивация истёкших
│   │   └── permission.py
│   ├── support/
│   │   ├── doctype/
│   │   │   ├── support_ticket/     ← Тикет с SLA и авто-назначением
│   │   │   ├── ticket_comment/     ← Комментарии (публичные/внутренние)
│   │   │   └── ticket_escalation/  ← Эскалации
│   │   ├── report/support_sla/     ← Отчёт по SLA
│   │   └── permission.py
│   ├── analytics/
│   │   ├── linella_ai.py           ← GPT-4o: генерация текстов, классификация
│   │   └── tasks.py                ← Еженедельный отчёт
│   └── public/
│       ├── css/linella.css         ← Стили с брендингом Linella
│       └── js/linella.js           ← Глобальный JS: утилиты, real-time
├── fixtures/
│   ├── loyalty_tier.json           ← 4 тира лояльности
│   └── customer_segment.json       ← 6 сегментов покупателей
├── setup.py
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## 🚀 Установка

### Вариант А: Frappe Bench (рекомендуется)

```bash
# 1. Установить bench
pip install frappe-bench

# 2. Инициализировать
bench init frappe-bench --frappe-branch version-15
cd frappe-bench

# 3. Создать сайт
bench new-site linella.localhost \
  --admin-password admin \
  --db-root-password root

# 4. Клонировать приложение
bench get-app linella_crm https://github.com/linella/linella_crm.git

# 5. Установить
bench --site linella.localhost install-app linella_crm

# 6. Запустить
bench start
```

Открыть: **http://linella.localhost:8000**

### Вариант Б: Docker (быстрый старт)

```bash
git clone https://github.com/linella/linella_crm.git
cd linella_crm
docker-compose up -d
```

---

## ⚙️ Настройка

### OpenAI API для AI-функций

В `site_config.json` вашего Frappe-сайта добавьте:
```json
{
  "openai_api_key": "sk-..."
}
```

Или через **Linella CRM Settings** в интерфейсе.

### Уровни лояльности (настраиваются через UI)

| Уровень  | Минимум баллов | Баллов за MDL | Множитель |
|----------|---------------|---------------|-----------|
| Bronze   | 0             | 1.0           | ×1        |
| Silver   | 500           | 1.5           | ×1.5      |
| Gold     | 2,000         | 2.0           | ×2        |
| Platinum | 10,000        | 3.0           | ×3        |

### Роли пользователей

| Роль | Доступ |
|---|---|
| `Linella CRM Manager` | Полный доступ ко всем модулям |
| `Linella Sales Rep` | CRM, только свои лиды |
| `Linella Support Agent` | Тикеты поддержки |
| `Linella Marketing` | Акции, промо-кампании |

---

## 📊 Отчёты

| Отчёт | Модуль | Описание |
|---|---|---|
| Lead Pipeline | CRM | Воронка лидов по статусам и суммам |
| Loyalty Overview | Loyalty | Распределение по тирам, RFM, средний чек |
| Support SLA Report | Support | Время ответа, нарушения SLA, оценки |
| Promotion ROI | Promotions | Выручка и ROI каждой акции |

---

## 🤖 AI-функции (GPT-4o)

```python
# Генерация текстов акции для Instagram/TikTok
frappe.call("linella_crm.analytics.linella_ai.generate_promotion_copy",
            promotion_name="PROMO-2025-00001")

# Авто-классификация тикета
frappe.call("linella_crm.analytics.linella_ai.classify_ticket",
            ticket_name="TKT-2025-01-00001")

# Персональные рекомендации клиенту
frappe.call("linella_crm.analytics.linella_ai.get_customer_recommendations",
            card_name="LC-00001")
```

---

## 🔗 Интеграции

- **Telegram Bot** — уведомления и поддержка (см. `linella_bot/`)
- **n8n** — авто-публикация в TikTok/Instagram (см. `linella_n8n_social_media.json`)
- **OpenAI GPT-4o** — генерация контента и классификация
- **Google Wallet** — интеграция Linella Card

---

## 📞 Контакты разработки

- **Компания:** Moldretail Group SRL
- **Email:** it@linella.md
- **Сайт:** https://linella.md
