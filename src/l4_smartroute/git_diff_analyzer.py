import subprocess

from l4_smartroute.graph_analyzer import GraphAnalyzer


def parse_diff_output(output: str) -> list[str]:
    return [line.strip() for line in output.strip().splitlines() if line.strip()]


def get_changed_files(diff_target: str | None = None) -> list[str]:
    if diff_target:
        cmd = ["git", "diff", "--name-only", diff_target]
    else:
        cmd = ["git", "diff", "--name-only"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return parse_diff_output(result.stdout)


def match_diff(analyzer: GraphAnalyzer, changed_files: list[str]) -> list[dict]:
    matched = {}
    for filepath in changed_files:
        for node in analyzer.find_by_source_file(filepath):
            matched[node["id"]] = node
    return list(matched.values())
