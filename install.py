"""
Скрипт установки Linella CRM.
Запускается командой: bench --site mysite install-app linella_crm
"""
import frappe


def after_install():
    """Выполняется после установки приложения."""
    _create_roles()
    _create_default_settings()
    _load_fixtures()
    frappe.db.commit()
    print("✅ Linella CRM успешно установлен!")


def _create_roles():
    """Создаёт роли пользователей Linella CRM."""
    roles = [
        {"role_name": "Linella CRM Manager",  "desk_access": 1},
        {"role_name": "Linella Sales Rep",     "desk_access": 1},
        {"role_name": "Linella Support Agent", "desk_access": 1},
        {"role_name": "Linella Marketing",     "desk_access": 1},
    ]
    for role_def in roles:
        if not frappe.db.exists("Role", role_def["role_name"]):
            role = frappe.get_doc({"doctype": "Role", **role_def})
            role.insert(ignore_permissions=True)
            print(f"  ✔ Роль создана: {role_def['role_name']}")
        else:
            print(f"  — Роль уже существует: {role_def['role_name']}")


def _create_default_settings():
    """Создаёт запись настроек если не существует."""
    # Здесь можно добавить Single DocType настроек
    pass


def _load_fixtures():
    """Загружает начальные данные (тиры лояльности, сегменты)."""
    import json
    import os

    fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "fixtures")
    if not os.path.exists(fixtures_dir):
        return

    for filename in sorted(os.listdir(fixtures_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(fixtures_dir, filename)
        with open(filepath, encoding="utf-8") as f:
            records = json.load(f)
        for record in records:
            dt = record.get("doctype")
            name = record.get("tier_name") or record.get("segment_name") or record.get("name")
            if dt and name and not frappe.db.exists(dt, name):
                doc = frappe.get_doc(record)
                doc.insert(ignore_permissions=True)
                print(f"  ✔ {dt}: {name}")


def before_uninstall():
    """Предупреждение перед удалением."""
    print("⚠️  Удаление Linella CRM. Все данные будут сохранены в БД.")
