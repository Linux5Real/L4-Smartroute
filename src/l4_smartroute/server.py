import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from l4_smartroute.blast_radius import calculate_blast_radius, compute_blast_score, score_to_complexity
from l4_smartroute.config import get_available_models, load_config, load_latest_model_library
from l4_smartroute.git_diff_analyzer import get_changed_files, match_diff
from l4_smartroute.graph_analyzer import GraphAnalyzer
from l4_smartroute.prompt_matcher import extract_keywords, match_prompt
from l4_smartroute.recommender import recommend

SERVER_DIR = Path(__file__).parent.parent.parent

MAX_FILES = 20
MAX_COMMUNITIES = 10


def build_analyze_result(
    mode: str,
    matched_keywords: list[str],
    blast_radius: dict,
    complexity: str,
    total_score: float,
    recommendation: dict,
    available_models: list[dict],
) -> dict:
    all_files = blast_radius["affected_files"]
    all_communities = blast_radius["affected_communities"]

    return {
        "analysis": {
            "mode": mode,
            "matched_keywords": matched_keywords,
            "complexity": complexity,
            "blast_radius": {
                "total_score": total_score,
                "files_affected": blast_radius["files_affected"],
                "communities_crossed": blast_radius["communities_crossed"],
                "avg_centrality": blast_radius["avg_centrality"],
                "max_edge_depth": blast_radius["max_edge_depth"],
            },
            "top_affected_files": all_files[:MAX_FILES],
            "files_truncated": len(all_files) > MAX_FILES,
            "top_affected_communities": all_communities[:MAX_COMMUNITIES],
            "communities_truncated": len(all_communities) > MAX_COMMUNITIES,
        },
        "recommendation": recommendation,
        "available_models": [
            {"id": m["id"], "tier": m["tier"]}
            for m in available_models
        ],
    }


class _ConfigLoader:
    """Reloads config.yaml and models.json when either file changes on disk."""

    def __init__(self, config_path: Path, models_path: Path):
        self._config_path = config_path
        self._models_path = models_path
        self._config_mtime: float = 0.0
        self._models_mtime: float = 0.0
        self._cfg: dict = {}
        self._all_models: list[dict] = load_latest_model_library(models_path)
        self._available: list[dict] = []
        self._reload()

    def _reload(self):
        self._cfg = load_config(self._config_path)

        try:
            models_mtime = self._models_path.stat().st_mtime
        except OSError:
            models_mtime = self._models_mtime

        if models_mtime != self._models_mtime:
            self._all_models = load_latest_model_library(self._models_path)
            self._models_mtime = models_mtime

        self._available = get_available_models(self._all_models, self._cfg["available_models"])
        self._config_mtime = self._config_path.stat().st_mtime

    def get(self) -> tuple[dict, list[dict]]:
        try:
            config_mtime = self._config_path.stat().st_mtime
            try:
                models_mtime = self._models_path.stat().st_mtime
            except OSError:
                models_mtime = self._models_mtime

            if config_mtime != self._config_mtime or models_mtime != self._models_mtime:
                self._reload()
        except OSError:
            pass
        return self._cfg, self._available


def create_server(
    config_path: Path | None = None,
    models_path: Path | None = None,
) -> FastMCP:
    if config_path is None:
        config_path = SERVER_DIR / "config.yaml"
    if models_path is None:
        models_path = SERVER_DIR / "models.json"

    loader = _ConfigLoader(config_path, models_path)
    mcp = FastMCP("l4-smartroute")
    analyzer_cache: dict[str, GraphAnalyzer] = {}

    def _get_analyzer(graphify_path: str | None) -> GraphAnalyzer:
        cfg, _ = loader.get()
        gpath = Path(graphify_path) if graphify_path else Path(cfg["graphify_path"])
        if not gpath.exists():
            raise FileNotFoundError(
                f"Graphify graph not found at {gpath}. "
                "Run 'graphify ./your-project' first, or set graphify_path in config.yaml."
            )
        key = str(gpath.resolve())
        if key not in analyzer_cache:
            analyzer_cache[key] = GraphAnalyzer(gpath)
        return analyzer_cache[key]

    def _analyze(
        mode: str,
        start_nodes: list[dict],
        keywords: list[str],
        analyzer: GraphAnalyzer,
        prompt: str = "",
    ) -> str:
        cfg, available = loader.get()
        br = calculate_blast_radius(analyzer, start_nodes, cfg["preferences"]["bfs_max_depth"])
        score = compute_blast_score(
            br["files_affected"],
            br["communities_crossed"],
            br["avg_centrality"],
            br["max_edge_depth"],
        )
        complexity = score_to_complexity(score)
        rec = recommend(
            complexity,
            available,
            cfg["preferences"]["optimize_for"],
            prompt=prompt,
            blast_radius=br,
            router_mode=cfg["preferences"].get("router_mode", "hybrid"),
        )
        result = build_analyze_result(
            mode=mode,
            matched_keywords=keywords,
            blast_radius=br,
            complexity=complexity,
            total_score=round(score, 2),
            recommendation=rec,
            available_models=available,
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    def analyze_task(prompt: str, graphify_path: str | None = None) -> str:
        """Analyze a task prompt and recommend the best AI model + effort level.

        Uses the project's Graphify knowledge graph to calculate blast radius,
        affected files/communities, and complexity score.
        """
        analyzer = _get_analyzer(graphify_path)
        matched = match_prompt(analyzer, prompt)
        keywords = extract_keywords(prompt)
        return _analyze("prompt", matched, keywords, analyzer, prompt=prompt)

    @mcp.tool()
    def analyze_diff(diff_target: str | None = None, graphify_path: str | None = None) -> str:
        """Analyze git diff and recommend the best AI model + effort level for review.

        Maps changed files to the Graphify knowledge graph to calculate blast radius.
        """
        analyzer = _get_analyzer(graphify_path)
        changed_files = get_changed_files(diff_target)
        matched = match_diff(analyzer, changed_files)
        return _analyze("diff", matched, changed_files, analyzer, prompt=" ".join(changed_files))

    @mcp.tool()
    def list_models() -> str:
        """List all available AI models with their metadata, costs, and effort levels."""
        _, available = loader.get()
        return json.dumps(available, indent=2)

    return mcp


def main():
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
