"""Prepara la portada a partir de una imagen: arte ASCII a color y un fondo tenue.

Solo hay que ejecutarlo cuando cambie la imagen (requiere Pillow):
    python scripts/portrait.py ruta/a/imagen
Genera data/portrait.json y assets/br2049/cover.jpg.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 872, 420  # tamaño de la imagen dentro de la portada
COLS, ROWS = 176, 55
TOP = 0.55  # al recortar en vertical: 0 conserva la parte superior, 1 la inferior
RAMP = " .:-=+*#%@"


def crop(img):
    """Recorta a la proporción de la portada sin deformar la imagen."""
    ratio = WIDTH / HEIGHT
    w, h = img.size
    if w / h > ratio:
        new = round(h * ratio)
        left = (w - new) // 2
        return img.crop((left, 0, left + new, h))
    new = round(w / ratio)
    top = round((h - new) * TOP)
    return img.crop((0, top, w, top + new))


def ascii_rows(img):
    img = ImageEnhance.Contrast(img).enhance(1.2)
    # realce local: recupera las siluetas entre la neblina
    img = img.filter(ImageFilter.UnsharpMask(radius=6, percent=160, threshold=0))
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    rows = []
    for y in range(ROWS):
        runs = []  # [color, texto] agrupando caracteres del mismo color
        for x in range(COLS):
            r, g, b = img.getpixel((x, y))
            level = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            char = RAMP[max(1, min(int(level ** 0.9 * len(RAMP)), len(RAMP) - 1))]
            gain = min(255 / max(r, g, b, 1), 1.6)
            color = "#" + "".join(f"{min(int(c * gain) // 24 * 24 + 12, 255):02x}" for c in (r, g, b))
            if runs and runs[-1][0] == color:
                runs[-1][1] += char
            else:
                runs.append([color, char])
        rows.append(runs)
    return rows


def main(source):
    img = crop(Image.open(source).convert("RGB"))
    data = ROOT / "data" / "portrait.json"
    data.parent.mkdir(exist_ok=True)
    data.write_text(json.dumps(ascii_rows(img), separators=(",", ":")), encoding="utf-8")
    img.resize((WIDTH, HEIGHT), Image.LANCZOS).save(ROOT / "assets" / "br2049" / "cover.jpg", quality=82)


if __name__ == "__main__":
    main(sys.argv[1])
