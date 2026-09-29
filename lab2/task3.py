from pathlib import Path
import argparse

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from PIL import Image, ImageOps


def rgb_to_hsv(rgb):
    rgb = rgb.astype(np.float64) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maximum = rgb.max(axis=-1)
    minimum = rgb.min(axis=-1)
    delta = maximum - minimum
    hue = np.zeros_like(maximum)
    saturation = np.zeros_like(maximum)
    colored = delta > 0

    red = colored & (maximum == r)
    green = colored & ~red & (maximum == g)
    blue = colored & ~red & ~green
    hue[red] = ((g[red] - b[red]) / delta[red]) % 6
    hue[green] = (b[green] - r[green]) / delta[green] + 2
    hue[blue] = (r[blue] - g[blue]) / delta[blue] + 4
    hue *= 60
    np.divide(delta, maximum, out=saturation, where=maximum > 0)
    return np.stack([hue, saturation, maximum], axis=-1)


def hsv_to_rgb(hsv):
    hue = (hsv[..., 0] % 360) / 60
    saturation = np.clip(hsv[..., 1], 0, 1)
    value = np.clip(hsv[..., 2], 0, 1)
    chroma = value * saturation
    x = chroma * (1 - np.abs(hue % 2 - 1))
    zero = np.zeros_like(chroma)
    rgb = np.zeros(hsv.shape, dtype=np.float64)
    sectors = [(chroma, x, zero), (x, chroma, zero), (zero, chroma, x),
               (zero, x, chroma), (x, zero, chroma), (chroma, zero, x)]
    for index, components in enumerate(sectors):
        mask = np.floor(hue).astype(int) == index
        rgb[mask] = np.stack(components, axis=-1)[mask]
    rgb += (value - chroma)[..., None]
    return np.rint(np.clip(rgb, 0, 1) * 255).astype(np.uint8)


def adjust_hsv(original, hue_shift, saturation_shift, value_shift):
    adjusted = original.copy()
    adjusted[..., 0] = (adjusted[..., 0] + hue_shift) % 360
    adjusted[..., 1] = np.clip(adjusted[..., 1] + saturation_shift, 0, 1)
    adjusted[..., 2] = np.clip(adjusted[..., 2] + value_shift, 0, 1)
    return hsv_to_rgb(adjusted)


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Редактор HSV")
    parser.add_argument("image", nargs="?", type=Path, default=base / "sample.png")
    parser.add_argument("--output", type=Path, default=base / "results" / "task3" / "edited.png")
    args = parser.parse_args()
    try:
        with Image.open(args.image) as image:
            original = np.array(ImageOps.exif_transpose(image).convert("RGB"))
    except (OSError, ValueError) as error:
        parser.error(f"Не удалось открыть изображение: {error}")

    hsv = rgb_to_hsv(original)
    result = original.copy()
    fig, axes = plt.subplots(1, 2, figsize=(12, 7))
    fig.subplots_adjust(bottom=0.32)
    axes[0].imshow(original)
    axes[0].set_title("Оригинал")
    preview = axes[1].imshow(result)
    axes[1].set_title("Результат HSV → RGB")
    for ax in axes:
        ax.axis("off")

    hue = Slider(fig.add_axes([0.23, 0.23, 0.6, 0.025]), "Оттенок, °", -180, 180, valinit=0)
    saturation = Slider(fig.add_axes([0.23, 0.18, 0.6, 0.025]), "Насыщенность Δ", -1, 1, valinit=0)
    value = Slider(fig.add_axes([0.23, 0.13, 0.6, 0.025]), "Яркость Δ", -1, 1, valinit=0)
    save_button = Button(fig.add_axes([0.57, 0.04, 0.2, 0.045]), "Сохранить")
    reset_button = Button(fig.add_axes([0.25, 0.04, 0.2, 0.045]), "Сбросить")
    status = fig.text(0.5, 0.005, "", ha="center", fontsize=9)

    def update(_):
        nonlocal result
        # Каждый раз изменяем исходный HSV, чтобы не копить погрешность.
        result = adjust_hsv(hsv, hue.val, saturation.val, value.val)
        preview.set_data(result)
        status.set_text("")
        fig.canvas.draw_idle()

    def save(_):
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(result).save(args.output)
            status.set_text(f"Сохранено: {args.output.name}")
            print(f"Сохранено: {args.output.resolve()}")
        except (OSError, ValueError) as error:
            status.set_text(f"Ошибка сохранения: {error}")
        fig.canvas.draw_idle()

    def reset(_):
        for slider in [hue, saturation, value]:
            slider.reset()

    for slider in [hue, saturation, value]:
        slider.on_changed(update)
    save_button.on_clicked(save)
    reset_button.on_clicked(reset)
    plt.show()


if __name__ == "__main__":
    main()
