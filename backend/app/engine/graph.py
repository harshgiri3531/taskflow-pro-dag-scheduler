"""Pure graph utilities: no web framework, no DB. Fully unit-testable."""
from collections import deque
from typing import Dict, List, Set, Tuple


class CycleError(Exception):
    def __init__(self, path: List[str]):
        self.path = path
        super().__init__(f"Cycle detected: {' -> '.join(path)}")


class Graph:
    """Adjacency-list DAG. Nodes are task ids (str)."""

    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, Set[str]] = {}   # predecessor -> {successors}
        self.reverse: Dict[str, Set[str]] = {}  # successor -> {predecessors}

    def add_node(self, node_id: str):
        self.nodes.add(node_id)
        self.edges.setdefault(node_id, set())
        self.reverse.setdefault(node_id, set())

    def remove_node(self, node_id: str):
        for pred in list(self.reverse.get(node_id, [])):
            self.edges[pred].discard(node_id)
        for succ in list(self.edges.get(node_id, [])):
            self.reverse[succ].discard(node_id)
        self.nodes.discard(node_id)
        self.edges.pop(node_id, None)
        self.reverse.pop(node_id, None)

    def add_edge(self, pred: str, succ: str):
        if pred == succ:
            raise CycleError([pred, succ])
        self.add_node(pred)
        self.add_node(succ)
        self.edges[pred].add(succ)
        self.reverse[succ].add(pred)

    def remove_edge(self, pred: str, succ: str):
        self.edges.get(pred, set()).discard(succ)
        self.reverse.get(succ, set()).discard(pred)

    def would_create_cycle(self, pred: str, succ: str) -> Tuple[bool, List[str]]:
        """Check if adding pred->succ creates a cycle, WITHOUT mutating self.
        A cycle forms iff pred is reachable FROM succ (succ can already reach pred)."""
        if pred == succ:
            return True, [pred, succ]
        visited = {succ}
        parent = {succ: None}
        queue = deque([succ])
        while queue:
            cur = queue.popleft()
            if cur == pred:
                path = []
                node = cur
                while node is not None:
                    path.append(node)
                    node = parent[node]
                path.reverse()
                path.append(succ)
                return True, path
            for nxt in self.edges.get(cur, []):
                if nxt not in visited:
                    visited.add(nxt)
                    parent[nxt] = cur
                    queue.append(nxt)
        return False, []

    def topological_order(self) -> List[str]:
        """Kahn's algorithm. Raises CycleError if graph is not a DAG."""
        in_degree = {n: len(self.reverse.get(n, [])) for n in self.nodes}
        queue = deque([n for n in self.nodes if in_degree[n] == 0])
        order = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for succ in self.edges.get(node, []):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)
        if len(order) != len(self.nodes):
            remaining = self.nodes - set(order)
            raise CycleError(list(remaining))
        return order

    def descendants(self, node_id: str) -> Set[str]:
        """All nodes reachable forward from node_id (used for incremental recompute)."""
        seen = set()
        queue = deque([node_id])
        while queue:
            cur = queue.popleft()
            for succ in self.edges.get(cur, []):
                if succ not in seen:
                    seen.add(succ)
                    queue.append(succ)
        return seen
