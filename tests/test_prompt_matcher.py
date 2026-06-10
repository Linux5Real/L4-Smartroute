from pathlib import Path

import pytest

from model_selector.graph_analyzer import GraphAnalyzer
from model_selector.prompt_matcher import extract_keywords, match_prompt

FIXTURE = Path(__file__).parent / "fixtures" / "sample_graph.json"


@pytest.fixture
def analyzer():
    return GraphAnalyzer(FIXTURE)


class TestExtractKeywords:
    def test_basic_extraction(self):
        keywords = extract_keywords("Refactor the auth middleware to use JWT")
        assert "auth" in keywords
        assert "middleware" in keywords
        assert "jwt" in keywords
        assert "refactor" in keywords

    def test_strips_stopwords(self):
        keywords = extract_keywords("Fix the bug in the database pool")
        assert "the" not in keywords
        assert "in" not in keywords
        assert "database" in keywords
        assert "pool" in keywords

    def test_lowercases(self):
        keywords = extract_keywords("Update JWTHandler")
        assert "jwthandler" in keywords

    def test_empty_prompt(self):
        assert extract_keywords("") == []

    def test_splits_compound_words(self):
        keywords = extract_keywords("auth_middleware jwt_handler")
        assert "auth" in keywords
        assert "middleware" in keywords


class TestMatchPrompt:
    def test_matches_by_label(self, analyzer):
        result = match_prompt(analyzer, "jwt handler")
        ids = {n["id"] for n in result}
        assert "jwt_handler" in ids

    def test_matches_by_source_file_path(self, analyzer):
        result = match_prompt(analyzer, "middleware")
        ids = {n["id"] for n in result}
        assert "auth_middleware_py" in ids

    def test_no_matches_returns_empty(self, analyzer):
        result = match_prompt(analyzer, "zzz_nonexistent_zzz")
        assert result == []

    def test_deduplicates_matches(self, analyzer):
        result = match_prompt(analyzer, "auth middleware")
        ids = [n["id"] for n in result]
        assert len(ids) == len(set(ids))
