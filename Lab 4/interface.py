import math
import tkinter as tk
from tkinter import ttk
import member1_transforms as transforms
import member2_edges as edges
import member3_polygons as polygons


MESSAGES = {
    "empty": "Сначала создайте фигуру.",
    "self_intersection": "Стороны пересекаются. Нужен простой полигон; отмените последнюю вершину.",
    "zero_area": "Вершины лежат на одной прямой. Для ребра оставьте две вершины.",
    "zero_scale": "Коэффициенты масштаба должны быть ненулевыми.",
    "nonfinite": "Слишком большие значения преобразования.",
    "inside": "Точка внутри", "outside": "Точка снаружи", "boundary": "Точка на границе",
    "left": "Точка слева от A → B", "right": "Точка справа от A → B",
    "on_segment": "Точка на отрезке", "on_line": "Точка на продолжении прямой",
    "degenerate": "У ребра нулевая длина: справа и слева не определены.",
}
HELP = {
    "draw": "ЛКМ — вершина. Enter, ПКМ или «Завершить» — сохранить фигуру. Можно оставить 1 или 2 вершины.",
    "pivot": "Щёлкните, чтобы задать центр преобразования. Затем примените поворот или масштаб.",
    "inside": "Щёлкайте для проверки точек относительно выбранного полигона. Инструмент остаётся активным.",
    "side": "Выберите ребро A → B в списке. Каждый щелчок проверяет новую точку.",
    "intersect": "Выберите первое ребро. Два щелчка задают второе, движение мыши показывает пересечение. Можно сразу задать следующее.",
}


class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная 4. Аффинные преобразования")
        root.geometry("1220x850")
        self.figures = []
        self.draft = []
        self.pivot = None
        self.probe = None
        self.second_start = None
        self.second_end = None
        self.mode = tk.StringVar(value="draw")
        self.pivot_mode = tk.StringVar(value="center")
        self.status = tk.StringVar(value=HELP["draw"])
        self.fields = {}
        controls = ttk.Frame(root, padding=10)
        controls.pack(side="left", fill="y")
        ttk.Label(controls, text="Лабораторная №4", font=("Arial", 15, "bold")).pack(anchor="w")
        ttk.Label(controls, text="1 — матрицы; 2 — рёбра; 3 — полигоны", wraplength=340).pack(anchor="w", pady=5)
        for value, title in [("draw", "Создать фигуру"), ("pivot", "Задать центр мышью"),
                             ("inside", "Точка в полигоне"), ("side", "Справа / слева от ребра"),
                             ("intersect", "Пересечение двух рёбер")]:
            ttk.Radiobutton(controls, text=title, variable=self.mode, value=value,
                            command=self.change_mode).pack(anchor="w")
        row = ttk.Frame(controls); row.pack(fill="x", pady=5)
        ttk.Button(row, text="Завершить", command=self.finish).pack(side="left")
        ttk.Button(row, text="Убрать вершину", command=self.undo).pack(side="left")
        ttk.Button(controls, text="Очистить сцену", command=self.clear).pack(fill="x", pady=4)
        ttk.Label(controls, text="Выбранная фигура:").pack(anchor="w")
        self.figure_box = ttk.Combobox(controls, state="readonly", width=35)
        self.figure_box.pack(fill="x")
        self.figure_box.bind("<<ComboboxSelected>>", self.select_figure)
        ttk.Label(controls, text="Направленное ребро A → B:").pack(anchor="w", pady=(5,0))
        self.edge_box = ttk.Combobox(controls, state="readonly", width=35)
        self.edge_box.pack(fill="x")
        self.edge_box.bind("<<ComboboxSelected>>", self.select_edge)
        group = ttk.LabelFrame(controls, text="Преобразования", padding=6)
        group.pack(fill="x", pady=10)
        self.add_fields(group, [("dx", "40"), ("dy", "20")])
        ttk.Button(group, text="Сместить", command=lambda: self.transform("move")).pack(fill="x")
        ttk.Radiobutton(group, text="Относительно своего центра", variable=self.pivot_mode, value="center").pack(anchor="w", pady=(8,0))
        ttk.Radiobutton(group, text="Относительно точки мышью", variable=self.pivot_mode, value="point").pack(anchor="w")
        self.add_fields(group, [("Угол, °", "30")])
        ttk.Button(group, text="Повернуть", command=lambda: self.transform("rotate")).pack(fill="x")
        self.add_fields(group, [("kx", "1.2"), ("ky", "1.2")])
        ttk.Button(group, text="Масштабировать", command=lambda: self.transform("scale")).pack(fill="x")
        ttk.Label(controls, text="X вправо, Y вверх. Положительный угол — против часовой стрелки.\nЦентр полигона — центр площади; ребра — середина; точки — она сама.", wraplength=320).pack(anchor="w", pady=5)
        self.help_label = ttk.Label(controls, text=HELP["draw"], wraplength=320)
        self.help_label.pack(anchor="w", pady=8)
        area = ttk.Frame(root); area.pack(side="right", fill="both", expand=True)
        ttk.Label(area, textvariable=self.status, wraplength=800, padding=8).pack(side="bottom", fill="x")
        self.canvas = tk.Canvas(area, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Button-3>", lambda _: self.finish() if self.mode.get() == "draw" else None)
        self.canvas.bind("<Motion>", self.motion)
        self.canvas.bind("<Configure>", lambda _: self.redraw())
        self.canvas.bind("<Return>", lambda _: self.finish() if self.mode.get() == "draw" else None)
        self.canvas.bind("<Escape>", lambda _: self.cancel())

    def add_fields(self, parent, values):
        row = ttk.Frame(parent); row.pack(fill="x", pady=4)
        for name, value in values:
            ttk.Label(row, text=name).pack(side="left", padx=3)
            field = ttk.Entry(row, width=8)
            field.insert(0, value); field.pack(side="left")
            self.fields[name] = field

    def selected(self):
        index = self.figure_box.current()
        return self.figures[index] if 0 <= index < len(self.figures) else None

    def selected_edge(self):
        vertices = self.selected()
        sides = edges.edges(vertices) if vertices else []
        index = self.edge_box.current()
        return sides[index] if 0 <= index < len(sides) else None

    def world(self, event):
        return event.x - self.canvas.winfo_width()/2, self.canvas.winfo_height()/2 - event.y

    def screen(self, point):
        return point[0] + self.canvas.winfo_width()/2, self.canvas.winfo_height()/2 - point[1]

    def change_mode(self):
        self.probe = self.second_start = self.second_end = None
        self.help_label.config(text=HELP[self.mode.get()])
        self.status.set(HELP[self.mode.get()]); self.redraw()

    def select_figure(self, event=None):
        vertices = self.selected()
        sides = edges.edges(vertices) if vertices else []
        self.edge_box.configure(values=[f"{i+1}: вершина {i+1} → {(i+1)%len(vertices)+1}" for i in range(len(sides))])
        if sides: self.edge_box.current(0)
        else: self.edge_box.set("")
        self.change_mode()

    def select_edge(self, event=None):
        self.probe = self.second_start = self.second_end = None
        self.status.set(HELP[self.mode.get()]); self.redraw()

    def update_list(self, index):
        labels=[]
        for i, vertices in enumerate(self.figures):
            kind = "точка" if len(vertices)==1 else "ребро" if len(vertices)==2 else "выпуклый" if polygons.is_convex(vertices) else "невыпуклый"
            labels.append(f"{i+1}. {kind}, вершин: {len(vertices)}")
        self.figure_box.configure(values=labels)
        self.figure_box.current(index)

    def finish(self):
        if not self.draft: return
        try: vertices = polygons.make_polygon(self.draft)
        except ValueError as error:
            self.status.set(MESSAGES.get(str(error), str(error))); return
        self.figures.append(vertices); self.draft=[]
        self.update_list(len(self.figures)-1); self.select_figure()
        self.status.set("Фигура создана. Можно создать следующую или выбрать инструмент.")

    def undo(self):
        if self.draft: self.draft.pop()
        self.redraw()

    def cancel(self):
        self.draft=[]; self.probe=self.second_start=self.second_end=None
        self.status.set(HELP[self.mode.get()]); self.redraw()

    def clear(self):
        self.figures=[]; self.draft=[]
        self.pivot=self.probe=self.second_start=self.second_end=None
        self.figure_box.configure(values=[]); self.figure_box.set("")
        self.edge_box.configure(values=[]); self.edge_box.set("")
        self.status.set("Сцена очищена."); self.redraw()

    def click(self, event):
        self.canvas.focus_set()
        point=self.world(event); mode=self.mode.get()
        if mode=="draw":
            self.draft.append(point)
            self.status.set(f"Вершин: {len(self.draft)}. Enter или «Завершить» сохраняет фигуру.")
        elif mode=="pivot":
            self.pivot=point; self.pivot_mode.set("point")
            self.status.set(f"Центр: ({point[0]:.1f}, {point[1]:.1f}).")
        elif self.selected() is None:
            self.status.set("Сначала создайте или выберите фигуру.")
        elif mode=="inside":
            self.probe=point
            self.status.set(MESSAGES[polygons.contains_point(self.selected(),point)])
        elif self.selected_edge() is None:
            self.status.set("Для этого инструмента нужна фигура хотя бы с двумя вершинами.")
        elif mode=="side":
            self.probe=point
            self.status.set(MESSAGES[edges.point_side(*self.selected_edge(),point)])
        elif mode=="intersect":
            if self.second_start is None:
                self.second_start=point; self.second_end=point
            else:
                self.second_end=point
                self.report_intersection(self.second_start,point)
                self.probe=(self.second_start,point)
                self.second_start=self.second_end=None
        self.redraw()

    def motion(self, event):
        if self.mode.get()=="intersect" and self.second_start is not None:
            self.second_end=self.world(event)
            self.report_intersection(self.second_start,self.second_end)
            self.redraw()

    def report_intersection(self, a, b):
        kind, points=edges.intersection(*self.selected_edge(),a,b)
        if kind=="none": text="Отрезки не пересекаются."
        elif kind=="point": text=f"Пересечение: ({points[0][0]:.2f}, {points[0][1]:.2f})."
        else: text=f"Совпадают на отрезке от {tuple(round(v,2) for v in points[0])} до {tuple(round(v,2) for v in points[1])}."
        self.status.set(text+" Два следующих щелчка — новое ребро.")

    def number(self, name):
        value=float(self.fields[name].get().replace(",","."))
        if not math.isfinite(value): raise ValueError("nonfinite")
        return value

    def transform(self, operation):
        vertices=self.selected()
        if vertices is None:
            self.status.set("Сначала создайте или выберите фигуру."); return
        pivot=None
        if operation!="move" and self.pivot_mode.get()=="point":
            if self.pivot is None:
                self.status.set("Сначала задайте центр инструментом «Задать центр мышью»."); return
            pivot=self.pivot
        try:
            if operation=="move": result=transforms.move(vertices,self.number("dx"),self.number("dy"))
            elif operation=="rotate": result=transforms.rotate(vertices,self.number("Угол, °"),pivot)
            else: result=transforms.scale(vertices,self.number("kx"),self.number("ky"),pivot)
            if any(abs(v)>1e7 for p in result for v in p): raise ValueError("nonfinite")
        except (ValueError, OverflowError) as error:
            self.status.set(MESSAGES.get(str(error),"Введите корректные числовые значения.")); return
        index=self.figure_box.current(); self.figures[index]=result
        self.update_list(index)
        self.probe=self.second_start=self.second_end=None
        self.status.set("Преобразование применено матрицей."); self.redraw()

    def dot(self, point, color, radius=4):
        x,y=self.screen(point)
        self.canvas.create_oval(x-radius,y-radius,x+radius,y+radius,fill=color,outline=color)

    def line(self, a, b, **kwargs):
        self.canvas.create_line(*self.screen(a),*self.screen(b),**kwargs)

    def redraw(self):
        self.canvas.delete("all")
        w,h=self.canvas.winfo_width(),self.canvas.winfo_height()
        self.canvas.create_line(0,h/2,w,h/2,fill="#dddddd",arrow="last")
        self.canvas.create_line(w/2,h,w/2,0,fill="#dddddd",arrow="last")
        self.canvas.create_text(w-15,h/2+12,text="X"); self.canvas.create_text(w/2+12,15,text="Y")
        for index, vertices in enumerate(self.figures):
            color="#1769aa" if index==self.figure_box.current() else "#888888"
            for a,b in edges.edges(vertices): self.line(a,b,fill=color,width=2)
            for i,point in enumerate(vertices):
                self.dot(point,color,3)
                if index==self.figure_box.current():
                    x,y=self.screen(point);self.canvas.create_text(x+10,y-10,text=str(i+1),fill=color)
        for a,b in zip(self.draft,self.draft[1:]):self.line(a,b,fill="#555555",dash=(4,3))
        for point in self.draft:self.dot(point,"#555555")
        if self.pivot is not None:self.dot(self.pivot,"#9b2fae",5)
        if self.selected() is not None:self.dot(transforms.center(self.selected()),"#2b9a57",3)
        mode=self.mode.get()
        edge=self.selected_edge()
        if edge and mode in ("side","intersect"):
            self.line(*edge,fill="#d07400",width=3,arrow="last")
        if mode in ("inside","side") and self.probe is not None:self.dot(self.probe,"#ce2950",5)
        if mode=="intersect" and edge:
            segment=(self.second_start,self.second_end) if self.second_start is not None else self.probe
            if segment:
                self.line(*segment,fill="#8e44ad",width=2)
                for point in segment:self.dot(point,"#8e44ad",3)
                kind,points=edges.intersection(*edge,*segment)
                if kind=="overlap":self.line(*points,fill="#e53935",width=5)
                for point in points:self.dot(point,"#e53935",5)


if __name__=="__main__":
    root=tk.Tk()
    app=App(root)
    root.mainloop()
