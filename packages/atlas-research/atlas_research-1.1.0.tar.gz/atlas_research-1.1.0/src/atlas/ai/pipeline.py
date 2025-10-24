# src/atlas/ai/pipeline.py
"""
Atlas v1.1.0 - pipeline.py
Analyzer → KnowledgeGraph 전체 처리 파이프라인
"""

from src.atlas.ai.analyzer import analyze_text
from src.atlas.ai.knowledge_graph import build_graph

def run_pipeline(text: str):
    entities, relations = analyze_text(text)
    graph_data = build_graph(entities, relations)
    return graph_data