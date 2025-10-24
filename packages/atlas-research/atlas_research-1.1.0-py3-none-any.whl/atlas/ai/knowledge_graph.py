# src/ai/knowledge_graph.py
"""
Atlas v1.1.0 - knowledge_graph.py
분석된 엔티티/관계를 기반으로 그래프 데이터 생성
"""

import networkx as nx

def build_graph(entities, relations):
    """
    엔티티와 관계를 받아 네트워크 그래프 구성 후 JSON 반환
    """
    G = nx.DiGraph()
    for e in entities:
        G.add_node(e)
    for r in relations:
        G.add_edge(r["source"], r["target"], type=r["type"])

    # 프론트엔드 전달용 구조
    return {
        "nodes": [{"id": n, "label": n} for n in G.nodes()],
        "edges": [{"source": u, "target": v, "type": d["type"]}
                  for u, v, d in G.edges(data=True)],
    }