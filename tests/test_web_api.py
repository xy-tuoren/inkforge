"""Integration tests for FastAPI Web Studio endpoints."""

from pathlib import Path

from fastapi.testclient import TestClient

from inkforge.config import AppSettings, LLMConfig
from inkforge.web.app import create_app


def _make_client(tmp_path: Path) -> TestClient:
    settings = AppSettings(data_dir=tmp_path / ".inkforge", llm=LLMConfig(provider="demo"))
    app = create_app(settings)
    return TestClient(app)


def test_web_api_full_lifecycle(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    # Index HTML & health & genres
    assert client.get("/").status_code == 200
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["provider"] == "demo"

    genres = client.get("/api/genres").json()["genres"]
    assert len(genres) >= 10

    # Create project with auto Story Bible planning
    created = client.post(
        "/api/projects",
        json={
            "title": "东坡旧药园",
            "genre_id": "xianxia",
            "premise": "守药园废徒撞见重伤执剑长老与宗门真账。",
            "target_chapters": 3,
            "auto_plan": True,
        },
    )
    assert created.status_code == 200
    pid = created.json()["project"]["id"]
    assert len(created.json()["project"]["bible"]["characters"]) >= 2

    # Generate chapter 1
    gen = client.post(
        f"/api/projects/{pid}/chapters/1/generate",
        json={"mode": "craft"},
    )
    assert gen.status_code == 200
    ch = gen.json()["chapter"]
    assert ch["audit"]["metrics"]["humanity_score"] >= 85.0

    # Manual edit + automatic re-audit
    edited = client.put(
        f"/api/projects/{pid}/chapters/1",
        json={
            "title": "药锄与断剑",
            "content": "霜降刚过，山风冷得刺骨。空气仿佛凝固了，他嘴角勾起一抹冷笑。",
        },
    )
    assert edited.status_code == 200
    assert edited.json()["chapter"]["audit"]["metrics"]["slop_hits"] >= 2

    # Export EPUB download
    exp = client.get(f"/api/projects/{pid}/export/epub")
    assert exp.status_code == 200
    assert exp.headers["content-type"] == "application/epub+zip"
    assert len(exp.content) > 500

    # Standalone tool audit & polish
    slop_txt = "空气仿佛凝固了，他深吸了一口气，嘴角勾起一抹冷笑。这一刻，他终于明白一切才刚刚开始。"
    t_audit = client.post("/api/tools/audit", json={"text": slop_txt, "genre_id": "suspense"})
    assert t_audit.status_code == 200
    before_score = t_audit.json()["audit"]["metrics"]["humanity_score"]

    t_polish = client.post("/api/tools/polish", json={"text": slop_txt, "genre_id": "suspense"})
    assert t_polish.status_code == 200
    assert t_polish.json()["after_audit"]["metrics"]["humanity_score"] > before_score

    # Delete project
    assert client.delete(f"/api/projects/{pid}").status_code == 200
    assert client.get(f"/api/projects/{pid}").status_code == 404
