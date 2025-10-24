<p align="center">
  <img src="https://raw.githubusercontent.com/engineer0427/Atlas/main/docs/AtlasImage.png" alt="Atlas Logo" width="400"/>
</p>

<p align="center">
  <a href="https://pypi.org/project/atlas/">
    <img src="https://img.shields.io/pypi/v/atlas?color=blue&style=for-the-badge" alt="PyPI version"/>
  </a>
  <a href="https://img.shields.io/badge/python-3.10+-brightgreen?style=for-the-badge&logo=python">
    <img src="https://img.shields.io/badge/python-3.10+-brightgreen?style=for-the-badge&logo=python" alt="Python"/>
  </a>
  <a href="https://github.com/engineer0427/Atlas/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-Apache%202.0-lightgrey?style=for-the-badge" alt="License"/>
  </a>
</p>

---

> 🧭 **AI로 지식을 그리다.**  
> Atlas는 AI가 텍스트·코드·데이터의 의미를 분석해 관계를 이해하고,  
> 지식의 흐름을 시각적으로 표현하는 **AI-Powered Knowledge Mapping Platform**입니다.

Atlas v1.1.0은 연구 중심 프레임워크를 넘어  
누구나 AI로 지식을 구조화하고 탐색할 수 있는 **웹 기반 플랫폼(SaaS)** 으로 발전했습니다.  
FastAPI 백엔드와 Next.js 프론트엔드가 완전히 통합되어 있으며,  
Koyeb·Vercel·PyPI 자동 배포 파이프라인까지 구축되어 있습니다.

---

## 🌐 Live Demo

> 📍 **Web App:** [https://atlas-gamma-wine.vercel.app](https://atlas-gamma-wine.vercel.app)  
> ☁️ **API Endpoint:** `/api/analyze`  
> 📦 **PyPI Package:** [https://pypi.org/project/atlas/](https://pypi.org/project/atlas/)

---

## 💡 Vision
> **From Framework to Platform. From Knowledge to Insight.**

Atlas는 AI가 인간의 사고 구조를 이해하고,  
지식의 연결을 '지도(map)' 형태로 시각화하는 플랫폼을 목표로 합니다.  
AI가 지식을 분석하고, 사용자는 이를 탐색·확장할 수 있습니다.

---

## 🚀 설치 (Installation)

```bash
pip install atlas
```

또는 개발 버전:
```bash
pip install -e .
```

---

## 🧠 주요 기능 (Key Features)

| 기능 | 설명 |
|------|------|
| 🤖 **AI Analysis Pipeline** | 텍스트 입력 → 개체(Entity) 및 관계(Relation) 추출 → 그래프 데이터 생성 |
| 🌐 **Knowledge Graph Builder** | 개체 간 관계를 네트워크 형태로 시각화 |
| 🧩 **Frontend Integration** | `/test` 페이지에서 실시간 AI 분석 테스트 |
| ⚙️ **FastAPI Backend** | `/api/analyze` 엔드포인트 제공 |
| 🚀 **CI/CD 자동화** | GitHub Actions → Koyeb + Vercel + PyPI 완전 자동 배포 |
| 🧱 **모듈 확장성** | `src/atlas/ai`, `src/atlas/viz` 등 추가 기능 손쉽게 통합 |

---

## ⚙️ API Example

```bash
curl -X POST http://127.0.0.1:8000/api/analyze  -H "Content-Type: application/json"  -d '{"text": "Atlas는 AI를 통해 지식을 시각화한다."}'
```

응답:
```json
{
  "status": "ok",
  "data": {
    "nodes": [...],
    "edges": [...]
  }
}
```

---

## 🖥️ Frontend Test Page

> `/test` 경로에서 직접 텍스트를 입력하고 AI 분석 결과를 확인할 수 있습니다.

```tsx
fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/analyze`, { method: "POST" })
```

---

## 🧩 CI/CD Pipeline

| 구성 요소 | 역할 |
|------------|------|
| 🧱 **GitHub Actions** | 릴리스 및 PyPI 업로드 자동화 |
| ☁️ **Koyeb** | FastAPI 백엔드 자동 배포 |
| 🌐 **Vercel** | Next.js 프론트엔드 자동 배포 |
| 🔐 **Secrets** | `VERCEL_TOKEN`, `KOYEB_API_KEY`, `PYPI_API_TOKEN` 관리 |

---

## 💖 Support Atlas

Atlas는 지식의 연결을 AI로 표현하는 오픈소스 플랫폼입니다.  
작은 후원이 AI 지식 지도 혁신의 큰 힘이 됩니다. 💙

<p align="center">
  <a href="https://github.com/sponsors/engineer0427">
    <img src="https://img.shields.io/badge/Sponsor-Atlas-blue?style=for-the-badge&logo=github-sponsors&logoColor=white" alt="Sponsor Atlas"/>
  </a>
</p>

---

## ⚖️ License

이 프로젝트는 **Apache License 2.0** 하에 배포됩니다.  
자유로운 수정 및 상업적 활용이 가능하며, 원저작자 명시만 유지하시면 됩니다.  
자세한 내용은 [LICENSE](./LICENSE) 참고.
