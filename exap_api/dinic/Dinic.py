from collections import deque
from typing import List, Tuple
import networkx as nx

from exap_api.dataclass import Result
from exap_api.dinic.dataclass import Edge
from exap_api.utils import convert_to_networkx, networkx_to_dinic_format


class DinicSolver:

    def __init__(self, n: int, graph=None):
        self.n = n
        if graph:
            self.graph = graph
        else:
            self.graph: List[List[Edge]] = [[] for _ in range(n)]

        self.result = Result()
        self.node_labels = list(range(n))
        self.step_count = 0

    def _log(self, title: str, data: str = ""):
        self.step_count += 1
        nx_graph = convert_to_networkx(self.graph, self.node_labels)
        self.result.add_step(f"{self.step_count}. {title}", nx_graph, data)

    def add_edge(self, from_: int, to: int, capacity: int) -> None:
        forward = Edge(to, len(self.graph[to]), capacity)
        backward = Edge(from_, len(self.graph[from_]), 0)

        self.graph[from_].append(forward)
        self.graph[to].append(backward)

    def max_flow(self, s: int, t: int) -> int:
        self._log("Начало алгоритма", f"Исток: {s}, Сток: {t}")

        flow = 0
        INF = 10 ** 18

        phase = 1

        while self._bfs(s, t):
            self._log(f"Фаза {phase}", f"Строим слоистую сеть")
            self.it = [0] * self.n
            dfs_count = 0
            while True:
                pushed = self._dfs(s, t, INF)
                dfs_count += 1
                if pushed == 0:
                    break
                self._log(f"Поток {dfs_count}", f"Найден поток: {pushed}")
                flow += pushed
            self._log(f"Конец фазы {phase}", f"Суммарный поток: {flow}")
        self._log("Конец алгоритма", f"Максимальный поток: {flow}")
        return flow

    def _bfs(self, s: int, t: int) -> bool:
        """слоистая сеть"""
        self.level = [-1] * self.n
        queue = deque([s])
        self.level[s] = 0
        s = "Начало BFS" + "\n   " + f"Исток: {s}"
        # self._log("Начало BFS", f"Исток: {s}")

        while queue:
            v = queue.popleft()
            for edge in self.graph[v]:
                if edge.capacity > 0 and self.level[edge.to] < 0:
                    self.level[edge.to] = self.level[v] + 1
                    queue.append(edge.to)
                    s += "\n" + f"BFS: {v} → {edge.to}" + "\n   " + f"Уровень {self.level[edge.to]}, capacity: {edge.capacity}"
                    # self._log(f"BFS: {v} → {edge.to}",
                    #           f"У/ровень {self.level[edge.to]}, capacity: {edge.capacity}")
        reachable = self.level[t] >= 0
        s += "\n" + "Конец BFS" + "\n    " + f"Сток достижим: {reachable}"
        self._log("BFS", s)
        # self._log("Конец BFS", f"Сток достижим: {reachable}")
        return self.level[t] >= 0

    def _dfs(self, v: int, t: int, f: int) -> int:
        """блокирующий поток """
        if v == t:
            return f
        s = ""

        for i in range(self.it[v], len(self.graph[v])):
            self.it[v] = i
            edge = self.graph[v][i]

            if edge.capacity > 0 and self.level[v] + 1 == self.level[edge.to]:
                s = "\n" + f"DFS проверяет {v} → {edge.to}" + "\n    " + \
                    f"Capacity: {edge.capacity}"
                # self._log(f"DFS проверяет {v} → {edge.to}",
                #           f"Capacity: {edge.capacity}")
                pushed = self._dfs(edge.to, t, min(f, edge.capacity))
                if pushed > 0:
                    # Обновляем остаточные ёмкости
                    edge.capacity -= pushed
                    self.graph[edge.to][edge.rev].capacity += pushed
                    s += "\n" + f"Обновление ёмкости {v} → {edge.to}" + "\n     " + \
                         f"-{pushed}, новая capacity: {edge.capacity}"
                    # self._log(f"Обновление ёмкости {v} → {edge.to}",
                    #           f"-{pushed}, новая capacity: {edge.capacity}")
                    return pushed

        self._log("DFS", s)

        return 0


if __name__ == '__main__':
    g = nx.DiGraph()
    g.add_node(0)
    g.add_node(1)
    g.add_node(2)
    g.add_node(3)

    g.add_edge(0, 1, capacity=1)
    g.add_edge(0, 2, capacity=1)
    g.add_edge(1, 2, capacity=1)
    g.add_edge(1, 3, capacity=1)
    g.add_edge(2, 3, capacity=1)

    new_g, labels = networkx_to_dinic_format(g)

    s = DinicSolver(len(new_g), new_g)
    s.max_flow(0, 3)

    print(s.max_flow(0, 3))
