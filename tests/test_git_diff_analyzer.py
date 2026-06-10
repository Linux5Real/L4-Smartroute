from pathlib import Path

import pytest

from model_selector.graph_analyzer import GraphAnalyzer
from model_selector.git_diff_analyzer import parse_diff_output, match_diff

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph.json"


@pytest.fixture
def analyzer():
    return GraphAnalyzer(FIXTURE)


class TestParseDiffOutput:
    def test_parses_file_list(self):
        output = "src/auth/middleware.py\nsrc/api/routes.py\n"
        files = parse_diff_output(output)
        assert files == ["src/auth/middleware.py", "src/api/routes.py"]

    def test_strips_whitespace(self):
        output = "  src/auth/jwt.py  \n"
        files = parse_diff_output(output)
        assert files == ["src/auth/jwt.py"]

    def test_empty_output(self):
        assert parse_diff_output("") == []
        assert parse_diff_output("\n") == []


class TestMatchDiff:
    def test_matches_changed_files_to_nodes(self, analyzer):
        changed_files = ["src/auth/middleware.py", "src/auth/jwt.py"]
        nodes = match_diff(analyzer, changed_files)
        ids = {n["id"] for n in nodes}
        assert "auth_middleware_py" in ids
        assert "jwt_handler" in ids
        assert "validate_token" in ids

    def test_unknown_files_are_skipped(self, analyzer):
        changed_files = ["nonexistent/file.py"]
        nodes = match_diff(analyzer, changed_files)
        assert nodes == []

    def test_deduplicates(self, analyzer):
        changed_files = ["src/auth/jwt.py", "src/auth/jwt.py"]
        nodes = match_diff(analyzer, changed_files)
        ids = [n["id"] for n in nodes]
        assert len(ids) == len(set(ids))
