import re

from l4_smartroute.graph_analyzer import GraphAnalyzer

STOPWORDS = frozenset({
    "a", "an", "the", "to", "in", "on", "at", "of", "for", "is", "it",
    "and", "or", "but", "with", "from", "by", "as", "be", "was", "were",
    "this", "that", "these", "those", "i", "we", "you", "they", "my",
    "do", "does", "did", "will", "would", "should", "could", "can",
    "not", "no", "so", "if", "then", "than", "also", "just", "about",
})


def extract_keywords(prompt: str) -> list[str]:
    if not prompt.strip():
        return []
    tokens = re.split(r'[\s,.:;!?()"\'/]+', prompt.lower())
    expanded = []
    for token in tokens:
        parts = re.split(r'[_\-]', token)
        if len(parts) > 1:
            expanded.extend(parts)
        expanded.append(token)
    keywords = [t for t in expanded if t and t not in STOPWORDS and len(t) > 1]
    return list(dict.fromkeys(keywords))


def match_prompt(analyzer: GraphAnalyzer, prompt: str) -> list[dict]:
    keywords = extract_keywords(prompt)
    if not keywords:
        return []

    matched = {}
    for kw in keywords:
        for node in analyzer.find_by_label(kw):
            matched[node["id"]] = node
        for node in analyzer._node_data.values():
            sf = node.get("source_file", "")
            if kw in sf.lower():
                matched[node["id"]] = node

    return list(matched.values())
