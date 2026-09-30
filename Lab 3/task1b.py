import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
from PIL import Image, ImageDraw, ImageTk
import numpy as np


def scanline_fill(pixels, x, y, paint):
    height, width = pixels.shape[:2]
    if not (0 <= x < width and 0 <= y < height):
        return 0
    target = pixels[y, x].copy()
    visited = np.zeros((height, width), dtype=bool)
    pending = [(x, y)]
    count = 0

    def suitable(px, py):
        return not visited[py, px] and np.array_equal(pixels[py, px], target)

    def fill(px, py, depth):
        nonlocal count
        if not suitable(px, py):
            return
        left = right = px
        while left > 0 and suitable(left - 1, py):
            left -= 1
        while right + 1 < width and suitable(right + 1, py):
            right += 1
        visited[py, left:right + 1] = True
        for column in range(left, right + 1):
            pixels[py, column] = paint(column, py)
        count += right - left + 1
        # Рекурсивно заливаем соседние серии.
        for row in (py - 1, py + 1):
            if not 0 <= row < height:
                continue
            column = left
            while column <= right:
                if suitable(column, row):
                    if depth < 200:
                        fill(column, row, depth + 1)
                    else:
                        # Продолжение длинной области без переполнения стека.
                        pending.append((column, row))
                    column += 1
                    while column <= right and suitable(column, row):
                        column += 1
                else:
                    column += 1

    while pending:
        px, py = pending.pop()
        fill(px, py, 0)
    return count


class App:
    def __init__(self, root):
        self.root = root
        root.title(TITLE)
        self.image = Image.new("RGB", (800, 550), "white")
        self.color = (230, 110, 40)
        self.pattern = None
        self.points = []
        self.mode = tk.StringVar(value="draw")
        bar = tk.Frame(root)
        bar.pack(fill="x")
        tk.Radiobutton(bar, text="Контур", variable=self.mode, value="draw").pack(side="left")
        tk.Radiobutton(bar, text="Заливка", variable=self.mode, value="fill").pack(side="left")
        tk.Button(bar, text=CHOOSE_TEXT, command=self.choose).pack(side="left")
        tk.Button(bar, text="Очистить", command=self.clear).pack(side="left")
        tk.Button(bar, text="Сохранить", command=self.save).pack(side="left")
        tk.Label(root, text=HELP, wraplength=800).pack()
        self.canvas = tk.Canvas(root, width=800, height=550, highlightthickness=0)
        self.canvas.pack()
        self.item = self.canvas.create_image(0, 0, anchor="nw")
        self.status = tk.Label(root, text="Нарисуйте внешний контур и, при необходимости, отверстия внутри.")
        self.status.pack()
        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.refresh()

    def refresh(self):
        self.photo = ImageTk.PhotoImage(self.image)
        self.canvas.itemconfigure(self.item, image=self.photo)

    def position(self, event):
        return max(0, min(799, event.x)), max(0, min(549, event.y))

    def press(self, event):
        point = self.position(event)
        if self.mode.get() == "draw":
            self.points = [point]
        else:
            self.flood(*point)

    def drag(self, event):
        if self.mode.get() == "draw" and self.points:
            point = self.position(event)
            ImageDraw.Draw(self.image).line([self.points[-1], point], fill="black", width=3)
            self.points.append(point)
            self.refresh()

    def release(self, event):
        if self.mode.get() == "draw" and self.points:
            self.drag(event)
            ImageDraw.Draw(self.image).line([self.points[-1], self.points[0]], fill="black", width=3)
            self.points = []
            self.refresh()

    def clear(self):
        self.image = Image.new("RGB", (800, 550), "white")
        self.refresh()

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            try:
                self.image.save(path)
            except OSError as error:
                messagebox.showerror("Ошибка", str(error))

    def choose(self):
        path = filedialog.askopenfilename(filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Все файлы", "*")])
        if path:
            try:
                with Image.open(path) as image:
                    self.pattern = np.array(image.convert("RGB"))
                self.status.config(text=f"Рисунок: {self.pattern.shape[1]} × {self.pattern.shape[0]}, без масштабирования")
            except (OSError, ValueError) as error:
                messagebox.showerror("Ошибка", str(error))

    def flood(self, x, y):
        if self.pattern is None:
            messagebox.showinfo("Рисунок", "Сначала загрузите рисунок для заливки.")
            return
        pixels = np.array(self.image)
        height, width = self.pattern.shape[:2]
        # Начало рисунка совпадает с точкой щелчка, края повторяются.
        count = scanline_fill(pixels, x, y, lambda px, py: self.pattern[(py - y) % height, (px - x) % width])
        self.image = Image.fromarray(pixels)
        self.status.config(text=f"Закрашено пикселей: {count}")
        self.refresh()


TITLE = "1б. Заливка рисунком"
CHOOSE_TEXT = "Загрузить рисунок"
HELP = "Нарисуйте замкнутые контуры, затем выберите «Заливка» и щёлкните внутри. Рисунок начинается в точке щелчка: маленький повторяется, большой обрезается по области. Масштаб не меняется."


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
