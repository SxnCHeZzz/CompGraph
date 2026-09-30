import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk, ImageDraw


def rasterize_triangle(vertices, colors, width=800, height=550):
    image = np.full((height, width, 3), 255, dtype=np.uint8)
    a, b, c = np.asarray(vertices, dtype=float)
    colors = np.asarray(colors, dtype=float)
    denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(denominator) < 1e-10:
        raise ValueError("Вершины лежат на одной прямой. Выберите другой треугольник.")
    left = max(0, int(np.floor(min(a[0], b[0], c[0]))))
    right = min(width - 1, int(np.ceil(max(a[0], b[0], c[0]))))
    top = max(0, int(np.floor(min(a[1], b[1], c[1]))))
    bottom = min(height - 1, int(np.ceil(max(a[1], b[1], c[1]))))
    x = np.arange(left, right + 1)
    # Растеризация по строкам, цвет — по барицентрическим координатам.
    for y in range(top, bottom + 1):
        first = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / denominator
        second = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / denominator
        third = 1 - first - second
        inside = (first >= -1e-10) & (second >= -1e-10) & (third >= -1e-10)
        weights = np.stack([first[inside], second[inside], third[inside]], axis=-1)
        image[y, x[inside]] = np.floor(np.clip(weights @ colors, 0, 255) + 0.5 + 1e-9).astype(np.uint8)
    return Image.fromarray(image)


class App:
    def __init__(self, root):
        root.title("3. Градиентный треугольник")
        self.vertices = []
        self.colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        self.image = Image.new("RGB", (800, 550), "white")
        bar = tk.Frame(root)
        bar.pack()
        self.buttons = []
        for index in range(3):
            button = tk.Button(bar, text=f"Цвет вершины {index + 1}", command=lambda i=index: self.choose(i))
            button.pack(side="left")
            self.buttons.append(button)
        tk.Button(bar, text="Очистить", command=self.clear).pack(side="left")
        tk.Button(bar, text="Сохранить", command=self.save).pack(side="left")
        tk.Label(root, text="Три щелчка задают вершины. Начальные цвета: красный, зелёный, синий.\nСледующий щелчок после готового треугольника начинает новый.").pack()
        self.canvas = tk.Canvas(root, width=800, height=550, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.click)
        self.status = tk.Label(root, text="Выберите вершину 1.")
        self.status.pack()
        self.show()

    def show(self):
        display = self.image.copy()
        if len(self.vertices) < 3:
            draw = ImageDraw.Draw(display)
            for (x, y), color in zip(self.vertices, self.colors):
                draw.ellipse((x-3, y-3, x+3, y+3), fill=color, outline="black")
        self.photo = ImageTk.PhotoImage(display)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        for button, color in zip(self.buttons, self.colors):
            button.config(text=f"Вершина {self.buttons.index(button) + 1}: #{color[0]:02x}{color[1]:02x}{color[2]:02x}")

    def draw(self):
        if len(self.vertices) == 3:
            try:
                self.image = rasterize_triangle(self.vertices, self.colors)
                self.status.config(text="Треугольник готов. Цвета вершин можно изменить.")
            except ValueError as error:
                self.vertices.pop()
                self.status.config(text=str(error))
        self.show()

    def choose(self, index):
        color, _ = colorchooser.askcolor(color=self.colors[index])
        if color:
            color = tuple(round(value) for value in color)
            if any(color == other for i, other in enumerate(self.colors) if i != index):
                messagebox.showinfo("Цвет", "Все три вершины должны иметь разные цвета.")
                return
            self.colors[index] = color
            self.draw()

    def click(self, event):
        if len(self.vertices) == 3:
            self.clear()
        self.vertices.append((max(0, min(799, event.x)), max(0, min(549, event.y))))
        self.status.config(text=f"Выберите вершину {len(self.vertices) + 1}.")
        self.draw()

    def clear(self):
        self.vertices = []
        self.image = Image.new("RGB", (800, 550), "white")
        self.status.config(text="Выберите вершину 1.")
        self.show()

    def save(self):
        if len(self.vertices) != 3:
            messagebox.showinfo("Треугольник", "Сначала задайте три вершины.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            try:
                self.image.save(path)
            except OSError as error:
                messagebox.showerror("Ошибка", str(error))


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
