from model_selector.graph_analyzer import GraphAnalyzer

WEIGHT_FILES = 1.0
WEIGHT_COMMUNITIES = 3.0
WEIGHT_CENTRALITY = 20.0
WEIGHT_DEPTH = 1.5


def calculate_blast_radius(
    analyzer: GraphAnalyzer,
    start_nodes: list[dict],
    max_depth: int,
) -> dict:
    if not start_nodes:
        return {
            "files_affected": 0,
            "communities_crossed": 0,
            "avg_centrality": 0.0,
            "max_edge_depth": 0,
            "affected_files": [],
            "affected_communities": [],
        }

    start_ids = [n["id"] for n in start_nodes if n]
    reachable = analyzer.bfs_reachable(start_ids, max_depth)

    centrality = analyzer.betweenness_centrality()
    start_centralities = [centrality.get(nid, 0.0) for nid in start_ids]
    avg_centrality = sum(start_centralities) / len(start_centralities) if start_centralities else 0.0

    max_edge_depth = max(reachable.values()) if reachable else 0

    source_files = set()
    communities = {}
    for nid, depth in reachable.items():
        node = analyzer.get_node(nid)
        if not node:
            continue
        sf = node.get("source_file")
        if sf:
            source_files.add(sf)
        cid = node.get("community")
        if cid is not None:
            if cid not in communities:
                community_labels = analyzer.community_labels()
                communities[cid] = {
                    "id": cid,
                    "label": community_labels.get(cid, f"Community {cid}"),
                    "nodes_affected": 0,
                }
            communities[cid]["nodes_affected"] += 1

    return {
        "files_affected": len(source_files),
        "communities_crossed": len(communities),
        "avg_centrality": round(avg_centrality, 4),
        "max_edge_depth": max_edge_depth,
        "affected_files": sorted(source_files),
        "affected_communities": sorted(communities.values(), key=lambda c: -c["nodes_affected"]),
    }


def compute_blast_score(
    files_affected: int,
    communities_crossed: int,
    avg_centrality: float,
    max_edge_depth: int,
) -> float:
    return (
        files_affected * WEIGHT_FILES
        + communities_crossed * WEIGHT_COMMUNITIES
        + avg_centrality * WEIGHT_CENTRALITY
        + max_edge_depth * WEIGHT_DEPTH
    )


def score_to_complexity(score: float) -> str:
    if score < 15:
        return "low"
    elif score < 40:
        return "medium"
    elif score < 80:
        return "high"
    else:
        return "critical"
