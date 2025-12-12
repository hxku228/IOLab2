from dataclasses import dataclass, Field

import networkx as nx


@dataclass
class Step:
    title: str
    graph: nx.DiGraph
    data: str



class Result:
    def __init__(self):
        self.steps: list[Step] = []
        self._current_step_id = 0

    def getNextStep(self):
        if self._current_step_id < len(self.steps):
            self._current_step_id += 1
        return self.steps[self._current_step_id]

    def getPreviousStep(self):
        if self._current_step_id > 0:
            self._current_step_id -= 1
        return self.steps[self._current_step_id]

    def add_step(self, title, graph, data):
        self.steps.append(Step(title, graph, data))

