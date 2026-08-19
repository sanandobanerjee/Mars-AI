from collections import defaultdict
from typing import Dict, List, Optional, Set

from src.ingestion.models import Chunk


class CallGraph:
    def __init__(self, chunks: List[Chunk]):
        self.chunks_by_id: Dict[str, Chunk] = {c.id: c for c in chunks}
        self._by_qualified_name: Dict[str, str] = {}
        self._by_simple_name: Dict[str, List[str]] = defaultdict(list)
        self.calls: Dict[str, Set[str]] = defaultdict(set)
        self.called_by: Dict[str, Set[str]] = defaultdict(set)

        self._build_lookups(chunks)
        self._resolve_calls(chunks)

    def _build_lookups(self, chunks: List[Chunk]) -> None:
        for c in chunks:
            if c.type in ("function", "method"):
                self._by_qualified_name[c.qualified_name] = c.id
                self._by_simple_name[c.name].append(c.id)

    def _resolve_target(self, caller: Chunk, raw_call: str) -> Optional[str]:
        if raw_call.startswith("self.") or raw_call.startswith("cls."):
            method_name = raw_call.split(".", 1)[1]
            if "." in caller.qualified_name:
                class_name = caller.qualified_name.split(".")[0]
                candidate = f"{class_name}.{method_name}"
                return self._by_qualified_name.get(candidate)
            return None

        if "." in raw_call:
            return self._by_qualified_name.get(raw_call)

        candidates = self._by_simple_name.get(raw_call, [])
        if len(candidates) == 1:
            return candidates[0]
        return None

    def _resolve_calls(self, chunks: List[Chunk]) -> None:
        for c in chunks:
            if c.type not in ("function", "method"):
                continue
            for raw_call in c.calls:
                target_id = self._resolve_target(c, raw_call)
                if target_id and target_id != c.id:
                    self.calls[c.id].add(target_id)
                    self.called_by[target_id].add(c.id)

    def get_callees(self, chunk_id: str, max_hops: int = 1) -> Set[str]:
        return self._traverse(chunk_id, self.calls, max_hops)

    def get_callers(self, chunk_id: str, max_hops: int = 1) -> Set[str]:
        return self._traverse(chunk_id, self.called_by, max_hops)

    def _traverse(self, start_id: str, edge_map: Dict[str, Set[str]], max_hops: int) -> Set[str]:
        visited: Set[str] = set()
        frontier: Set[str] = {start_id}
        for _ in range(max_hops):
            next_frontier: Set[str] = set()
            for node_id in frontier:
                for neighbor in edge_map.get(node_id, set()):
                    if neighbor not in visited and neighbor != start_id:
                        next_frontier.add(neighbor)
            if not next_frontier:
                break
            visited.update(next_frontier)
            frontier = next_frontier
        return visited

    def stats(self) -> dict:
        return {
            "total_nodes": len(self.chunks_by_id),
            "nodes_with_calls": len(self.calls),
            "total_edges": sum(len(v) for v in self.calls.values()),
        }