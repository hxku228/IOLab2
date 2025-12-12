from dataclasses import dataclass, Field

import networkx as nx



class Edge:

    def __init__(self, to: int, rev: int, capacity: int):
        self.to = to
        self.rev = rev  # индекс обратного ребра в _g[to]
        self.capacity = capacity

    def __str__(self):
        return f"EDGE( to= {self.to}, rev= {self.rev}, cap= {self.capacity})"
