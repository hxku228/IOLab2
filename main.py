import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib

matplotlib.use('TkAgg')
import numpy as np


class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Алгоритмы на графах - Лабораторная работа")
        self.root.geometry("1400x900")

        self.graph = nx.DiGraph()
        self.pos = None
        self.node_patches = {}
        self.node_labels = {}
        self.edge_lines = {}
        self.edge_labels = {}

        self.mode = "drag"
        self.edge_start = None
        self.drag_node = None
        self.drag_offset = (0, 0)

        self.create_widgets()
        self.bind_mouse_events()

    def create_widgets(self):
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky="nsew")

        graph_frame = ttk.Frame(self.root, padding="10")
        graph_frame.grid(row=0, column=1, sticky="nsew")

        output_frame = ttk.Frame(self.root, padding="10")
        output_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(1, weight=1)

        self.create_control_panel(control_frame)
        self.create_graph_panel(graph_frame)
        self.create_output_panel(output_frame)

    def create_control_panel(self, parent):
        title_label = ttk.Label(parent, text="Управление графом", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20), sticky="w")

        ttk.Label(parent, text="Добавление вершин:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w",
                                                                                      pady=(0, 5))
        vertex_frame = ttk.Frame(parent)
        vertex_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(vertex_frame, text="Имя вершины:").pack(side=tk.LEFT, padx=(0, 5))
        self.vertex_entry = ttk.Entry(vertex_frame, width=15)
        self.vertex_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(vertex_frame, text="Добавить", command=self.add_vertex).pack(side=tk.LEFT)

        ttk.Button(parent, text="Очистить граф", command=self.clear_graph).grid(row=3, column=0, sticky="ew", pady=5)

        ttk.Label(parent, text="Режим работы:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w",
                                                                                 pady=(20, 5))
        mode_frame = ttk.Frame(parent)
        mode_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))

        self.mode_var = tk.StringVar(value="drag")
        ttk.Radiobutton(mode_frame, text="Перетаскивание вершин", variable=self.mode_var, value="drag",
                        command=self.set_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Добавление рёбер", variable=self.mode_var, value="edge",
                        command=self.set_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Удаление рёбер", variable=self.mode_var, value="delete_edge",
                        command=self.set_mode).pack(anchor=tk.W)

        info_frame = ttk.LabelFrame(parent, text="Информация о графе", padding="10")
        info_frame.grid(row=6, column=0, sticky="nsew", pady=(20, 0))
        self.info_text = scrolledtext.ScrolledText(info_frame, height=10, width=30)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.update_graph_info()

    def create_graph_panel(self, parent):
        title_label = ttk.Label(parent, text="Визуализация графа", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky="w")

        algorithms_frame = ttk.Frame(parent)
        algorithms_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.create_algorithm_buttons(algorithms_frame)

        fig_frame = ttk.Frame(parent)
        fig_frame.grid(row=2, column=0, sticky="nsew")
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.figure = plt.figure(figsize=(12, 8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, fig_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.draw_graph()

    def create_algorithm_buttons(self, parent):
        algorithms = [
            ("1. Компоненты сильной связности (Косарайю)", self.find_scc),
            ("2. Алгоритм Прима", self.prim_algorithm),
            ("3. Алгоритм A*", self.a_star_algorithm),
            ("4. Алгоритм Диница", self.dinic_algorithm),
            ("5. Алгоритм Джонсона", self.johnson_algorithm)
        ]
        for i, (text, command) in enumerate(algorithms):
            btn = ttk.Button(parent, text=text, command=command)
            btn.grid(row=0, column=i, padx=2, sticky="ew")
            parent.grid_columnconfigure(i, weight=1)

    def create_output_panel(self, parent):
        title_label = ttk.Label(parent, text="Результаты работы алгоритмов", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky="w")

        self.output_text = scrolledtext.ScrolledText(parent, height=12, width=100)
        self.output_text.grid(row=1, column=0, sticky="nsew")

        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, sticky="e", pady=(5, 0))
        ttk.Button(button_frame, text="Очистить вывод", command=self.clear_output).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Копировать", command=self.copy_output).pack(side=tk.RIGHT)

        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

    def set_mode(self):
        self.mode = self.mode_var.get()
        self.edge_start = None
        self.drag_node = None

        if self.mode == "drag":
            title = "Режим перетаскивания: перетаскивайте вершины мышкой"
        elif self.mode == "edge":
            title = "Режим добавления рёбер: кликните на начальную вершину"
        elif self.mode == "delete_edge":
            title = "Режим удаления рёбер: кликните на ребро или две вершины"
        else:
            title = "Граф"

        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.canvas.draw_idle()

    def bind_mouse_events(self):
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_press(self, event):
        if event.inaxes is None:
            return

        if self.mode == "drag":
            for node, (x, y) in self.pos.items():
                distance = np.sqrt((event.xdata - x) ** 2 + (event.ydata - y) ** 2)
                if distance <= 1.5:
                    self.drag_node = node
                    self.drag_offset = (event.xdata - x, event.ydata - y)
                    if node in self.node_patches:
                        self.node_patches[node].set_color('orange')
                        self.node_patches[node].set_alpha(0.9)
                        self.canvas.draw_idle()
                    return

        elif self.mode == "edge":
            for node, (x, y) in self.pos.items():
                distance = np.sqrt((event.xdata - x) ** 2 + (event.ydata - y) ** 2)
                if distance <= 1.5:
                    if self.edge_start is None:
                        self.edge_start = node
                        self.highlight_node(node, 'lightgreen')
                        self.ax.set_title(
                            f"Режим добавления рёбер: начальная вершина '{node}', кликните на конечную вершину",
                            fontsize=14, fontweight='bold')
                    else:
                        edge_end = node
                        if self.edge_start == edge_end:
                            messagebox.showwarning("Предупреждение", "Нельзя создать ребро из вершины в саму себя!")
                            self.clear_edge_selection()
                            return
                        weight = self.ask_edge_weight(edge_end)
                        if weight is None:
                            self.clear_edge_selection()
                            return
                        self.graph.add_edge(self.edge_start, edge_end, weight=weight)
                        self.update_graph_info()
                        self.draw_graph()
                        self.clear_edge_selection()
                    self.canvas.draw_idle()
                    return

        elif self.mode == "delete_edge":
            clicked_edge = self.find_clicked_edge(event.xdata, event.ydata)
            if clicked_edge:
                u, v = clicked_edge
                self.graph.remove_edge(u, v)
                self.print_output(f"Ребро {u} → {v} удалено.")
                self.update_graph_info()
                self.draw_graph()
                return

            for node, (x, y) in self.pos.items():
                distance = np.sqrt((event.xdata - x) ** 2 + (event.ydata - y) ** 2)
                if distance <= 1.5:
                    if self.edge_start is None:
                        self.edge_start = node
                        self.highlight_node(node, 'salmon')
                        self.ax.set_title(
                            f"Выбрана вершина '{node}'. Кликните на вторую вершину для удаления ребра.",
                            fontsize=14, fontweight='bold')
                    else:
                        if self.edge_start == node:
                            self.clear_edge_selection()
                            return
                        removed = False
                        if self.graph.has_edge(self.edge_start, node):
                            self.graph.remove_edge(self.edge_start, node)
                            self.print_output(f"Ребро {self.edge_start} → {node} удалено.")
                            removed = True
                        elif self.graph.has_edge(node, self.edge_start):
                            self.graph.remove_edge(node, self.edge_start)
                            self.print_output(f"Ребло {node} → {self.edge_start} удалено.")
                            removed = True
                        else:
                            messagebox.showinfo("Информация", f"Ребро между {self.edge_start} и {node} не найдено.")
                        self.update_graph_info()
                        self.draw_graph()
                        self.clear_edge_selection()
                        return
                    self.canvas.draw_idle()
                    return

    def ask_edge_weight(self, edge_end):
        """
        Запрашивает вес ребра у пользователя.
        Если вершины имеют позиции, предлагает геометрическое расстояние как значение по умолчанию.
        """
        # Вычисляем геометрическое расстояние, если позиции известны
        default_weight = 1.0
        if self.pos and self.edge_start in self.pos and edge_end in self.pos:
            x1, y1 = self.pos[self.edge_start]
            x2, y2 = self.pos[edge_end]
            dist = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            default_weight = round(dist, 2)  # округляем до 2 знаков

        dialog = tk.Toplevel(self.root)
        dialog.title("Вес ребра")
        dialog.geometry("350x220")
        dialog.transient(self.root)
        dialog.grab_set()

        # Центрирование
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        label = ttk.Label(dialog, text=f"Введите вес ребра {self.edge_start} → {edge_end}:", font=("Arial", 11))
        label.pack(pady=10)

        # Подсказка о геометрическом расстоянии
        if default_weight != 1.0:
            hint = ttk.Label(dialog, text=f"Геометрическое расстояние: {default_weight:.2f}",
                             font=("Arial", 9, "italic"), foreground="gray")
            hint.pack()

        weight_var = tk.StringVar(value=f"{default_weight:.2f}")
        entry_frame = ttk.Frame(dialog)
        entry_frame.pack(pady=5)
        entry = ttk.Entry(entry_frame, textvariable=weight_var, width=15, font=("Arial", 11))
        entry.pack()
        entry.focus_set()

        result = {"weight": None}

        def on_ok():
            try:
                weight = float(weight_var.get())
                if weight <= 0:
                    raise ValueError
                result["weight"] = weight
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Вес должен быть положительным числом!", parent=dialog)
                entry.focus_set()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Отмена", command=on_cancel, width=10).pack(side=tk.LEFT)

        entry.bind('<Return>', lambda e: on_ok())
        dialog.bind('<Escape>', lambda e: on_cancel())
        self.root.wait_window(dialog)
        return result["weight"]

    def highlight_node(self, node, color):
        if node in self.node_patches:
            self.node_patches[node].set_color(color)
            self.node_patches[node].set_alpha(0.9)

    def clear_edge_selection(self):
        if self.edge_start and self.edge_start in self.node_patches:
            self.node_patches[self.edge_start].set_color('lightblue')
            self.node_patches[self.edge_start].set_alpha(0.8)
        self.edge_start = None
        if self.mode == "edge":
            title = "Режим добавления рёбер: кликните на начальную вершину"
        elif self.mode == "delete_edge":
            title = "Режим удаления рёбер: кликните на ребро или две вершины"
        else:
            title = "Режим перетаскивания: перетаскивайте вершины мышкой"
        self.ax.set_title(title, fontsize=14, fontweight='bold')

    def on_release(self, event):
        if self.mode == "drag" and self.drag_node:
            if self.drag_node in self.node_patches:
                self.node_patches[self.drag_node].set_color('lightblue')
                self.node_patches[self.drag_node].set_alpha(0.8)
            # Обновляем граф, чтобы рёбра "догнали" вершину
            self.draw_graph()

        self.drag_node = None
        self.drag_offset = (0, 0)

    def on_motion(self, event):
        if self.mode == "drag" and self.drag_node and event.inaxes:
            new_x = event.xdata - self.drag_offset[0]
            new_y = event.ydata - self.drag_offset[1]
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            margin = 0.3
            new_x = max(x_min + margin, min(x_max - margin, new_x))
            new_y = max(y_min + margin, min(y_max - margin, new_y))
            self.pos[self.drag_node] = (new_x, new_y)

            if self.drag_node in self.node_patches:
                self.node_patches[self.drag_node].center = (new_x, new_y)
            if self.drag_node in self.node_labels:
                self.node_labels[self.drag_node].set_position((new_x, new_y))

            self.canvas.draw_idle()

    def find_clicked_edge(self, x_click, y_click, threshold=1.0):
        if not hasattr(self, 'edge_lines') or not self.graph.edges():
            return None
        min_dist = float('inf')
        closest_edge = None
        for (u, v) in self.graph.edges():
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            dist = self.point_to_segment_distance(x_click, y_click, x1, y1, x2, y2)
            if dist < min_dist and dist < threshold:
                min_dist = dist
                closest_edge = (u, v)
        return closest_edge

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        line_vec = np.array([x2 - x1, y2 - y1])
        point_vec = np.array([px - x1, py - y1])
        line_len = np.dot(line_vec, line_vec)
        if line_len == 0:
            return np.linalg.norm(point_vec)
        t = max(0, min(1, np.dot(point_vec, line_vec) / line_len))
        projection = np.array([x1, y1]) + t * line_vec
        return np.linalg.norm(np.array([px, py]) - projection)

    def add_vertex(self):
        vertex = self.vertex_entry.get().strip()
        if not vertex:
            messagebox.showwarning("Предупреждение", "Введите имя вершины!")
            return
        if vertex in self.graph.nodes():
            messagebox.showwarning("Предупреждение", "Вершина уже существует!")
            return
        self.graph.add_node(vertex)
        self.vertex_entry.delete(0, tk.END)
        self.update_graph_info()
        self.draw_graph()

    def clear_graph(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить граф?"):
            self.graph.clear()
            self.pos = None
            self.node_patches = {}
            self.node_labels = {}
            self.edge_start = None
            self.drag_node = None
            self.update_graph_info()
            self.draw_graph()

    def update_graph_info(self):
        self.info_text.delete(1.0, tk.END)
        if not self.graph.nodes():
            self.info_text.insert(tk.END, "Граф пуст")
            return
        self.info_text.insert(tk.END, "Вершины:\n")
        vertices = list(self.graph.nodes())
        for i, v in enumerate(vertices):
            self.info_text.insert(tk.END, f"  {v}")
            if (i + 1) % 5 == 0:
                self.info_text.insert(tk.END, "\n")
            elif i != len(vertices) - 1:
                self.info_text.insert(tk.END, ", ")
        self.info_text.insert(tk.END, "\n\nРёбра:\n")
        for u, v, data in self.graph.edges(data=True):
            weight = data.get('weight', 1.0)
            self.info_text.insert(tk.END, f"  {u} → {v} (вес: {weight})\n")
        self.info_text.insert(tk.END, f"\nВсего вершин: {self.graph.number_of_nodes()}\n")
        self.info_text.insert(tk.END, f"Всего рёбер: {self.graph.number_of_edges()}\n")
        self.info_text.insert(tk.END, "\nИнструкция:\n")
        self.info_text.insert(tk.END, "1. Перетаскивание: режим 'Перетаскивание'\n")
        self.info_text.insert(tk.END, "2. Добавление рёбер: режим 'Добавление рёбер'\n")
        self.info_text.insert(tk.END, "3. Удаление рёбер: режим 'Удаление рёбер'\n")

    def _draw_graph_on_ax(self, ax, graph, pos, title="", show_order=None):
        ax.clear()
        if not graph.nodes():
            ax.text(0.5, 0.5, "Граф пуст", ha='center', va='center')
            ax.set_axis_off()
            return

        is_directed = graph.is_directed()

        #ребра
        for u, v, data in graph.edges(data=True):
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            dx, dy = x2 - x1, y2 - y1
            length = np.hypot(dx, dy)
            shrink = 1.1 if length > 0 else 0

            if length > 0:
                if is_directed:
                    x2_adj = x1 + dx * (length - shrink) / length
                    y2_adj = y1 + dy * (length - shrink) / length
                    ax.annotate("", xy=(x2_adj, y2_adj), xytext=(x1, y1),
                                arrowprops=dict(arrowstyle="->", color='gray', linewidth=1.5),
                                annotation_clip=False)
                else:
                    ax.plot([x1, x2], [y1, y2], color='gray', linewidth=1.5, alpha=0.8)
            else:
                #петля для прикола
                circle = plt.Circle((x1, y1), radius=1.5, color='gray', fill=False, linewidth=1.5)
                ax.add_patch(circle)

            # Подпись веса
            weight = data.get('weight', 1.0)
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            offset_x = -0.4 * dy / (length + 1e-6)
            offset_y = 0.4 * dx / (length + 1e-6)
            ax.text(mid_x + offset_x, mid_y + offset_y, f"{weight:.1f}",
                    fontsize=10, ha='center', va='center',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.7))

        #вершины
        for node, (x, y) in pos.items():
            circle = plt.Circle((x, y), radius=1.1, color='lightblue', alpha=0.8, ec='black', linewidth=2)
            ax.add_patch(circle)
            ax.text(x, y, node, fontsize=9, fontweight='bold', ha='center', va='center')
            if show_order and node in show_order:
                order_num = show_order[node]
                ax.text(x, y + 1.3, f"{order_num}", fontsize=11, color='red', weight='bold')

        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_axis_off()

    def draw_graph(self):
        self.ax.clear()
        self.node_patches = {}
        self.node_labels = {}
        self.edge_lines = {}
        self.edge_labels = {}

        if not self.graph.nodes():
            self.ax.text(0.5, 0.5, "Граф пуст\nДобавьте вершины и рёбра", ha='center', va='center', fontsize=12)
            self.ax.set_xlim(-10, 10)
            self.ax.set_ylim(-10, 10)
            self.ax.set_axis_off()
            self.canvas.draw()
            return

        if self.pos is None:
            self.pos = nx.spring_layout(self.graph, seed=42, k=5.0, iterations=50)
            for node in self.pos:
                x, y = self.pos[node]
                self.pos[node] = (x * 8, y * 8)
        else:
            for node in self.graph.nodes():
                if node not in self.pos:
                    self.pos[node] = (np.random.uniform(-9, 9), np.random.uniform(-9, 9))

        # Рисуем рёбра
        for u, v, data in self.graph.edges(data=True):
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx * dx + dy * dy)
            if length > 0:
                shrink = 1.1
                x2_adj = x1 + dx * (length - shrink) / length
                y2_adj = y1 + dy * (length - shrink) / length
            else:
                x2_adj, y2_adj = x2, y2

            arrow = self.ax.annotate("",
                                     xy=(x2_adj, y2_adj),
                                     xytext=(x1, y1),
                                     arrowprops=dict(arrowstyle="->", color='gray', linewidth=1.5),
                                     annotation_clip=False
                                     )
            self.edge_lines[(u, v)] = arrow

            weight = data.get('weight', 1.0)
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            offset_x = -0.4 * dy / (length + 1e-6)
            offset_y = 0.4 * dx / (length + 1e-6)
            label = self.ax.text(mid_x + offset_x, mid_y + offset_y, f"{weight:.1f}",
                                 fontsize=10, ha='center', va='center',
                                 bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.7)
                                 )
            self.edge_labels[(u, v)] = label

        # Рисуем вершины
        for node, (x, y) in self.pos.items():
            circle = plt.Circle((x, y), radius=1.1, color='lightblue', alpha=0.8, ec='black', linewidth=2)
            self.node_patches[node] = circle
            self.ax.add_patch(circle)
            label = self.ax.text(x, y, node, fontsize=9, fontweight='bold', ha='center', va='center')
            self.node_labels[node] = label

        # Заголовок
        if self.mode == "edge":
            title = "Режим добавления рёбер: кликните на начальную вершину"
            if self.edge_start:
                title = f"Режим добавления рёбер: начальная вершина '{self.edge_start}', кликните на конечную"
        elif self.mode == "delete_edge":
            title = "Режим удаления рёбер: кликните на ребро или две вершины"
            if self.edge_start:
                title = f"Выбрана вершина '{self.edge_start}'. Кликните на вторую."
        else:
            title = "Режим перетаскивания: перетаскивайте вершины мышкой"
        self.ax.set_title(title, fontsize=14, fontweight='bold')

        self.ax.set_axis_off()
        self.ax.set_xlim(-12, 12)
        self.ax.set_ylim(-12, 12)
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle='--', alpha=0.3)
        self.ax.set_xticks(np.arange(-12, 13, 2))
        self.ax.set_yticks(np.arange(-12, 13, 2))
        self.figure.tight_layout()
        self.canvas.draw()

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def copy_output(self):
        output = self.output_text.get(1.0, tk.END).strip()
        if output:
            self.root.clipboard_clear()
            self.root.clipboard_append(output)
            messagebox.showinfo("Успех", "Текст скопирован в буфер обмена")

    def print_output(self, text):
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)

    # === АЛГОРИТМЫ ===

    def find_scc(self):
        self.print_output("\n" + "=" * 60)
        self.print_output("АЛГОРИТМ КОСАРАЙЮ: Компоненты сильной связности")
        self.print_output("=" * 60)
        if not self.graph.nodes():
            self.print_output("Граф пуст!")
            return

        # === Первый DFS ===
        self.print_output("\n→ Первый DFS (исходный граф):")
        visited = set()
        order = []

        def dfs1(node, depth=0):
            visited.add(node)
            self.print_output(f"  {'  ' * depth}Вход в {node}")
            for neighbor in sorted(self.graph.successors(node)):
                if neighbor not in visited:
                    dfs1(neighbor, depth + 1)
            order.append(node)
            self.print_output(f"  {'  ' * depth}Выход из {node} → порядок {len(order)}")

        for node in sorted(self.graph.nodes()):
            if node not in visited:
                dfs1(node)

        self.print_output(f"\nПорядок завершения: {order}")
        self.print_output(f"Обратный порядок для второго DFS: {list(reversed(order))}")

        # === Транспонирование ===
        transposed = self.graph.reverse()
        self.print_output("\n→ Построен транспонированный граф")

        # === Второй DFS ===
        self.print_output("\n→ Второй DFS (транспонированный граф):")
        visited.clear()
        scc_components = []

        def dfs2(node, component, depth=0):
            visited.add(node)
            component.append(node)
            self.print_output(f"  {'  ' * depth}Посетили {node}")
            for neighbor in sorted(transposed.successors(node)):
                if neighbor not in visited:
                    dfs2(neighbor, component, depth + 1)

        for node in reversed(order):
            if node not in visited:
                component = []
                self.print_output(f"\nНачало новой компоненты от {node}:")
                dfs2(node, component)
                scc_components.append(component)
                self.print_output(f"Завершена компонента: {sorted(component)}")

        # === Вывод результата ===
        self.print_output(f"\n✅ Найдено компонент: {len(scc_components)}")
        for i, comp in enumerate(scc_components, 1):
            self.print_output(f"  Компонента {i}: {sorted(comp)}")

        # === Визуализация в основном окне ===
        self.visualize_scc(scc_components)

        # === Пошаговое окно ===
        # Создаём отображение порядка: node -> номер (1, 2, 3...)
        order_map = {node: i + 1 for i, node in enumerate(reversed(order))}
        self.visualize_scc_step_by_step(scc_components, order_map, transposed)


    def visualize_scc_step_by_step(self, scc_components, order_map, transposed_graph):
        step_window = tk.Toplevel(self.root)
        step_window.title("Алгоритм Косарайю — пошаговая визуализация")
        step_window.geometry("1500x700")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=100)

        pos_trans = {node: self.pos[node] for node in self.pos}

        self._draw_graph_on_ax(ax1, self.graph, self.pos, "Исходный граф\n(красные цифры = порядок завершения DFS)",
                               order_map)
        self._draw_graph_on_ax(ax2, transposed_graph, pos_trans,
                               "Транспонированный граф\n(компоненты сильной связности)")

        # Раскраска компонент на правом графе
        colors = plt.cm.tab10(np.linspace(0, 1, len(scc_components)))
        node_to_color = {}
        for i, comp in enumerate(scc_components):
            for node in comp:
                node_to_color[node] = colors[i]

        for node, (x, y) in pos_trans.items():
            color = node_to_color.get(node, 'lightblue')
            circle = plt.Circle((x, y), radius=1.1, color=color, alpha=0.8, ec='black', linewidth=2)
            ax2.add_patch(circle)
            ax2.text(x, y, node, fontsize=9, fontweight='bold', ha='center', va='center')

        # Легенда
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=colors[i], label=f'Компонента {i + 1}') for i in range(len(scc_components))]
        ax2.legend(handles=legend_elements, loc='upper right', fontsize=9)

        canvas = FigureCanvasTkAgg(fig, step_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        plt.tight_layout()
        canvas.draw()

    def visualize_scc(self, scc_components):
        if not self.graph.nodes():
            return
        colors = plt.cm.tab10(np.linspace(0, 1, len(scc_components)))
        self.ax.clear()
        self.node_patches = {}
        self.node_labels = {}
        self.edge_lines = {}
        self.edge_labels = {}

        # Рёбра
        for u, v, data in self.graph.edges(data=True):
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx * dx + dy * dy)
            if length > 0:
                shrink = 1.1
                x2_adj = x1 + dx * (length - shrink) / length
                y2_adj = y1 + dy * (length - shrink) / length
            else:
                x2_adj, y2_adj = x2, y2
            arrow = self.ax.annotate("", xy=(x2_adj, y2_adj), xytext=(x1, y1),
                                     arrowprops=dict(arrowstyle="->", color='gray', linewidth=1.5),
                                     annotation_clip=False)
            self.edge_lines[(u, v)] = arrow
            weight = data.get('weight', 1.0)
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            offset_x = -0.4 * dy / (length + 1e-6)
            offset_y = 0.4 * dx / (length + 1e-6)
            label = self.ax.text(mid_x + offset_x, mid_y + offset_y, f"{weight:.1f}",
                                 fontsize=10, ha='center', va='center',
                                 bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.7))
            self.edge_labels[(u, v)] = label

        # Вершины
        node_to_color = {}
        for i, comp in enumerate(scc_components):
            for node in comp:
                node_to_color[node] = colors[i]
        for node, (x, y) in self.pos.items():
            color = node_to_color.get(node, 'lightblue')
            circle = plt.Circle((x, y), radius=1.1, color=color, alpha=0.8, ec='black', linewidth=2)
            self.node_patches[node] = circle
            self.ax.add_patch(circle)
            label = self.ax.text(x, y, node, fontsize=9, fontweight='bold', ha='center', va='center')
            self.node_labels[node] = label

        # Легенда
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=colors[i], label=f'Компонента {i + 1}') for i in range(len(scc_components))]
        self.ax.legend(handles=legend_elements, loc='upper right')

        self.ax.set_title("Компоненты сильной связности", fontsize=14, fontweight='bold')
        self.ax.set_axis_off()
        self.ax.set_xlim(-12, 12)
        self.ax.set_ylim(-12, 12)
        self.ax.set_aspect('equal')
        self.ax.grid(True, linestyle='--', alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()

    def visualize_mst_side_by_side(self, mst_edges, order_map):
        if not self.graph.nodes():
            return

        pos = {node: self.pos[node] for node in self.pos if node in self.graph}

        step_window = tk.Toplevel(self.root)
        step_window.title("Алгоритм Прима — визуализация")
        step_window.geometry("1500x700")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=100)

        #Левая панель: исходный граф
        self._draw_graph_on_ax(ax1, self.graph, pos, "Исходный граф")

        #Правая панель: MST (неориентированный)
        mst_graph = nx.Graph()
        mst_graph.add_nodes_from(self.graph.nodes())
        for u, v, w in mst_edges:
            mst_graph.add_edge(u, v, weight=w)

        self._draw_graph_on_ax(ax2, mst_graph, pos, "Минимальное остовное дерево (MST)")

        #порядок добавления
        for node, (x, y) in pos.items():
            if node in order_map:
                order_num = order_map[node]
                ax2.text(x, y + 1.3, f"{order_num}", fontsize=12, color='red', weight='bold',
                         ha='center', va='center')

        for ax in (ax1, ax2):
            ax.set_xlim(-12, 12)
            ax.set_ylim(-12, 12)
            ax.set_aspect('equal')
            ax.grid(True, linestyle='--', alpha=0.3)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, step_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    def prim_algorithm(self):
        self.print_output("\n" + "=" * 60)
        self.print_output("АЛГОРИТМ ПРИМА: Минимальное остовное дерево")
        self.print_output("=" * 60)

        if not self.graph.nodes():
            self.print_output("Граф пуст!")
            return

        nodes = list(self.graph.nodes())
        n = len(nodes)
        if n == 1:
            self.print_output("Граф состоит из одной вершины. MST не содержит рёбер.")
            return

        # Построение неориентированной весовой матрицы
        node_to_idx = {node: i for i, node in enumerate(nodes)}
        idx_to_node = {i: node for node, i in node_to_idx.items()}
        INF = float('inf')
        adj_matrix = [[INF] * n for _ in range(n)]

        for u, v, data in self.graph.edges(data=True):
            i, j = node_to_idx[u], node_to_idx[v]
            weight = data.get('weight', 1.0)
            if weight < adj_matrix[i][j]:
                adj_matrix[i][j] = weight
                adj_matrix[j][i] = weight  # симметрия для неориентированного графа

        # Проверка связности
        visited = set()
        stack = [nodes[0]]
        visited.add(nodes[0])
        while stack:
            u = stack.pop()
            u_idx = node_to_idx[u]
            for v_idx in range(n):
                if adj_matrix[u_idx][v_idx] != INF and idx_to_node[v_idx] not in visited:
                    visited.add(idx_to_node[v_idx])
                    stack.append(idx_to_node[v_idx])

        if len(visited) != n:
            self.print_output("Ошибка: граф несвязный! Алгоритм Прима применим только к связным графам.")
            return

        self.print_output("\n→ Граф корректен: связный, неориентированный, взвешенный.")
        self.print_output(f"Вершины: {sorted(nodes)}")
        self.print_output(f"Количество вершин: {n}")

        #Инициализация
        key = [INF] * n  # key[i] — минимальный вес ребра для подключения вершины i
        frt = [-1] * n  # frt[i] — предок вершины i в MST (-1 = нет предка)
        in_mst = [False] * n  # включена ли вершина в дерево

        # Начинаем с первой вершины
        start_idx = 0
        key[start_idx] = 0
        frt[start_idx] = -1

        self.print_output(f"\n→ Инициализация:")
        self.print_output(f"  Начальная вершина: {nodes[start_idx]}")
        self.print_output(f"  key = {[f'{x:.1f}' if x != INF else '∞' for x in key]}")
        self.print_output(
            f"  ftr = {[(idx_to_node[i] if frt[i] != -1 else '—') if i < len(frt) else '?' for i in range(n)]}")
        self.print_output(f"  in_mst = {in_mst}")

        total_weight = 0
        mst_edges = []
        order_of_addition = {}

        #Основной цикл
        for step in range(n):
            self.print_output(f"\n→ Шаг {step + 1}/{n}:")

            # Найти u из Q с минимальным key[u]
            u = -1
            min_key = INF
            for v in range(n):
                if not in_mst[v] and key[v] < min_key:
                    min_key = key[v]
                    u = v

            if u == -1:
                self.print_output("Нет доступных вершин — остановка.")
                break

            # добавляем u в MST
            in_mst[u] = True
            total_weight += key[u]
            current_vertex = idx_to_node[u]
            order_of_addition[current_vertex] = step + 1

            if frt[u] != -1:
                parent_vertex = idx_to_node[frt[u]]
                weight = adj_matrix[frt[u]][u]
                mst_edges.append((parent_vertex, current_vertex, weight))
                self.print_output(f"  Выбрана вершина: {current_vertex}")
                self.print_output(f"  Добавлено ребро: {parent_vertex} — {current_vertex} (вес = {weight})")
            else:
                self.print_output(f"  Выбрана начальная вершина: {current_vertex}")

            # Обновление ключей соседей
            updated = []
            for v in range(n):
                if adj_matrix[u][v] != INF and not in_mst[v]:
                    old_key = key[v]
                    if adj_matrix[u][v] < key[v]:
                        key[v] = adj_matrix[u][v]
                        frt[v] = u
                        updated.append((idx_to_node[v], old_key, key[v]))

            # Вывод состояния после обновления
            self.print_output(f"  Текущее дерево включает: {[idx_to_node[i] for i in range(n) if in_mst[i]]}")
            self.print_output(f"  key = {[f'{x:.1f}' if x != INF else '∞' for x in key]}")
            self.print_output(
                f"  frt = {[(idx_to_node[frt[i]] if frt[i] != -1 else '—') if in_mst[i] or key[i] != INF else '—' for i in range(n)]}")
            if updated:
                self.print_output("  Обновлены ключи:")
                for v_name, old_k, new_k in updated:
                    old_str = f"{old_k:.1f}" if old_k != INF else "∞"
                    self.print_output(f"    {v_name}: {old_str} → {new_k:.1f}")
            else:
                self.print_output("  Нет обновлений ключей.")

        #
        self.print_output(f"\n" + "-" * 50)
        self.print_output("РЕЗУЛЬТАТ АЛГОРИТМА ПРИМА")
        self.print_output("-" * 50)
        self.print_output(f"Минимальное остовное дерево содержит {len(mst_edges)} рёбер:")
        for i, (u, v, w) in enumerate(mst_edges, 1):
            self.print_output(f"  {i}. {u} — {v} (вес = {w})")
        self.print_output(f"\nОбщая стоимость MST: {total_weight:.2f}")

        self.visualize_mst_side_by_side(mst_edges, order_of_addition)

    def a_star_algorithm(self):
        self.print_output("\n" + "=" * 60)
        self.print_output("АЛГОРИТМ A*: Поиск кратчайшего пути")
        self.print_output("=" * 60)

        if not self.graph.nodes():
            self.print_output("Граф пуст!")
            return

        nodes = list(self.graph.nodes())
        if len(nodes) == 1:
            self.print_output("Граф содержит только одну вершину.")
            return

        # Обеспечиваем наличие позиций
        if self.pos is None:
            self.pos = {}
        for node in nodes:
            if node not in self.pos:
                self.pos[node] = (np.random.uniform(-10, 10), np.random.uniform(-10, 10))

        # Выбор вершин
        start_node = self.select_vertex_dialog("Выберите стартовую вершину")
        if start_node is None:
            return
        if start_node not in self.graph:
            self.print_output(f"Ошибка: вершина '{start_node}' не существует.")
            return

        goal_node = self.select_vertex_dialog("Выберите целевую вершину")
        if goal_node is None:
            return
        if goal_node not in self.graph:
            self.print_output(f"Ошибка: вершина '{goal_node}' не существует.")
            return

        if start_node == goal_node:
            self.print_output(f"\nСтарт и цель совпадают: {start_node}")
            self.visualize_a_star_path([start_node], start_node, goal_node, 0.0)
            return

        # Проверка на отрицательные веса
        has_negative = any(data.get('weight', 1.0) < 0 for _, _, data in self.graph.edges(data=True))
        if has_negative:
            self.print_output("Внимание: в графе есть рёбра с отрицательными весами.")
            self.print_output("   A* может не найти оптимальный путь!")

        # Эвристика
        def heuristic(node):
            x1, y1 = self.pos[node]
            x2, y2 = self.pos[goal_node]
            return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        # Инициализация
        g_score = {node: float('inf') for node in nodes}
        f_score = {node: float('inf') for node in nodes}
        parent = {node: None for node in nodes}

        g_score[start_node] = 0
        f_score[start_node] = heuristic(start_node)

        open_set = set([start_node])
        closed_set = set()

        self.print_output(f"\n→ Поиск кратчайшего пути от '{start_node}' до '{goal_node}'")
        self.print_output(f"Эвристика h(v) = евклидово расстояние до '{goal_node}'")
        self.print_output("\n" + "-" * 80)
        self.print_output(
            f"{'Шаг':<4} | {'Текущая':<10} | {'g(текущей)':<10} | {'f(текущей)':<10} | {'Открытое множество (вершина: f)':<40}")
        self.print_output("-" * 80)

        step = 0
        found = False

        while open_set:
            # Выбираем вершину с минимальным f_score
            current = min(open_set, key=lambda node: f_score[node])
            open_set.remove(current)
            closed_set.add(current)

            step += 1
            current_f = f_score[current]
            current_g = g_score[current]

            open_str = ", ".join([f"{n}: {f_score[n]:.2f}" for n in sorted(open_set, key=lambda x: f_score[x])])
            if not open_str:
                open_str = "∅"

            self.print_output(f"{step:<4} | {current:<10} | {current_g:<10.2f} | {current_f:<10.2f} | {open_str}")

            if current == goal_node:
                found = True
                break

            for neighbor in self.graph.successors(current):
                if neighbor in closed_set:
                    continue

                weight = self.graph[current][neighbor].get('weight', 1.0)
                tentative_g = g_score[current] + weight

                if tentative_g < g_score[neighbor]:
                    parent[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor)
                    open_set.add(neighbor)

                    self.print_output(
                        f"      → Обновление {neighbor}: g={tentative_g:.2f}, f={f_score[neighbor]:.2f} (через {current})")

        if found:
            path = []
            current = goal_node
            while current is not None:
                path.append(current)
                current = parent[current]
            path.reverse()

            total_cost = g_score[goal_node]

            self.print_output("\n" + "-" * 50)
            self.print_output("РЕЗУЛЬТАТ АЛГОРИТМА A*")
            self.print_output("-" * 50)
            self.print_output(f"Кратчайший путь: {' → '.join(path)}")
            self.print_output(f"Стоимость пути: {total_cost:.2f}")
            self.print_output(f"Количество шагов: {step}")

            self.visualize_a_star_path(path, start_node, goal_node, total_cost)
        else:
            self.print_output("\nПуть не найден!")
            self.print_output(f"Вершина '{goal_node}' недостижима из '{start_node}'.")

    def select_vertex_dialog(self, title_text):
        """диалоговое окно для выбора пути"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title_text)
        dialog.geometry("300x250")
        dialog.transient(self.root)
        dialog.grab_set()

        label = ttk.Label(dialog, text=title_text + ":", font=("Arial", 11))
        label.pack(pady=10)

        combo = ttk.Combobox(dialog, values=sorted(self.graph.nodes()), state="readonly", width=25)
        combo.pack(pady=10)
        combo.set("")

        result = {"vertex": None}

        def on_ok():
            val = combo.get()
            if not val:
                messagebox.showwarning("Ошибка", "Выберите вершину!", parent=dialog)
                return
            result["vertex"] = val
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=15)
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        self.root.wait_window(dialog)
        return result["vertex"]

    def visualize_a_star_path(self, path, start, goal, cost):
        step_window = tk.Toplevel(self.root)
        step_window.title("Алгоритм A* — найденный путь")
        step_window.geometry("1500x700")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=100)

        pos = {node: self.pos[node] for node in self.pos if node in self.graph}

        # Левая панель: исходный граф
        self._draw_graph_on_ax(ax1, self.graph, pos, "Исходный граф")

        # Правая панель: выделенный путь
        self._draw_graph_on_ax(ax2, self.graph, pos, f"Путь A*: {start} → {goal}\nСтоимость: {cost:.2f}")

        # Множество рёбер пути (для ориентированного графа)
        path_edges = set()
        for i in range(len(path) - 1):
            path_edges.add((path[i], path[i + 1]))

        # Перерисовываем рёбра: путь — жирный зелёный
        for u, v, data in self.graph.edges(data=True):
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            dx, dy = x2 - x1, y2 - y1
            length = np.hypot(dx, dy)
            shrink = 1.1 if length > 0 else 0
            if length > 0:
                x2_adj = x1 + dx * (length - shrink) / length
                y2_adj = y1 + dy * (length - shrink) / length
            else:
                x2_adj, y2_adj = x2, y2

            color = 'green' if (u, v) in path_edges else 'gray'
            linewidth = 3.0 if (u, v) in path_edges else 1.5
            alpha = 1.0 if (u, v) in path_edges else 0.6

            if self.graph.is_directed():
                ax2.annotate("", xy=(x2_adj, y2_adj), xytext=(x1, y1),
                             arrowprops=dict(arrowstyle="->", color=color, linewidth=linewidth, alpha=alpha))
            else:
                ax2.plot([x1, x2], [y1, y2], color=color, linewidth=linewidth, alpha=alpha)

            # Подпись веса
            weight = data.get('weight', 1.0)
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            offset_x = -0.4 * dy / (length + 1e-6)
            offset_y = 0.4 * dx / (length + 1e-6)
            ax2.text(mid_x + offset_x, mid_y + offset_y, f"{weight:.1f}",
                     fontsize=10, ha='center', va='center',
                     bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="none", alpha=0.8))

        # Вершины
        for node, (x, y) in pos.items():
            color = 'lightgreen' if node in path else 'lightblue'
            edge_color = 'darkgreen' if node == start else ('red' if node == goal else 'black')
            circle = plt.Circle((x, y), radius=1.1, color=color, alpha=0.9, ec=edge_color, linewidth=2.5)
            ax2.add_patch(circle)
            ax2.text(x, y, node, fontsize=9, fontweight='bold', ha='center', va='center')

        for ax in (ax1, ax2):
            ax.set_xlim(-12, 12)
            ax.set_ylim(-12, 12)
            ax.set_aspect('equal')
            ax.grid(True, linestyle='--', alpha=0.3)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, step_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    def dinic_algorithm(self):
        self.print_output("\n" + "=" * 60)
        self.print_output("АЛГОРИТМ ДИНИЦА: Максимальный поток")
        self.print_output("=" * 60)
        self.print_output("Реализуйте этот метод в своей части работы!")
        self.print_output("Для работы алгоритма нужны источник и сток.")

    def johnson_algorithm(self):
        self.print_output("\n" + "=" * 60)
        self.print_output("АЛГОРИТМ ДЖОНСОНА: Поиск всех циклов")
        self.print_output("=" * 60)
        self.print_output("Реализуйте этот метод в своей части работы!")
        self.print_output("Алгоритм находит все элементарные циклы в графе.")


def main():
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()