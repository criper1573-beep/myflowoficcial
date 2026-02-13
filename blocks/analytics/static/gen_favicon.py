# -*- coding: utf-8 -*-
"""Скрипт генерации favicon.png (буква F, синий). Запуск: python gen_favicon.py"""
try:
    from PIL import Image, ImageDraw
except ImportError:
    import sys
    sys.exit("Нужен Pillow: pip install pillow")

W, H = 64, 64
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
# Синий (#3b82f6)
blue = (59, 130, 246, 255)
margin = 10
thick = 7
# Вертикальная полоса F
d.rectangle([margin, margin, margin + thick, H - margin], fill=blue)
# Верхняя горизонтальная
d.rectangle([margin, margin, W - margin, margin + thick], fill=blue)
# Средняя горизонтальная
d.rectangle([margin, margin + 22, margin + 28, margin + 22 + thick], fill=blue)
import sys
out = (sys.argv[1] if len(sys.argv) > 1 else
       str(__file__).replace("gen_favicon.py", "favicon.png"))
img.resize((32, 32), Image.Resampling.LANCZOS).save(out, "PNG")
print("Saved:", out)
