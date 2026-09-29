import math
import tkinter as tk
from tkinter import ttk



functions = {
    "sin(x)": math.sin,
    "x^2": lambda x: x ** 2,
    "cos(x)": math.cos,
    "x^3": lambda x: x ** 3,
}



def to_screen(x, y, x_min, x_max, y_min, y_max, width, height):
    margin = 40

    graph_width = width - 2 * margin
    graph_height = height - 2 * margin

    screen_x = (
        margin
        + (x - x_min) / (x_max - x_min) * graph_width
    )

    screen_y = (
        height
        - margin
        - (y - y_min) / (y_max - y_min) * graph_height
    )

    return screen_x, screen_y



def draw_graph(func, x_min, x_max):
    canvas.delete("all")

    width = canvas.winfo_width()
    height = canvas.winfo_height()

    margin = 40

    
    if x_min >= x_max:
        return

    
    points = []

    
    y_min = float("inf")
    y_max = float("-inf")

    count = 500

    # Считаем точки функции
    for i in range(count):
        x = (
            x_min
            + (x_max - x_min) * i / (count - 1)
        )

        y = func(x)

        points.append((x, y))

        y_min = min(y_min, y)
        y_max = max(y_max, y)

    
    if y_min == y_max:
        y_min -= 1
        y_max += 1

    
    padding = (y_max - y_min) * 0.05

    y_min -= padding
    y_max += padding

    # Рамка области графика
    canvas.create_rectangle(
        margin,
        margin,
        width - margin,
        height - margin,
        outline="gray"
    )

    # Ось X
    if y_min <= 0 <= y_max:
        x1, y0 = to_screen(
            x_min,
            0,
            x_min,
            x_max,
            y_min,
            y_max,
            width,
            height
        )

        x2, y0 = to_screen(
            x_max,
            0,
            x_min,
            x_max,
            y_min,
            y_max,
            width,
            height
        )

        canvas.create_line(
            x1,
            y0,
            x2,
            y0,
            fill="black"
        )

    # Ось Y
    if x_min <= 0 <= x_max:
        x0, y1 = to_screen(
            0,
            y_min,
            x_min,
            x_max,
            y_min,
            y_max,
            width,
            height
        )

        x0, y2 = to_screen(
            0,
            y_max,
            x_min,
            x_max,
            y_min,
            y_max,
            width,
            height
        )

        canvas.create_line(
            x0,
            y1,
            x0,
            y2,
            fill="black"
        )

    #рисуем график 
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]

        screen_x1, screen_y1 = to_screen(
            x1,
            y1,
            x_min,
            x_max,
            y_min,
            y_max,
            width,
            height
        )

        screen_x2, screen_y2 = to_screen(
            x2,
            y2,
            x_min,
            x_max,
            y_min,
            y_max,
            width,
            height
        )

        canvas.create_line(
            screen_x1,
            screen_y1,
            screen_x2,
            screen_y2,
            fill="blue",
            width=2
        )



def button_click():
    try:
        x_min = float(entry_x_min.get())
        x_max = float(entry_x_max.get())

        function_name = function_box.get()

        func = functions[function_name]

        draw_graph(
            func,
            x_min,
            x_max
        )

    except ValueError:
        pass



def resize(event):
    try:
        x_min = float(entry_x_min.get())
        x_max = float(entry_x_max.get())

        function_name = function_box.get()

        if function_name != "":
            func = functions[function_name]

            draw_graph(
                func,
                x_min,
                x_max
            )

    except ValueError:
        pass


# Главное окно
root = tk.Tk()

root.title("График функции")
root.geometry("800x600")


# Верхняя панель
top_frame = tk.Frame(root)

top_frame.pack(pady=10)


# Надпись "Функция"
tk.Label(top_frame,text="Функция:").pack(side="left")


# Список функций
function_box = ttk.Combobox(top_frame,values=list(functions.keys()),state="readonly",width=10)

function_box.set("sin(x)")

function_box.pack(side="left", padx=5)


# X min
tk.Label(top_frame,text="X min:").pack(side="left",padx=5)

entry_x_min = tk.Entry(top_frame, width=8)

entry_x_min.insert(0, "-10")

entry_x_min.pack(side="left")

# X max
tk.Label(top_frame, text="X max:").pack(side="left",padx=5)

entry_x_max = tk.Entry(top_frame, width=8)

entry_x_max.insert(0, "10")

entry_x_max.pack(side="left")

button = tk.Button(top_frame,text="Построить",command=button_click)

button.pack(side="left", padx=10)

canvas = tk.Canvas(root,bg="white")

canvas.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

canvas.bind("<Configure>",resize)

root.mainloop()