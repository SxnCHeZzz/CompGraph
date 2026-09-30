import math
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


def bresenham(x0, y0, x1, y1):
    points = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        points.append((x0, y0, 1.0))
        if x0 == x1 and y0 == y1:
            return points
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x0 += sx
        if doubled <= dx:
            error += dx
            y0 += sy


def wu(x0, y0, x1, y1):
    if x0 == x1 and y0 == y1:
        return [(x0, y0, 1.0)]
    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0, x1, y1 = y0, x0, y1, x1
    if x0 > x1:
        x0, x1, y0, y1 = x1, x0, y1, y0
    gradient = (y1 - y0) / (x1 - x0)
    points = []

    def plot(x, y, intensity):
        if intensity > 0:
            points.append((y, x, intensity) if steep else (x, y, intensity))

    # Вклад двух соседних пикселей зависит от дробной части Y.
    for x in range(x0, x1 + 1):
        y = y0 + gradient * (x - x0)
        lower = math.floor(y)
        fraction = y - lower
        weight = 0.5 if x in (x0, x1) else 1.0
        plot(x, lower, (1 - fraction) * weight)
        plot(x, lower + 1, fraction * weight)
    return points


def render(points, size=(360, 360)):
    image = Image.new("RGB", size, "white")
    for x, y, intensity in points:
        if 0 <= x < size[0] and 0 <= y < size[1]:
            shade = round(255 * (1 - max(0, min(1, intensity))))
            image.putpixel((x, y), (shade, shade, shade))
    return image


class App:
    def __init__(self, root):
        root.title("2. Брезенхем и Ву")
        self.start = None
        self.images = [Image.new("RGB", (360, 360), "white") for _ in range(2)]
        self.photos = []
        bar = tk.Frame(root)
        bar.pack()
        tk.Label(bar, text="Два щелчка в любом поле задают концы отрезка. Масштаб:").pack(side="left")
        self.zoom = tk.IntVar(value=1)
        tk.OptionMenu(bar, self.zoom, 1, 2, command=lambda _: self.show()).pack(side="left")
        tk.Button(bar, text="Сохранить", command=self.save).pack(side="left")
        body = tk.Frame(root)
        body.pack()
        self.canvases = []
        for name in ["Брезенхем", "Ву"]:
            frame = tk.Frame(body)
            frame.pack(side="left", padx=5)
            tk.Label(frame, text=name).pack()
            canvas = tk.Canvas(frame, width=360, height=360, highlightthickness=0)
            canvas.pack()
            canvas.bind("<Button-1>", self.click)
            self.canvases.append(canvas)
        self.status = tk.Label(root, text="Выберите начало отрезка.")
        self.status.pack()
        self.show()

    def show(self):
        scale = self.zoom.get()
        self.photos = []
        for canvas, image in zip(self.canvases, self.images):
            photo = ImageTk.PhotoImage(image.resize((360 * scale, 360 * scale), Image.Resampling.NEAREST))
            self.photos.append(photo)
            canvas.config(width=360 * scale, height=360 * scale)
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=photo)
            if self.start is not None:
                x, y = self.start
                canvas.create_oval(x*scale-3, y*scale-3, x*scale+3, y*scale+3, outline="red")

    def click(self, event):
        scale = self.zoom.get()
        point = min(359, event.x // scale), min(359, event.y // scale)
        if self.start is None:
            self.start = point
            self.status.config(text=f"Начало: {point}. Выберите конец.")
        else:
            coordinates = (*self.start, *point)
            self.images = [render(bresenham(*coordinates)), render(wu(*coordinates))]
            self.status.config(text=f"Отрезок: {self.start} → {point}. Можно задать новый.")
            self.start = None
        self.show()

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            result = Image.new("RGB", (720, 360), "white")
            for index, image in enumerate(self.images):
                result.paste(image, (index * 360, 0))
            try:
                result.save(path)
            except OSError as error:
                messagebox.showerror("Ошибка", str(error))


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
