# -*- coding: utf-8 -*-
"""
One-time migration: rename Russian-named folders and files to Latin.
Run from project root: python docs/scripts/migrate_to_latin.py
"""
import os
from pathlib import Path

# Project root (parent of docs/)
ROOT = Path(__file__).resolve().parent.parent.parent

# Order: rename from deepest to top-level so paths stay valid
RENAMES = [
    # blocks subtree
    ("Блоки/проекты/данные", "Блоки/проекты/data"),
    ("Блоки/проекты/загрузчик.py", "Блоки/проекты/loader.py"),
    ("Блоки/проекты", "Блоки/projects"),
    ("Блоки/интеграции_ии", "Блоки/ai_integrations"),
    ("Блоки/спамбот", "Блоки/spambot"),
    ("Блоки", "blocks"),
    # docs subtree
    ("Документация/Архитектура", "Документация/architecture"),
    ("Документация/Бекапы", "Документация/backups"),
    ("Документация/Конфигурация", "Документация/config"),
    ("Документация/Правила и стандарты", "Документация/rules"),
    ("Документация/Руководства/МУЛЬТИПРОЕКТНОСТЬ.md", "Документация/Руководства/MULTIPROJECT.md"),
    ("Документация/Руководства", "Документация/guides"),
    ("Документация/Скрипты", "Документация/scripts"),
    ("Документация", "docs"),
]


def main():
    os.chdir(ROOT)
    for old_rel, new_rel in RENAMES:
        old_path = ROOT / old_rel
        new_path = ROOT / new_rel
        if not old_path.exists():
            print("Skip (not found):", old_rel)
            continue
        if new_path.exists():
            print("Skip (target exists):", new_rel)
            continue
        try:
            old_path.rename(new_path)
            print("OK:", old_rel, "->", new_rel)
        except Exception as e:
            print("FAIL:", old_rel, "-", e)
    print("Done. Update imports and paths in code/docs next.")


if __name__ == "__main__":
    main()
