# src/ai/analyzer.py
"""
Atlas v1.1.0 - analyzer.py
텍스트 입력을 받아 개체(Entity)와 관계(Relation)를 추출하는 모듈.
(기본 버전은 간단한 규칙 기반, 추후 OpenAI API 연동 가능)
"""

import re

def analyze_text(text: str):
    """
    입력 문장에서 명사(개체)와 단어 간 연결(관계)을 간단히 추출
    """
    # 단순 명사 패턴 기반 토큰화 예시
    words = re.findall(r"[A-Za-z가-힣]+", text)
    entities = list(set(words))[:10]  # 상위 10개만 사용 (샘플)

    # 단순 인접 관계 추출
    relations = []
    for i in range(len(entities) - 1):
        relations.append({
            "source": entities[i],
            "target": entities[i + 1],
            "type": "related_to"
        })

    return entities, relations