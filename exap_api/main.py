import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
import json
import numpy as np

from .dataclass import Result, Step
from .dinic import DinicSolver
from .johnson import JohnsonSolver
from .utils import networkx_to_dinic_format, networkx_to_adjacency_list_with_labels


class ExapApi:
    def __init__(self, root, graph):
        self.root = root
        self.graph = graph
        self.dinic_input_window = None
        self.input_window = None

    def johnson(self):

        new_g, labels = networkx_to_adjacency_list_with_labels(self.graph)

        solver = JohnsonSolver(len(new_g), new_g)
        solver.johnsons_algorithm()
        self.show_result(solver.result)

    def dinic(self):
        self.input_window = tk.Toplevel(self.root)
        self.input_window.title("Алгоритм Диница")
        self.input_window.geometry("200x150")

        source_label = ttk.Label(self.input_window, text="Исток (Source):")
        source_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        self.source_entry = ttk.Entry(self.input_window, width=10)
        self.source_entry.grid(row=0, column=1, padx=10, pady=10)
        self.source_entry.insert(0, "0")

        sink_label = ttk.Label(self.input_window, text="Сток (Sink):")
        sink_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

        self.sink_entry = ttk.Entry(self.input_window, width=10)
        self.sink_entry.grid(row=1, column=1, padx=10, pady=10)
        self.sink_entry.insert(0, "1")

        # Кнопка расчета
        calculate_btn = ttk.Button(self.input_window, text="Найти максимальный поток",
                                   command=self.calculate_dinic)
        calculate_btn.grid(row=2, column=0, columnspan=2, pady=20)

        # Центрируем окно
        self.input_window.update_idletasks()
        x = (self.input_window.winfo_screenwidth() - self.input_window.winfo_width()) // 2
        y = (self.input_window.winfo_screenheight() - self.input_window.winfo_height()) // 2
        self.input_window.geometry(f"+{x}+{y}")

    def calculate_dinic(self):
        new_g, labels = networkx_to_dinic_format(self.graph)

        solver = DinicSolver(len(new_g), new_g)
        solver.max_flow(int(self.source_entry.get()), int(self.sink_entry.get()))
        self.show_result(solver.result)

    def show_result(self, result: Result):

        self.min_result = result
        self.current_step_index = 0

        result_window = tk.Toplevel(self.root)
        result_window.title("Результат минимизации")
        result_window.geometry("1200x700")

        self.result_window = result_window

        left_frame = tk.Frame(result_window, width=500, bg='lightgray')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)

        right_frame = tk.Frame(result_window, bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Сохраняем ссылки на фреймы
        self.result_left_frame = left_frame
        self.result_right_frame = right_frame

        output_frame = ttk.Frame(left_frame)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создаем прокручиваемое текстовое поле на весь экран
        self.output_text = scrolledtext.ScrolledText(output_frame, font=('Courier', 9))
        self.output_text.pack(fill=tk.BOTH, expand=True)

        steps_frame = tk.LabelFrame(left_frame, text="Шаги детерминации", bg='lightgray')
        steps_frame.pack(fill=tk.X, pady=10, padx=5)

        tk.Button(steps_frame, text="Назад", command=self.prev_result_step,
                  bg='lightyellow').grid(row=0, column=0, padx=5, pady=10)
        tk.Button(steps_frame, text="Вперед", command=self.next_result_step,
                  bg='lightyellow').grid(row=0, column=1, padx=5, pady=10)

        self.table_container = tk.Frame(self.result_left_frame, bg='lightgray')
        self.table_container.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)

        self.graph_container = tk.Frame(self.result_right_frame, bg='lightgray')
        self.graph_container.pack(fill=tk.X, expand=True, padx=5, pady=5)

        # Показываем первый шаг
        self.update_result_step()

        # Таблица переходов

    def update_result_step(self):
        """Обновляет отображение текущего шага"""
        # Проверяем границы
        if 0 <= self.current_step_index < len(self.min_result.steps):
            step = self.min_result.steps[self.current_step_index]

            if self.input_window:
                self.input_window.destroy()

            for widget in self.graph_container.winfo_children():
                widget.destroy()
            self.output_text.insert(tk.END, "\n" + step.title + "\n     " + step.data)
            # 6. Создаем новый граф
            self.create_result_graph(self.graph_container, step.graph, step.title)

    def create_result_graph(self, parent, data, title):
        """Создает граф для шага в указанном parent"""
        # if self.fig:
        #     plt.close(self.fig)
        self.fig, ax = plt.subplots(figsize=(10, 10))
        canvas = FigureCanvasTkAgg(self.fig, master=parent)
        canvas.get_tk_widget().pack(fill=tk.TOP, expand=True)

        self.draw_graph(ax, data, title=title)

        self.fig.canvas.draw()

    def next_result_step(self):
        """Следующий шаг"""
        if self.current_step_index < len(self.min_result.steps) - 1:
            self.current_step_index += 1
            self.update_result_step()

    def prev_result_step(self):
        """Предыдущий шаг"""
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self.update_result_step()

    # def show_result_step(self, left_frame, right_frame, step: Step):
    #     g = step.graph
    #
    #     output_frame = ttk.Frame(left_frame)
    #     output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    #
    #     # Создаем прокручиваемое текстовое поле на весь экран
    #     self.output_text = scrolledtext.ScrolledText(output_frame, font=('Courier', 9))
    #     self.output_text.pack(fill=tk.BOTH, expand=True)
    #     self.output_text.insert(tk.END, step.data)
    #
    #     self.graph_frame_result = tk.Frame(right_frame, bg='white')
    #     self.graph_frame_result.pack(fill=tk.BOTH, expand=True)
    #
    #     # Фигура для matplotlib
    #     self.fig_result, self.ax_result = plt.subplots(figsize=(10, 10))
    #     self.canvas_result = FigureCanvasTkAgg(self.fig_result, master=self.graph_frame_result)
    #     self.canvas_result.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    #
    #     self.draw_graph(self.ax_result, g, title=step.title)
    #
    def draw_graph(self, ax, G: nx.DiGraph, title="Визуализация графа"):

        if len(G.nodes()) > 0:
            # Располагаем по кругу
            pos = nx.circular_layout(G)

            # Рисуем узлы
            nx.draw_networkx_nodes(G, pos, node_size=2000,
                                   ax=ax, edgecolors='black', linewidths=2)
            nx.draw_networkx_labels(G, pos, ax=ax, font_weight='bold', font_size=12)

            # Рисуем ребра
            edge_labels = nx.get_edge_attributes(G, 'label')
            # nx.draw_networkx_edges(G, pos, ax=ax, arrows=True,
            #                        arrowstyle='-|>', arrowsize=20,
            #                        edge_color='gray', connectionstyle='arc3,rad=0.1')

            nx.draw_networkx_edges(G, pos, ax=ax, arrows=True,
                                   arrowstyle='-|>', arrowsize=30,
                                   edge_color='gray',
                                   connectionstyle='arc3,rad=0.1',
                                   node_size=1500)

            edge_labels = {}
            for u, v, data in G.edges(data=True):
                # Получаем вес или capacity
                weight = data.get('weight')
                capacity = data.get('capacity')

                if weight is not None:
                    edge_labels[(u, v)] = weight
                elif capacity is not None:
                    edge_labels[(u, v)] = capacity

            # Рисуем метки рёбер
            if edge_labels:
                nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=edge_labels,
                                             font_size=10, bbox=dict(boxstyle="round,pad=0.3",
                                                                     facecolor="white", alpha=0.8))

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axis('off')
        ax.set_aspect('equal')

        # Обновляем canvas
        # self.canvas.draw()
