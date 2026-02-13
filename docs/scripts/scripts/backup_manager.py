"""
Backup Manager - система управления бекапами блоков

Использование:
    # Создать бекап файла
    python docs/scripts/scripts/backup_manager.py create blocks/ai_integrations/grs_ai_client.py "Working version"
    
    # Создать бекап всего блока (все файлы в папке)
    python docs/scripts/scripts/backup_manager.py create-block blocks/spambot "Spambot block backup"
    
    # Список бекапов
    python docs/scripts/scripts/backup_manager.py list
    
    # Список бекапов конкретного блока
    python docs/scripts/scripts/backup_manager.py list blocks/ai_integrations/grs_ai_client.py
    
    # Восстановить бекап
    python scripts/backup_manager.py restore <backup_id>
    
    # Показать информацию о бекапе
    python scripts/backup_manager.py info <backup_id>
    
    # Сравнить текущую версию с бекапом
    python scripts/backup_manager.py diff <backup_id>
"""

import os
import sys
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class BackupManager:
    """Менеджер бекапов блоков"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Инициализация менеджера
        
        Args:
            project_root: Корневая директория проекта
        """
        if project_root is None:
            # Project root: from docs/scripts/scripts/ go 3 levels up
            _script_dir = Path(__file__).resolve().parent
            project_root = str(_script_dir.parent.parent.parent)
        
        self.project_root = Path(project_root)
        self.backups_dir = self.project_root / "docs" / "backups" / "backups"
        self.metadata_file = self.backups_dir / "metadata.json"
        
        # Создаем директорию для бекапов если её нет
        self.backups_dir.mkdir(exist_ok=True)
        
        # Загружаем метаданные
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Загрузка метаданных бекапов"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"backups": [], "next_id": 1}
    
    def _save_metadata(self):
        """Сохранение метаданных"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def _get_file_hash(self, filepath: Path) -> str:
        """Получение MD5 хеша файла"""
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    
    def _normalize_path(self, filepath: str) -> str:
        """Нормализация пути относительно корня проекта"""
        filepath = Path(filepath)
        
        # Если путь абсолютный, делаем относительным
        if filepath.is_absolute():
            try:
                filepath = filepath.relative_to(self.project_root)
            except ValueError:
                pass
        
        return str(filepath).replace('\\', '/')
    
    def create_backup(self, filepath: str, description: str = "", tags: List[str] = None) -> Dict:
        """
        Создание бекапа файла
        
        Args:
            filepath: Путь к файлу (относительно корня проекта или абсолютный)
            description: Описание бекапа
            tags: Теги для бекапа (например, ["working", "v1.0"])
        
        Returns:
            Информация о созданном бекапе
        """
        # Нормализуем путь
        rel_path = self._normalize_path(filepath)
        source_file = self.project_root / rel_path
        
        if not source_file.exists():
            raise FileNotFoundError(f"Файл не найден: {source_file}")
        
        # Получаем хеш файла
        file_hash = self._get_file_hash(source_file)
        
        # Проверяем, не создан ли уже бекап с таким же хешем
        for backup in self.metadata["backups"]:
            if backup["file_path"] == rel_path and backup["file_hash"] == file_hash:
                print(f"[!] Бекап с таким же содержимым уже существует: {backup['backup_id']}")
                return backup
        
        # Генерируем ID бекапа
        backup_id = f"backup_{self.metadata['next_id']:04d}"
        self.metadata['next_id'] += 1
        
        # Создаем директорию для бекапа
        backup_dir = self.backups_dir / backup_id
        backup_dir.mkdir(exist_ok=True)
        
        # Копируем файл
        backup_file = backup_dir / source_file.name
        shutil.copy2(source_file, backup_file)
        
        # Получаем размер файла
        file_size = source_file.stat().st_size
        
        # Создаем метаданные бекапа
        backup_info = {
            "backup_id": backup_id,
            "file_path": rel_path,
            "file_name": source_file.name,
            "file_hash": file_hash,
            "file_size": file_size,
            "description": description,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "backup_file": str(backup_file.relative_to(self.project_root)).replace('\\', '/')
        }
        
        # Сохраняем метаданные бекапа в отдельный файл
        backup_meta_file = backup_dir / "metadata.json"
        with open(backup_meta_file, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
        
        # Добавляем в общие метаданные
        self.metadata["backups"].append(backup_info)
        self._save_metadata()
        
        return backup_info
    
    def create_block_backup(self, block_path: str, description: str = "", tags: List[str] = None) -> List[Dict]:
        """
        Создание бекапов всех файлов в блоке (директории).
        
        Args:
            block_path: Путь к блоку (например blocks/spambot)
            description: Описание бекапа (добавится к каждому файлу)
            tags: Теги (например ["spambot", "block"])
        
        Returns:
            Список созданных бекапов
        """
        rel_path = self._normalize_path(block_path)
        block_dir = self.project_root / rel_path
        if not block_dir.is_dir():
            raise FileNotFoundError(f"Директория не найдена: {block_dir}")
        tags = list(tags or [])
        if rel_path.split("/")[-1] not in tags:
            tags.append(rel_path.split("/")[-1])
        if "block" not in tags:
            tags.append("block")
        created = []
        for f in sorted(block_dir.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                file_rel = (block_dir / f.name).relative_to(self.project_root)
                file_rel_str = str(file_rel).replace("\\", "/")
                try:
                    backup = self.create_backup(file_rel_str, description or f"Block backup: {rel_path}", tags)
                    created.append(backup)
                except Exception as e:
                    print(f"[!] Пропуск {f.name}: {e}")
        return created
    
    def list_backups(self, filepath: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict]:
        """
        Список бекапов
        
        Args:
            filepath: Фильтр по пути к файлу
            tags: Фильтр по тегам
        
        Returns:
            Список бекапов
        """
        backups = self.metadata["backups"]
        
        # Фильтр по файлу
        if filepath:
            rel_path = self._normalize_path(filepath)
            backups = [b for b in backups if b["file_path"] == rel_path]
        
        # Фильтр по тегам
        if tags:
            backups = [b for b in backups if any(tag in b.get("tags", []) for tag in tags)]
        
        # Сортируем по дате создания (новые сверху)
        backups = sorted(backups, key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    def get_backup(self, backup_id: str) -> Optional[Dict]:
        """
        Получение информации о бекапе
        
        Args:
            backup_id: ID бекапа
        
        Returns:
            Информация о бекапе или None
        """
        for backup in self.metadata["backups"]:
            if backup["backup_id"] == backup_id:
                return backup
        return None
    
    def restore_backup(self, backup_id: str, create_backup_before: bool = True) -> bool:
        """
        Восстановление бекапа
        
        Args:
            backup_id: ID бекапа
            create_backup_before: Создать бекап текущей версии перед восстановлением
        
        Returns:
            True если успешно
        """
        backup = self.get_backup(backup_id)
        if not backup:
            raise ValueError(f"Бекап не найден: {backup_id}")
        
        source_file = self.project_root / backup["backup_file"]
        target_file = self.project_root / backup["file_path"]
        
        if not source_file.exists():
            raise FileNotFoundError(f"Файл бекапа не найден: {source_file}")
        
        # Создаем бекап текущей версии
        if create_backup_before and target_file.exists():
            try:
                self.create_backup(
                    str(target_file),
                    description=f"Автобекап перед восстановлением {backup_id}",
                    tags=["auto-backup", "before-restore"]
                )
            except Exception as e:
                print(f"[!] Не удалось создать автобекап: {e}")
        
        # Восстанавливаем файл
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)
        
        return True
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Удаление бекапа
        
        Args:
            backup_id: ID бекапа
        
        Returns:
            True если успешно
        """
        backup = self.get_backup(backup_id)
        if not backup:
            raise ValueError(f"Бекап не найден: {backup_id}")
        
        # Удаляем директорию бекапа
        backup_dir = self.backups_dir / backup_id
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        # Удаляем из метаданных
        self.metadata["backups"] = [b for b in self.metadata["backups"] if b["backup_id"] != backup_id]
        self._save_metadata()
        
        return True
    
    def compare_with_current(self, backup_id: str) -> Dict:
        """
        Сравнение бекапа с текущей версией файла
        
        Args:
            backup_id: ID бекапа
        
        Returns:
            Информация о различиях
        """
        backup = self.get_backup(backup_id)
        if not backup:
            raise ValueError(f"Бекап не найден: {backup_id}")
        
        backup_file = self.project_root / backup["backup_file"]
        current_file = self.project_root / backup["file_path"]
        
        if not current_file.exists():
            return {
                "status": "file_deleted",
                "message": "Текущий файл не существует"
            }
        
        # Сравниваем хеши
        current_hash = self._get_file_hash(current_file)
        backup_hash = backup["file_hash"]
        
        if current_hash == backup_hash:
            return {
                "status": "identical",
                "message": "Файлы идентичны"
            }
        
        # Читаем содержимое для сравнения
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_content = f.readlines()
        
        with open(current_file, 'r', encoding='utf-8') as f:
            current_content = f.readlines()
        
        return {
            "status": "different",
            "message": "Файлы различаются",
            "backup_lines": len(backup_content),
            "current_lines": len(current_content),
            "backup_hash": backup_hash,
            "current_hash": current_hash
        }


def format_size(size_bytes: int) -> str:
    """Форматирование размера файла"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_datetime(iso_string: str) -> str:
    """Форматирование даты и времени"""
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Основная функция CLI"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    manager = BackupManager()
    
    try:
        if command == "create":
            # Создание бекапа
            if len(sys.argv) < 3:
                print("Использование: backup_manager.py create <filepath> [description] [--tags tag1,tag2]")
                return
            
            filepath = sys.argv[2]
            description = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else ""
            
            # Парсим теги
            tags = []
            if '--tags' in sys.argv:
                tags_idx = sys.argv.index('--tags')
                if tags_idx + 1 < len(sys.argv):
                    tags = sys.argv[tags_idx + 1].split(',')
            
            backup = manager.create_backup(filepath, description, tags)
            
            print(f"[OK] Бекап создан: {backup['backup_id']}")
            print(f"   Файл: {backup['file_path']}")
            print(f"   Размер: {format_size(backup['file_size'])}")
            print(f"   Описание: {backup['description']}")
            if backup['tags']:
                print(f"   Теги: {', '.join(backup['tags'])}")
        
        elif command == "create-block":
            if len(sys.argv) < 3:
                print("Использование: backup_manager.py create-block <blocks/block_name> [description] [--tags tag1,tag2]")
                return
            block_path = sys.argv[2]
            description = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else ""
            tags = []
            if '--tags' in sys.argv:
                tags_idx = sys.argv.index('--tags')
                if tags_idx + 1 < len(sys.argv):
                    tags = sys.argv[tags_idx + 1].split(',')
            created = manager.create_block_backup(block_path, description, tags)
            print(f"[OK] Бекап блока создан: {len(created)} файлов")
            for b in created:
                print(f"   {b['backup_id']} — {b['file_path']}")
        
        elif command == "list":
            # Список бекапов
            filepath = sys.argv[2] if len(sys.argv) > 2 else None
            backups = manager.list_backups(filepath)
            
            if not backups:
                print("Бекапов не найдено")
                return
            
            print(f"\n{'ID':<15} {'Файл':<40} {'Дата':<20} {'Размер':<10} {'Описание'}")
            print("=" * 120)
            
            for backup in backups:
                print(f"{backup['backup_id']:<15} "
                      f"{backup['file_path']:<40} "
                      f"{format_datetime(backup['created_at']):<20} "
                      f"{format_size(backup['file_size']):<10} "
                      f"{backup['description'][:30]}")
            
            print(f"\nВсего бекапов: {len(backups)}")
        
        elif command == "info":
            # Информация о бекапе
            if len(sys.argv) < 3:
                print("Использование: backup_manager.py info <backup_id>")
                return
            
            backup_id = sys.argv[2]
            backup = manager.get_backup(backup_id)
            
            if not backup:
                print(f"[X] Бекап не найден: {backup_id}")
                return
            
            print(f"\n[Backup] {backup['backup_id']}")
            print(f"   Файл: {backup['file_path']}")
            print(f"   Имя файла: {backup['file_name']}")
            print(f"   Размер: {format_size(backup['file_size'])}")
            print(f"   Хеш: {backup['file_hash']}")
            print(f"   Создан: {format_datetime(backup['created_at'])}")
            print(f"   Описание: {backup['description']}")
            if backup['tags']:
                print(f"   Теги: {', '.join(backup['tags'])}")
            print(f"   Путь к бекапу: {backup['backup_file']}")
        
        elif command == "restore":
            # Восстановление бекапа
            if len(sys.argv) < 3:
                print("Использование: backup_manager.py restore <backup_id>")
                return
            
            backup_id = sys.argv[2]
            backup = manager.get_backup(backup_id)
            
            if not backup:
                print(f"[X] Бекап не найден: {backup_id}")
                return
            
            print(f"[!] Восстановление бекапа: {backup_id}")
            print(f"   Файл: {backup['file_path']}")
            print(f"   Описание: {backup['description']}")
            
            response = input("\nПродолжить? (y/n): ")
            if response.lower() != 'y':
                print("Отменено")
                return
            
            manager.restore_backup(backup_id)
            print(f"[OK] Бекап восстановлен: {backup['file_path']}")
        
        elif command == "diff":
            # Сравнение с текущей версией
            if len(sys.argv) < 3:
                print("Использование: backup_manager.py diff <backup_id>")
                return
            
            backup_id = sys.argv[2]
            result = manager.compare_with_current(backup_id)
            
            print(f"\n[Diff] Сравнение бекапа {backup_id} с текущей версией:")
            print(f"   Статус: {result['status']}")
            print(f"   {result['message']}")
            
            if result['status'] == 'different':
                print(f"   Строк в бекапе: {result['backup_lines']}")
                print(f"   Строк в текущей версии: {result['current_lines']}")
                print(f"   Хеш бекапа: {result['backup_hash']}")
                print(f"   Хеш текущей версии: {result['current_hash']}")
        
        elif command == "delete":
            # Удаление бекапа
            if len(sys.argv) < 3:
                print("Использование: backup_manager.py delete <backup_id>")
                return
            
            backup_id = sys.argv[2]
            backup = manager.get_backup(backup_id)
            
            if not backup:
                print(f"[X] Бекап не найден: {backup_id}")
                return
            
            print(f"[!] Удаление бекапа: {backup_id}")
            print(f"   Файл: {backup['file_path']}")
            
            response = input("\nПродолжить? (y/n): ")
            if response.lower() != 'y':
                print("Отменено")
                return
            
            manager.delete_backup(backup_id)
            print(f"[OK] Бекап удален: {backup_id}")
        
        else:
            print(f"[X] Неизвестная команда: {command}")
            print(__doc__)
    
    except Exception as e:
        print(f"[X] Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
