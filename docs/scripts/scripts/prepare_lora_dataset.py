#!/usr/bin/env python3
"""
Подготовка датасета для обучения LoRA (лицо/персонаж).

- Берёт папку с фотографиями
- Приводит к 1024x1024 (crop center или resize с сохранением пропорций)
- Сохраняет в выходную папку и создаёт ZIP для Replicate

Зависимость: Pillow (pip install Pillow)
Запуск из корня проекта:
  python docs/scripts/scripts/prepare_lora_dataset.py --input ./my_photos --output ./lora_dataset
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Установите Pillow: pip install Pillow")

# Расширения изображений
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
# Целевой размер для FLUX / fast-flux-trainer
TARGET_SIZE = 1024


def resize_and_crop(img: Image.Image, size: int = TARGET_SIZE) -> Image.Image:
    """Привести к size x size: вписать по длинной стороне и обрезать по центру."""
    w, h = img.size
    if w == h and w == size:
        return img
    scale = size / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    # Center crop до size x size
    left = (new_w - size) // 2
    top = (new_h - size) // 2
    return img.crop((left, top, left + size, top + size))


def collect_images(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXT
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Подготовка фото для LoRA: resize 1024x1024 + ZIP"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Папка с исходными фотографиями",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("lora_dataset"),
        help="Папка для обработанных фото (по умолчанию lora_dataset)",
    )
    parser.add_argument(
        "--zip", "-z",
        type=Path,
        default=None,
        help="Путь к создаваемому ZIP (по умолчанию <output>/lora_dataset.zip)",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Не создавать ZIP, только сохранить изображения",
    )
    args = parser.parse_args()

    inp = args.input.resolve()
    out = args.output.resolve()

    if not inp.is_dir():
        raise SystemExit(f"Папка не найдена: {inp}")

    images = collect_images(inp)
    if not images:
        raise SystemExit(f"В папке {inp} нет изображений (.jpg, .png, .webp)")

    out.mkdir(parents=True, exist_ok=True)

    for i, path in enumerate(images):
        with Image.open(path) as img:
            img = img.convert("RGB")
            img = resize_and_crop(img, TARGET_SIZE)
            out_name = out / f"img_{i:04d}.jpg"
            img.save(out_name, "JPEG", quality=95)
    print(f"Обработано {len(images)} изображений → {out}")

    if args.no_zip:
        return

    zip_path = args.zip or (out / "lora_dataset.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(out.glob("*.jpg")):
            zf.write(f, f.name)
    print(f"ZIP создан: {zip_path}")


if __name__ == "__main__":
    main()
