import json
from pathlib import Path

import networkx as nx


class GraphAnalyzer:
    def __init__(self, graph_path: Path):
        self._path = Path(graph_path)
        self._graph = nx.Graph()
        self._node_data = {}
        self._communities = {}
        self._centrality_cache = None
        self._labels_cache = None
        self._load()

    def _load(self):
        with open(self._path) as f:
            data = json.load(f)

        for node in data.get("nodes", []):
            nid = node["id"]
            self._graph.add_node(nid)
            self._node_data[nid] = node
            community = node.get("community")
            if community is not None:
                self._communities.setdefault(community, []).append(node)

        for link in data.get("links", []):
            self._graph.add_edge(
                link["source"],
                link["target"],
                relation=link.get("relation"),
                weight=link.get("weight", 1.0),
                confidence_score=link.get("confidence_score", 1.0),
            )

        labels_path = self._path.parent / ".graphify_labels.json"
        if labels_path.exists():
            with open(labels_path) as f:
                self._labels_cache = {int(k): v for k, v in json.load(f).items()}

    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    def get_node(self, node_id: str) -> dict | None:
        return self._node_data.get(node_id)

    def community_labels(self) -> dict[int, str]:
        if self._labels_cache:
            return self._labels_cache
        return {cid: f"Community {cid}" for cid in self._communities}

    def nodes_in_community(self, community_id: int) -> list[dict]:
        return self._communities.get(community_id, [])

    def find_by_source_file(self, path: str) -> list[dict]:
        return [n for n in self._node_data.values() if n.get("source_file") == path]

    def find_by_label(self, substring: str) -> list[dict]:
        sub_lower = substring.lower()
        return [
            n for n in self._node_data.values()
            if sub_lower in n.get("norm_label", "").lower()
            or sub_lower in n.get("label", "").lower()
        ]

    def betweenness_centrality(self) -> dict[str, float]:
        if self._centrality_cache is None:
            n = self._graph.number_of_nodes()
            if n > 500:
                k = min(200, n)
                self._centrality_cache = nx.betweenness_centrality(self._graph, k=k)
            else:
                self._centrality_cache = nx.betweenness_centrality(self._graph)
        return self._centrality_cache

    def neighbors(self, node_id: str) -> list[str]:
        if node_id not in self._graph:
            return []
        return list(self._graph.neighbors(node_id))

    def bfs_reachable(self, start_ids: list[str], max_depth: int) -> dict[str, int]:
        visited = {}
        queue = [(nid, 0) for nid in start_ids if nid in self._graph]
        for nid, depth in queue:
            if nid in visited:
                continue
            visited[nid] = depth
            if depth < max_depth:
                for neighbor in self._graph.neighbors(nid):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
        return visited
