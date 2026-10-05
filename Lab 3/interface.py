import argparse
import sys
import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
from PIL import Image, ImageDraw, ImageTk
import numpy as np

import task1a
import task1b
import task1v
import task2
import task3


ERROR_MESSAGES = {
    'point_on_boundary': 'Щёлкните внутри области, не на её границе.',
    'open_region': 'Контур не замкнут. Проверьте цвет границы или увеличьте допуск и щёлкните снова.',
    'disconnected_boundary': 'Граница должна быть замкнутой и 8-связной.',
    'boundary_cycle': 'Не удалось замкнуть обход. Проверьте форму границы.',
    'degenerate_triangle': 'Вершины лежат на одной прямой. Выберите другой треугольник.',
}


def run_fill(algorithm, *args):
    previous_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(max(previous_limit, 10000))
        return algorithm(*args)
    finally:
        sys.setrecursionlimit(previous_limit)


def render_line(points, size=(360, 360)):
    image = Image.new("RGB", size, "white")
    for x, y, intensity in points:
        if 0 <= x < size[0] and 0 <= y < size[1]:
            shade = round(255 * (1 - max(0, min(1, intensity))))
            image.putpixel((x, y), (shade, shade, shade))
    return image


class ColorFillApp:
    def __init__(self, root):
        self.root = root
        root.title('1а. Заливка цветом')
        self.image = Image.new("RGB", (800, 550), "white")
        self.boundary = Image.new("1", (800, 550), 0)
        self.color = (230, 110, 40)
        self.points = []
        self.mode = tk.StringVar(value="draw")
        bar = tk.Frame(root)
        bar.pack(fill="x")
        tk.Radiobutton(bar, text="Контур", variable=self.mode, value="draw").pack(side="left")
        tk.Radiobutton(bar, text="Заливка", variable=self.mode, value="fill").pack(side="left")
        tk.Button(bar, text='Выбрать цвет', command=self.choose).pack(side="left")
        tk.Button(bar, text="Очистить", command=self.clear).pack(side="left")
        tk.Button(bar, text="Сохранить", command=self.save).pack(side="left")
        tk.Label(root, text='В режиме «Контур» рисуйте левой кнопкой: при отпускании контур замыкается. В режиме «Заливка» щёлкните внутри области.', wraplength=800).pack()
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
            ImageDraw.Draw(self.boundary).line([self.points[-1], point], fill=1, width=3)
            self.points.append(point)
            self.refresh()

    def release(self, event):
        if self.mode.get() == "draw" and self.points:
            self.drag(event)
            ImageDraw.Draw(self.image).line([self.points[-1], self.points[0]], fill="black", width=3)
            ImageDraw.Draw(self.boundary).line([self.points[-1], self.points[0]], fill=1, width=3)
            self.points = []
            self.refresh()

    def clear(self):
        self.image = Image.new("RGB", (800, 550), "white")
        self.boundary = Image.new("1", (800, 550), 0)
        self.refresh()

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            try:
                self.image.save(path)
            except OSError as error:
                messagebox.showerror("Ошибка", str(error))

    def choose(self):
        color, _ = colorchooser.askcolor()
        if color:
            self.color = tuple(round(value) for value in color)

    def flood(self, x, y):
        if self.boundary.getpixel((x, y)):
            self.status.config(text="Выберите точку внутри области, а не на границе.")
            return
        pixels = np.array(self.image)
        try:
            count = run_fill(task1a.fill_color, pixels, x, y, self.color, np.array(self.boundary))
        except RecursionError:
            messagebox.showerror("Заливка", "Слишком сложная область для рекурсивной заливки. Изображение не изменено.")
            return
        self.image = Image.fromarray(pixels)
        self.status.config(text=f"Закрашено пикселей: {count}")
        self.refresh()


class PatternFillApp:
    def __init__(self, root):
        self.root = root
        root.title('1б. Заливка рисунком')
        self.image = Image.new("RGB", (800, 550), "white")
        self.boundary = Image.new("1", (800, 550), 0)
        self.pattern = None
        self.points = []
        self.mode = tk.StringVar(value="draw")
        bar = tk.Frame(root)
        bar.pack(fill="x")
        tk.Radiobutton(bar, text="Контур", variable=self.mode, value="draw").pack(side="left")
        tk.Radiobutton(bar, text="Заливка", variable=self.mode, value="fill").pack(side="left")
        tk.Button(bar, text='Загрузить рисунок', command=self.choose).pack(side="left")
        tk.Button(bar, text="Очистить", command=self.clear).pack(side="left")
        tk.Button(bar, text="Сохранить", command=self.save).pack(side="left")
        tk.Label(root, text='Нарисуйте замкнутые контуры, затем выберите «Заливка» и щёлкните внутри. Рисунок начинается в точке щелчка: маленький повторяется, большой обрезается по области. Масштаб не меняется.', wraplength=800).pack()
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
            ImageDraw.Draw(self.boundary).line([self.points[-1], point], fill=1, width=3)
            self.points.append(point)
            self.refresh()

    def release(self, event):
        if self.mode.get() == "draw" and self.points:
            self.drag(event)
            ImageDraw.Draw(self.image).line([self.points[-1], self.points[0]], fill="black", width=3)
            ImageDraw.Draw(self.boundary).line([self.points[-1], self.points[0]], fill=1, width=3)
            self.points = []
            self.refresh()

    def clear(self):
        self.image = Image.new("RGB", (800, 550), "white")
        self.boundary = Image.new("1", (800, 550), 0)
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
        if self.boundary.getpixel((x, y)):
            self.status.config(text="Выберите точку внутри области, а не на границе.")
            return
        pixels = np.array(self.image)
        try:
            count = run_fill(task1b.fill_pattern, pixels, x, y, self.pattern, np.array(self.boundary))
        except RecursionError:
            messagebox.showerror("Заливка", "Слишком сложная область для рекурсивной заливки. Изображение не изменено.")
            return
        self.image = Image.fromarray(pixels)
        self.status.config(text=f"Закрашено пикселей: {count}")
        self.refresh()


class BoundaryApp:
    def __init__(self, root):
        root.title("1в. Обход границы")
        self.original = None
        self.result = None
        self.contour = []
        self.boundary_color = (0, 0, 0)
        self.tolerance = tk.IntVar(master=root, value=80)
        bar = tk.Frame(root)
        bar.pack(fill="x")
        tk.Button(bar, text="Открыть изображение", command=self.load).pack(side="left")
        tk.Button(bar, text="Цвет границы", command=self.choose_color).pack(side="left")
        tk.Button(bar, text="Сохранить результат", command=self.save).pack(side="left")
        settings = tk.Frame(root)
        settings.pack(fill="x")
        tk.Label(settings, text="Допуск цвета границы:").pack(side="left", padx=5)
        tk.Scale(settings, from_=0, to=200, orient="horizontal", variable=self.tolerance,
                 length=240).pack(side="left")
        tk.Label(settings, text="0 — точное совпадение. После изменения щёлкните по области снова.").pack(side="left", padx=10)
        tk.Label(root, text="Выберите цвет границы (по умолчанию чёрный), затем щёлкните ВНУТРИ замкнутой области.\nПрограмма выделяет контур цветом. Для сглаженных линий и JPEG используйте допуск, например 80.").pack()
        frame = tk.Frame(root)
        frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(frame, width=800, height=550, background="gray")
        horizontal = tk.Scrollbar(frame, orient="horizontal", command=self.canvas.xview)
        vertical = tk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        horizontal.pack(side="bottom", fill="x")
        vertical.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)
        self.item = self.canvas.create_image(0, 0, anchor="nw")
        self.canvas.bind("<Button-1>", self.select)
        self.status = tk.Label(root, text="Загрузите изображение. Масштаб 1:1, доступны полосы прокрутки.")
        self.status.pack()

    def show(self):
        self.photo = ImageTk.PhotoImage(self.result)
        self.canvas.itemconfigure(self.item, image=self.photo)
        self.canvas.config(scrollregion=(0, 0, *self.result.size))

    def load(self):
        path = filedialog.askopenfilename()
        if path:
            try:
                with Image.open(path) as image:
                    self.original = image.convert("RGB")
                self.result = self.original.copy()
                self.contour = []
                self.show()
            except (OSError, ValueError) as error:
                messagebox.showerror("Ошибка", str(error))

    def choose_color(self):
        color, _ = colorchooser.askcolor(color=self.boundary_color)
        if color:
            self.boundary_color = tuple(round(value) for value in color)
            self.status.config(text=f"Цвет границы: {self.boundary_color}. Выберите область.")

    def select(self, event):
        if self.original is None:
            return
        x, y = int(self.canvas.canvasx(event.x)), int(self.canvas.canvasy(event.y))
        try:
            contour = task1v.trace_boundary(np.array(self.original), x, y, self.boundary_color, self.tolerance.get())
        except ValueError as error:
            self.status.config(text=ERROR_MESSAGES.get(str(error), str(error)))
            return
        self.contour = contour
        self.result = self.original.copy()
        draw = ImageDraw.Draw(self.result)
        highlight = "red"
        if self.contour:
            color = self.original.getpixel(self.contour[0])
            if color[0] > 180 and color[1] < 100 and color[2] < 100:
                highlight = "cyan"
        for point in self.contour:
            draw.point(point, fill=highlight)
        self.status.config(text=f"Точек в порядке обхода: {len(self.contour)}")
        self.show()

    def save(self):
        if not self.contour:
            messagebox.showinfo("Граница", "Сначала выделите границу.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            try:
                self.result.save(path)
                with open(path + ".txt", "w", encoding="utf-8") as file:
                    file.write("\n".join(f"{x} {y}" for x, y in self.contour))
            except OSError as error:
                messagebox.showerror("Ошибка", str(error))


class LinesApp:
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
            self.images = [render_line(task2.bresenham(*coordinates)), render_line(task2.wu(*coordinates))]
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


class TriangleApp:
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
                self.image = Image.fromarray(task3.rasterize_triangle(self.vertices, self.colors))
                self.status.config(text="Треугольник готов. Цвета вершин можно изменить.")
            except ValueError as error:
                self.vertices.pop()
                self.status.config(text=ERROR_MESSAGES.get(str(error), str(error)))
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

TASKS = {
    "1a": ("1а. Заливка цветом", ColorFillApp),
    "1b": ("1б. Заливка рисунком", PatternFillApp),
    "1v": ("1в. Обход границы", BoundaryApp),
    "2": ("2. Брезенхем и Ву", LinesApp),
    "3": ("3. Градиентный треугольник", TriangleApp),
}


def main():
    parser = argparse.ArgumentParser(description="Лабораторная работа №3")
    parser.add_argument("task", nargs="?", choices=TASKS, help="Номер задания: 1a, 1b, 1v, 2 или 3")
    args = parser.parse_args()
    root = tk.Tk()
    if args.task:
        app = TASKS[args.task][1](root)
    else:
        root.title("Лабораторная работа №3")
        tk.Label(root, text="Выберите задание").pack(padx=30, pady=15)

        def open_task(app_class):
            window = tk.Toplevel(root)
            window.app = app_class(window)

        for title, app_class in TASKS.values():
            tk.Button(root, text=title, width=32,
                      command=lambda cls=app_class: open_task(cls)).pack(padx=20, pady=5)
    root.mainloop()


if __name__ == "__main__":
    main()
