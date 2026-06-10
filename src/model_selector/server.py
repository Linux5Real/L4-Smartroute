import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from model_selector.blast_radius import calculate_blast_radius, compute_blast_score, score_to_complexity
from model_selector.config import get_available_models, load_config, load_model_library
from model_selector.git_diff_analyzer import get_changed_files, match_diff
from model_selector.graph_analyzer import GraphAnalyzer
from model_selector.prompt_matcher import extract_keywords, match_prompt
from model_selector.recommender import recommend

SERVER_DIR = Path(__file__).parent.parent.parent


def build_analyze_result(
    mode: str,
    matched_keywords: list[str],
    blast_radius: dict,
    complexity: str,
    total_score: float,
    recommendation: dict,
    available_models: list[dict],
) -> dict:
    br = blast_radius.copy()
    br["total_score"] = total_score
    return {
        "analysis": {
            "mode": mode,
            "matched_keywords": matched_keywords,
            "blast_radius": br,
            "complexity": complexity,
            "affected_files": blast_radius["affected_files"],
            "affected_communities": blast_radius["affected_communities"],
        },
        "recommendation": recommendation,
        "available_models": [
            {"id": m["id"], "tier": m["tier"], "effort_levels": m.get("effort_levels")}
            for m in available_models
        ],
    }


def create_server(
    config_path: Path | None = None,
    models_path: Path | None = None,
) -> FastMCP:
    if config_path is None:
        config_path = SERVER_DIR / "config.yaml"
    if models_path is None:
        models_path = SERVER_DIR / "models.json"

    cfg = load_config(config_path)
    all_models = load_model_library(models_path)
    available = get_available_models(all_models, cfg["available_models"])

    mcp = FastMCP("model-selector")

    @mcp.tool()
    def analyze_task(prompt: str, graphify_path: str | None = None) -> str:
        """Analyze a task prompt and recommend the best AI model + effort level.

        Uses the project's Graphify knowledge graph to calculate blast radius,
        affected files/communities, and complexity score.
        """
        gpath = Path(graphify_path) if graphify_path else Path(cfg["graphify_path"])
        analyzer = GraphAnalyzer(gpath)

        matched = match_prompt(analyzer, prompt)
        keywords = extract_keywords(prompt)

        max_depth = cfg["preferences"]["bfs_max_depth"]
        br = calculate_blast_radius(analyzer, matched, max_depth)

        score = compute_blast_score(
            br["files_affected"],
            br["communities_crossed"],
            br["avg_centrality"],
            br["max_edge_depth"],
        )
        complexity = score_to_complexity(score)

        rec = recommend(complexity, available, cfg["preferences"]["optimize_for"])

        result = build_analyze_result(
            mode="prompt",
            matched_keywords=keywords,
            blast_radius=br,
            complexity=complexity,
            total_score=round(score, 2),
            recommendation=rec,
            available_models=available,
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    def analyze_diff(diff_target: str | None = None, graphify_path: str | None = None) -> str:
        """Analyze git diff and recommend the best AI model + effort level for review.

        Maps changed files to the Graphify knowledge graph to calculate blast radius.
        """
        gpath = Path(graphify_path) if graphify_path else Path(cfg["graphify_path"])
        analyzer = GraphAnalyzer(gpath)

        changed_files = get_changed_files(diff_target)
        matched = match_diff(analyzer, changed_files)

        max_depth = cfg["preferences"]["bfs_max_depth"]
        br = calculate_blast_radius(analyzer, matched, max_depth)

        score = compute_blast_score(
            br["files_affected"],
            br["communities_crossed"],
            br["avg_centrality"],
            br["max_edge_depth"],
        )
        complexity = score_to_complexity(score)

        rec = recommend(complexity, available, cfg["preferences"]["optimize_for"])

        result = build_analyze_result(
            mode="diff",
            matched_keywords=changed_files,
            blast_radius=br,
            complexity=complexity,
            total_score=round(score, 2),
            recommendation=rec,
            available_models=available,
        )
        return json.dumps(result, indent=2)

    @mcp.tool()
    def list_models() -> str:
        """List all available AI models with their metadata, costs, and effort levels."""
        return json.dumps(available, indent=2)

    return mcp


def main():
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
