import copy
import heapq

from ..dataclass import Result
from ..utils import adjacency_list_to_networkx


class JohnsonSolver:
    def __init__(self, n, graph):
        self.graph = graph
        self.n = n
        self.result = Result()
        self.step_count = 0
        self.node_labels = list(range(n))

    def _log(self, title: str, data: str = "", graph=None):
        self.step_count += 1
        nx_graph = adjacency_list_to_networkx(self.graph if not graph else graph, self.node_labels)
        self.result.add_step(f"{self.step_count}. {title}", nx_graph, data)

    def bellman_ford(self, graph, n, src):
        dist = [float("inf")] * n
        dist[src] = 0

        table_rows = []
        vertices = [f"V{i}" for i in range(n)]
        header = ["Итер."] + vertices
        table_rows.append(header)

        row0 = ["0"] + [f"{d:.1f}" if d != float('inf') else "∞" for d in dist]
        table_rows.append(row0)

        for iteration in range(1, n):
            prev_dist = dist.copy()

            for _ in range(n - 1):
                for u in range(n):
                    for v, weight in graph[u]:
                        if dist[u] != float("inf") and dist[u] + weight < dist[v]:
                            dist[v] = dist[u] + weight

            row = [str(iteration)]
            for j in range(n):
                if dist[j] == prev_dist[j]:
                    row.append(f"{dist[j]:.1f}")
                else:
                    row.append(f"{dist[j]:.1f}*")
            table_rows.append(row)

            if dist == prev_dist:
                break

        table_str = self._format_table(table_rows)
        return dist, table_str

    def _format_table(self, rows):
        if not rows:
            return ""

        col_widths = [0] * len(rows[0])
        for row in rows:
            for j, cell in enumerate(row):
                col_widths[j] = max(col_widths[j], len(str(cell)))

        lines = []
        for i, row in enumerate(rows):
            line_parts = []
            for j, cell in enumerate(row):
                if j == 0:
                    line_parts.append(str(cell).ljust(col_widths[j]))
                else:
                    line_parts.append(str(cell).rjust(col_widths[j]))
            lines.append(" | ".join(line_parts))

            if i == 0:
                total_width = sum(col_widths) + 3 * (len(col_widths) - 1)
                lines.append("-" * total_width)

        return "\n".join(lines)

    def dijkstra(self, graph, src, n):
        dist = [float("inf")] * n
        dist[src] = 0
        min_heap = [(0, src)]
        while min_heap:
            u_distance, u = heapq.heappop(min_heap)
            for v, weight in graph[u]:
                if u_distance + weight < dist[v]:
                    dist[v] = u_distance + weight
                    heapq.heappush(min_heap, (dist[v], v))
        return dist

    def update_graph(self, graph):
        self.graph = copy.copy(graph)
        self.node_labels = list(range(len(graph)))

    def johnsons_algorithm(self):
        self._log("1. Исходный граф", f"Количество вершин: {self.n}")

        new_graph = [[] for _ in range(self.n + 1)]
        for u in range(self.n):
            new_graph[u].extend(self.graph[u])
            new_graph[self.n].append((u, 0))

        self.update_graph(new_graph)
        self._log("2. Добавление фиктивной вершины S",
                  f"Добавлена вершина S (индекс {self.n}")

        h, bf_table = self.bellman_ford(new_graph, self.n + 1, self.n)
        self._log("3. Беллман-Форд из вершины S",
                  f"Таблица итераций:\n\n{bf_table}\n\n" +
                  f"Потенциалы h(v):\n" +
                  "\n".join([f"  h(V{i}) = {h[i]:.1f}" for i in range(self.n)]))

        h_formula = "Формула перевзвешивания:\n"
        h_formula += "ω'(u,v) = ω(u,v) + h(u) - h(v)\n\n"
        h_formula += "Пересчёт рёбер:\n"

        reweighted_graph = [[] for _ in range(self.n)]
        for u in range(self.n):
            for v, weight in self.graph[u]:
                new_weight = weight + h[u] - h[v]
                reweighted_graph[u].append((v, new_weight))
                h_formula += f"V{u}→V{v}: {weight:.1f} + {h[u]:.1f} - {h[v]:.1f} = {new_weight:.1f}\n"

        self.update_graph(reweighted_graph)
        self._log("4. Перевзвешивание рёбер", h_formula)

        self._log("5. Граф с неотрицательными весами",
                  "Все рёбра теперь имеют неотрицательные веса")

        distances = []
        for u in range(self.n):
            dist = self.dijkstra(reweighted_graph, u, self.n)
            true_dist = [d + h[v] - h[u] for v, d in enumerate(dist)]
            distances.append(true_dist)

            dist_str = ", ".join([
                f"V{v}:{d:.1f}" if d != float('inf') else f"V{v}:∞"
                for v, d in enumerate(true_dist)
            ])
            self._log(f"6.{u + 1}. Дейкстра из V{u}",
                      f"Результаты:\n[{dist_str}]")

        matrix_str = "Матрица кратчайших расстояний:\n\n"
        matrix_str += "     " + " ".join([f"V{i}".center(6) for i in range(self.n)]) + "\n"
        matrix_str += "    " + "-" * (self.n * 7) + "\n"

        for u in range(self.n):
            row = f"V{u} | "
            for v in range(self.n):
                d = distances[u][v]
                if d == float("inf"):
                    row += " ∞".center(6)
                else:
                    row += f"{d:.1f}".center(6)
            matrix_str += row + "\n"

        self._log("7. Итоговая матрица расстояний", matrix_str)

        return distances


