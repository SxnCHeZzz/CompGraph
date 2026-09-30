import tkinter as tk
from tkinter import filedialog, messagebox
from collections import deque
from PIL import Image, ImageTk, ImageDraw
import numpy as np


NEIGHBORS = [(-1, 0), (-1, -1), (0, -1), (1, -1),
             (1, 0), (1, 1), (0, 1), (-1, 1)]


def trace_boundary(pixels, x, y):
    height, width = pixels.shape[:2]
    if not (0 <= x < width and 0 <= y < height):
        return []
    color = pixels[y, x]
    component = {(x, y)}
    queue = deque([(x, y)])
    # Выбираем связную часть цвета, по которому щёлкнули.
    while queue:
        px, py = queue.popleft()
        for dx, dy in NEIGHBORS:
            point = px + dx, py + dy
            nx, ny = point
            if (0 <= nx < width and 0 <= ny < height and point not in component
                    and np.array_equal(pixels[ny, nx], color)):
                component.add(point)
                queue.append(point)

    start = min(component, key=lambda point: (point[1], point[0]))
    current = start
    back = (start[0] - 1, start[1])
    contour = []
    first_next = None
    states = set()
    # Обход Мура: проверяем восемь соседей по кругу.
    while True:
        state = (current, back)
        if state in states:
            break
        states.add(state)
        offset = back[0] - current[0], back[1] - current[1]
        index = NEIGHBORS.index(offset)
        following = None
        for step in range(1, 9):
            neighbor_index = (index + step) % 8
            dx, dy = NEIGHBORS[neighbor_index]
            candidate = current[0] + dx, current[1] + dy
            if candidate in component:
                following = candidate
                bx, by = NEIGHBORS[(neighbor_index - 1) % 8]
                new_back = current[0] + bx, current[1] + by
                break
        if following is None:
            contour.append(current)
            break
        if first_next is not None and current == start and following == first_next:
            break
        contour.append(current)
        if first_next is None:
            first_next = following
        current, back = following, new_back
    return contour


class App:
    def __init__(self, root):
        root.title("1в. Обход границы")
        self.original = None
        self.result = None
        self.contour = []
        bar = tk.Frame(root)
        bar.pack(fill="x")
        tk.Button(bar, text="Открыть изображение", command=self.load).pack(side="left")
        tk.Button(bar, text="Сохранить результат", command=self.save).pack(side="left")
        tk.Label(root, text="Щёлкните по одноцветной границе. Её внешний контур будет выделен цветом.\nДля точного цвета удобнее PNG или BMP. Координаты сохраняются в порядке обхода.").pack()
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

    def select(self, event):
        if self.original is None:
            return
        x, y = int(self.canvas.canvasx(event.x)), int(self.canvas.canvasy(event.y))
        self.contour = trace_boundary(np.array(self.original), x, y)
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


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
