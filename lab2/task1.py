from pathlib import Path
import argparse

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps


def to_grayscale(rgb):
    pixels = rgb.astype(np.float64)
    gray1 = np.rint(pixels @ [0.299, 0.587, 0.114]).astype(np.uint8)
    gray2 = np.rint(pixels @ [0.2126, 0.7152, 0.0722]).astype(np.uint8)
    # Знаковый тип нужен, чтобы вычитание не переполнялось.
    difference = np.abs(gray1.astype(np.int16) - gray2.astype(np.int16))
    return gray1, gray2, difference.astype(np.uint8)


def main():
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Два способа перевода в оттенки серого")
    parser.add_argument("image", nargs="?", type=Path, default=folder / "sample.png")
    args = parser.parse_args()
    try:
        with Image.open(args.image) as image:
            rgb = np.array(ImageOps.exif_transpose(image).convert("RGB"))
    except (OSError, ValueError) as error:
        parser.error(f"Не удалось открыть изображение: {error}")

    gray1, gray2, difference = to_grayscale(rgb)
    output = folder / "results" / "task1"
    output.mkdir(parents=True, exist_ok=True)
    for name, pixels in [("gray1", gray1), ("gray2", gray2), ("difference", difference)]:
        Image.fromarray(pixels).save(output / f"{name}.png")

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes[0, 0].imshow(rgb)
    axes[0, 0].set_title("Исходное изображение")
    axes[0, 1].imshow(gray1, cmap="gray", vmin=0, vmax=255)
    axes[0, 1].set_title("0.299R + 0.587G + 0.114B")
    axes[0, 2].imshow(gray2, cmap="gray", vmin=0, vmax=255)
    axes[0, 2].set_title("0.2126R + 0.7152G + 0.0722B")
    axes[1, 0].imshow(difference, cmap="gray", vmin=0, vmax=255)
    axes[1, 0].set_title("Абсолютная разность (шкала 0–255)")
    for ax in [*axes[0], axes[1, 0]]:
        ax.axis("off")

    for ax, gray, title in zip(axes[1, 1:], [gray1, gray2], ["Гистограмма 1", "Гистограмма 2"]):
        ax.bar(np.arange(256), np.bincount(gray.ravel(), minlength=256), width=1)
        ax.set(title=title, xlabel="Интенсивность", ylabel="Число пикселей", xlim=(0, 255))
    fig.tight_layout()
    fig.savefig(output / "comparison.png", dpi=150)
    print(f"Результаты: {output}")
    plt.show()


if __name__ == "__main__":
    main()
