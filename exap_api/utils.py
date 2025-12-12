from typing import List, Tuple, Dict

import networkx as nx

from exap_api.dinic.dataclass import Edge


def convert_to_networkx(adjacency: List[List[Edge]],
                        node_labels: List[str] = None,
                        include_capacity: bool = True) -> nx.DiGraph:
    """
    Конвертирует внутреннее представление графа (список списков Edge) в NetworkX DiGraph.

    Args:
        adjacency: Список списков ребер [from_idx][edge_idx] -> Edge
        node_labels: Список меток для вершин (если None, используются индексы)
        include_capacity: Включать ли capacity как атрибут рёбер

    Returns:
        NetworkX DiGraph
    """
    G = nx.DiGraph()
    n = len(adjacency)

    # Добавляем вершины
    if node_labels is not None and len(node_labels) >= n:
        # Используем переданные метки
        for i in range(n):
            G.add_node(node_labels[i])
        label_map = node_labels
    else:
        # Используем индексы как метки
        for i in range(n):
            G.add_node(i)
        label_map = list(range(n))

    # Добавляем рёбра
    for u_idx in range(n):
        for edge in adjacency[u_idx]:
            v_idx = edge.to

            # Добавляем только если capacity > 0 (активные рёбра в остаточном графе)
            if edge.capacity > 0:
                u_label = label_map[u_idx]
                v_label = label_map[v_idx]

                if include_capacity:
                    G.add_edge(u_label, v_label, capacity=edge.capacity)
                else:
                    G.add_edge(u_label, v_label)

    return G


def convert_with_flow(adjacency: List[List[Edge]],
                      original_capacities: dict = None,
                      node_labels: List[str] = None) -> nx.DiGraph:
    """
    Конвертирует граф с дополнительной информацией о потоке.

    Args:
        adjacency: Текущий остаточный граф
        original_capacities: Словарь исходных пропускных способностей {(u, v): capacity}
        node_labels: Список меток для вершин

    Returns:
        NetworkX DiGraph с атрибутами потока
    """
    G = convert_to_networkx(adjacency, node_labels, include_capacity=True)

    # Если есть информация об исходных пропускных способностях, добавляем поток
    if original_capacities:
        for u, v in G.edges():
            key = (u, v)
            if key in original_capacities:
                original_cap = original_capacities[key]
                residual_cap = G[u][v]['weight']
                flow = original_cap - residual_cap

                # Добавляем атрибуты
                G[u][v]['original_capacity'] = original_cap
                G[u][v]['flow'] = max(0, flow)  # поток не может быть отрицательным

    return G


def networkx_to_adjacency(digraph: nx.DiGraph,
                          capacity_attr: str = 'weight',
                          default_capacity: int = 1) -> Tuple[List[List[Edge]], Dict]:
    """
    Конвертирует NetworkX DiGraph в adjacency список (список списков Edge).

    Args:
        digraph: Ориентированный граф NetworkX
        capacity_attr: Имя атрибута, содержащего пропускную способность
        default_capacity: Пропускная способность по умолчанию

    Returns:
        Кортеж (adjacency, node_mapping)
        - adjacency: List[List[Edge]] - представление графа
        - node_mapping: Dict - mapping оригинальных меток -> индексы

    Raises:
        ValueError: Если граф пустой
    """
    if len(digraph.nodes()) == 0:
        raise ValueError("Граф не может быть пустым")

    # Создаем mapping узлов
    nodes = list(digraph.nodes())
    node_mapping = {node: i for i, node in enumerate(nodes)}
    n = len(nodes)

    # Инициализируем adjacency список
    adjacency: List[List[Edge]] = [[] for _ in range(n)]

    # Сначала собираем все прямые рёбра
    edges_data = []
    for u, v, data in digraph.edges(data=True):
        idx_u = node_mapping[u]
        idx_v = node_mapping[v]
        capacity = data.get(capacity_attr, default_capacity)
        edges_data.append((idx_u, idx_v, capacity))

    # Добавляем рёбра и создаем обратные
    reverse_edges_info = {}  # Для отслеживания reverse индексов

    for from_idx, to_idx, capacity in edges_data:
        # Индекс для обратного ребра (пока неизвестен)
        forward_rev_index = len(adjacency[to_idx])

        # Создаем прямое ребро
        forward_edge = Edge(to=to_idx, rev=forward_rev_index, capacity=capacity)
        adjacency[from_idx].append(forward_edge)

        # Сохраняем информацию для обратного ребра
        reverse_key = (to_idx, from_idx)
        if reverse_key not in reverse_edges_info:
            reverse_edges_info[reverse_key] = []
        reverse_edges_info[reverse_key].append((len(adjacency[from_idx]) - 1, capacity))

    # Добавляем обратные рёбра (с нулевой ёмкостью)
    for (from_idx, to_idx), forward_info in reverse_edges_info.items():
        for forward_index, _ in forward_info:
            # Индекс для обратного ребра
            reverse_rev_index = forward_index

            # Создаем обратное ребро
            reverse_edge = Edge(to=to_idx, rev=reverse_rev_index, capacity=0)
            adjacency[from_idx].append(reverse_edge)

            # Обновляем rev индекс в прямом ребре
            adjacency[to_idx][reverse_rev_index].rev = len(adjacency[from_idx]) - 1

    # Для рёбер, у которых нет обратных, создаем их отдельно
    for from_idx in range(n):
        for edge_idx, edge in enumerate(adjacency[from_idx]):
            # Проверяем, есть ли обратное ребро
            reverse_exists = False
            for rev_edge in adjacency[edge.to]:
                if rev_edge.to == from_idx and rev_edge.rev == edge_idx:
                    reverse_exists = True
                    break

            # Если обратного ребра нет, создаем его
            if not reverse_exists:
                # Создаем обратное ребро
                reverse_rev_index = edge_idx
                reverse_edge = Edge(to=from_idx, rev=reverse_rev_index, capacity=0)
                adjacency[edge.to].append(reverse_edge)

                # Обновляем rev индекс в прямом ребре
                edge.rev = len(adjacency[edge.to]) - 1

    return adjacency, node_mapping


def networkx_to_dinic_format(digraph: nx.DiGraph) -> Tuple[List[List[Edge]], List[str]]:
    """
    Конвертирует NetworkX DiGraph в формат для алгоритма Диница.

    Args:
        digraph: Ориентированный граф NetworkX

    Returns:
        Кортеж (adjacency, node_labels)
    """
    adjacency, node_mapping = networkx_to_adjacency(digraph)

    # Создаем обратный mapping для меток
    node_labels: list[str | None] = [None] * len(node_mapping)
    for original_label, index in node_mapping.items():
        node_labels[index] = original_label

    return adjacency, node_labels


# ===================================


def networkx_to_adjacency_list(digraph: nx.DiGraph,
                               weight_attr: str = 'weight',
                               default_weight: int = 1) -> list:
    """
    Конвертирует NetworkX DiGraph в список смежности.

    Формат: graph = [
        [(1, 3), (2, 8)],  # вершина 0 → (1, вес 3), (2, вес 8)
        [(3, -2)],         # вершина 1 → (3, вес -2)
        [(1, 4)],          # вершина 2 → (1, вес 4)
        []                 # вершина 3 → нет исходящих рёбер
    ]

    Args:
        digraph: Ориентированный граф NetworkX
        weight_attr: Имя атрибута с весом ребра
        default_weight: Вес по умолчанию если атрибут не указан

    Returns:
        Список смежности в указанном формате
    """
    # Получаем все вершины и сортируем их (если это числа или можно сравнивать)
    nodes = sorted(digraph.nodes())

    # Создаем mapping: node -> index
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    # Инициализируем пустой список смежности
    adjacency_list = [[] for _ in range(len(nodes))]

    # Заполняем список смежности
    for u, v, data in digraph.edges(data=True):
        idx_u = node_to_idx[u]
        idx_v = node_to_idx[v]

        # Получаем вес ребра
        weight = data.get(weight_attr, default_weight)

        # Добавляем в список смежности
        adjacency_list[idx_u].append((idx_v, weight))

    return adjacency_list


# Альтернативная версия (сохраняет оригинальные идентификаторы вершин)
def networkx_to_adjacency_list_with_labels(digraph: nx.DiGraph,
                                           weight_attr: str = 'weight',
                                           default_weight: int = 1) -> tuple:
    """
    Конвертирует NetworkX DiGraph в список смежности с метками вершин.

    Returns:
        Кортеж (adjacency_list, labels)
        adjacency_list: список смежности
        labels: список оригинальных меток вершин
    """
    nodes = list(digraph.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    adjacency_list = [[] for _ in range(len(nodes))]

    for u, v, data in digraph.edges(data=True):
        idx_u = node_to_idx[u]
        idx_v = node_to_idx[v]
        weight = data.get(weight_attr, default_weight)
        adjacency_list[idx_u].append((idx_v, weight))

    return adjacency_list, nodes


def adjacency_list_to_networkx(adjacency_list: list,
                               labels: list = None,
                               weight_attr: str = 'weight') -> nx.DiGraph:
    """
    Конвертирует список смежности в NetworkX DiGraph.

    Args:
        adjacency_list: Список смежности в формате [(to, weight), ...]
        labels: Список меток вершин (если None, используются индексы)
        weight_attr: Имя атрибута для веса ребра

    Returns:
        NetworkX DiGraph
    """
    digraph = nx.DiGraph()
    n = len(adjacency_list)

    # Создаем метки вершин
    if labels is None:
        labels = list(range(n))
    elif len(labels) != n:
        raise ValueError(f"Количество меток ({len(labels)}) должно совпадать "
                         f"с количеством вершин ({n})")

    # Добавляем вершины
    for label in labels:
        digraph.add_node(label)

    # Добавляем рёбра
    for i, neighbors in enumerate(adjacency_list):
        u = labels[i]
        for neighbor in neighbors:
            if len(neighbor) == 2:
                v_idx, weight = neighbor
                v = labels[v_idx]
                digraph.add_edge(u, v, **{weight_attr: weight})
            else:
                # Если только индекс вершины без веса
                v_idx = neighbor[0]
                v = labels[v_idx]
                digraph.add_edge(u, v)

    return digraph


# Упрощенная версия (только для числовых вершин)
def adjacency_list_to_networkx_simple(adjacency_list: list,
                                      weight_attr: str = 'weight') -> nx.DiGraph:
    """
    Упрощенная конвертация (вершины = индексы).
    """
    digraph = nx.DiGraph()

    # Добавляем вершины
    for i in range(len(adjacency_list)):
        digraph.add_node(i)

    # Добавляем рёбра
    for i, neighbors in enumerate(adjacency_list):
        for neighbor in neighbors:
            if len(neighbor) == 2:
                v, weight = neighbor
                digraph.add_edge(i, v, **{weight_attr: weight})
            else:
                v = neighbor[0]
                digraph.add_edge(i, v)

    return digraph