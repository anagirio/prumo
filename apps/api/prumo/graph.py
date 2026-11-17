"""Grafo de pré-requisitos (DAG) de conceitos.

Convenção: a aresta aponta do pré-requisito para o conceito que depende dele.
Tudo aqui é determinístico e não usa LLM.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable

from prumo.models import Concept


class GraphError(ValueError):
    """Grafo inválido (duplicado, pré-requisito inexistente ou ciclo)."""


class KnowledgeGraph:
    def __init__(self, concepts: Iterable[Concept]):
        self.concepts: dict[str, Concept] = {}
        for c in concepts:
            if c.id in self.concepts:
                raise GraphError(f"conceito duplicado: {c.id}")
            if len(set(c.prerequisites)) != len(c.prerequisites):
                raise GraphError(f"pré-requisitos repetidos em {c.id}")
            self.concepts[c.id] = c

        self._dependents: dict[str, list[str]] = {cid: [] for cid in self.concepts}
        for c in self.concepts.values():
            for p in c.prerequisites:
                if p == c.id:
                    raise GraphError(f"{c.id} depende de si mesmo")
                if p not in self.concepts:
                    raise GraphError(f"{c.id} depende de conceito inexistente: {p}")
                self._dependents[p].append(c.id)

        self._order = self._toposort()
        self._index = {cid: i for i, cid in enumerate(self._order)}
        self._ancestors = {cid: self._bfs(cid, self.prerequisites) for cid in self.concepts}
        self._descendants = {cid: self._bfs(cid, self.dependents) for cid in self.concepts}
        self._depth: dict[str, int] = {}
        for cid in self._order:
            prereqs = self.concepts[cid].prerequisites
            self._depth[cid] = 0 if not prereqs else 1 + max(self._depth[p] for p in prereqs)

    # ------------------------------------------------------------ consulta

    def prerequisites(self, cid: str) -> list[str]:
        return list(self.concepts[cid].prerequisites)

    def dependents(self, cid: str) -> list[str]:
        return list(self._dependents[cid])

    def ancestors(self, cid: str) -> dict[str, int]:
        """Todos os pré-requisitos (diretos e indiretos) -> distância mínima."""
        return self._ancestors[cid]

    def descendants(self, cid: str) -> dict[str, int]:
        """Todos os conceitos que dependem (direta ou indiretamente) de cid -> distância."""
        return self._descendants[cid]

    def depth(self, cid: str) -> int:
        return self._depth[cid]

    def topological_order(self) -> list[str]:
        return list(self._order)

    def topo_index(self, cid: str) -> int:
        return self._index[cid]

    def closure(self, targets: Iterable[str]) -> set[str]:
        """Alvos mais tudo que é preciso entender antes deles."""
        out: set[str] = set()
        for t in targets:
            if t not in self.concepts:
                raise KeyError(t)
            out.add(t)
            out.update(self._ancestors[t])
        return out

    def to_public(self) -> dict:
        return {
            "concepts": [c.model_dump() for c in self.concepts.values()],
            "edges": [
                {"from": p, "to": c.id} for c in self.concepts.values() for p in c.prerequisites
            ],
            "depth": dict(self._depth),
        }

    # ------------------------------------------------------------ interno

    def _toposort(self) -> list[str]:
        indeg = {cid: len(c.prerequisites) for cid, c in self.concepts.items()}
        ready = deque(cid for cid, d in indeg.items() if d == 0)
        order: list[str] = []
        while ready:
            cid = ready.popleft()
            order.append(cid)
            for d in self._dependents[cid]:
                indeg[d] -= 1
                if indeg[d] == 0:
                    ready.append(d)
        if len(order) != len(self.concepts):
            raise GraphError("o grafo de pré-requisitos tem ciclo")
        return order

    @staticmethod
    def _bfs(start: str, neighbors: Callable[[str], list[str]]) -> dict[str, int]:
        dist: dict[str, int] = {}
        queue: deque[tuple[str, int]] = deque((n, 1) for n in neighbors(start))
        while queue:
            node, d = queue.popleft()
            if node in dist:
                continue
            dist[node] = d
            queue.extend((n, d + 1) for n in neighbors(node))
        return dist
