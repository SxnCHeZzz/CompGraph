import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
import matplotlib.pyplot as plt


def split_channels(image):
    channels = []
    for index in range(3):
        channel = np.zeros_like(image)
        channel[:, :, index] = image[:, :, index]
        channels.append(channel)
    return channels


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Каналы RGB и их гистограммы")
    parser.add_argument("image", nargs="?", type=Path, default=base / "sample.png")
    args = parser.parse_args()
    try:
        with Image.open(args.image) as source:
            image = np.array(ImageOps.exif_transpose(source).convert("RGB"))
    except (OSError, ValueError) as error:
        parser.error(f"Не удалось открыть изображение: {error}")

    result_dir = base / "results" / "task2"
    result_dir.mkdir(parents=True, exist_ok=True)
    channels = split_channels(image)
    figure, plots = plt.subplots(2, 3, figsize=(13, 8))
    for i, (name, color) in enumerate(zip("RGB", ["red", "green", "blue"])):
        Image.fromarray(channels[i]).save(result_dir / f"channel_{name}.png")
        plots[0, i].imshow(channels[i])
        plots[0, i].set_title(f"Канал {name}")
        plots[0, i].axis("off")
        # Считаем только значения выбранного канала.
        counts = np.bincount(image[:, :, i].ravel(), minlength=256)
        plots[1, i].bar(np.arange(256), counts, color=color, width=1)
        plots[1, i].set(title=f"Гистограмма {name}", xlabel="Интенсивность",
                        ylabel="Число пикселей", xlim=(0, 255))

    figure.tight_layout()
    figure.savefig(result_dir / "channels.png", dpi=150)
    print(f"Результаты: {result_dir}")
    plt.show()


if __name__ == "__main__":
    main()
