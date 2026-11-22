"""FastAPI application powering the InkForge Editorial Studio & REST API."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from inkforge import __version__
from inkforge.analyzer.slop_detector import analyze_prose
from inkforge.config import PROVIDER_PRESETS, AppSettings, LLMConfig, load_settings
from inkforge.engine.exporter import export_project
from inkforge.engine.pipeline import NovelPipeline
from inkforge.genres.blueprints import list_genres
from inkforge.llm import LLMError, create_llm_client
from inkforge.models import Chapter, ChapterRevision, StoryBible
from inkforge.storage.repository import NovelRepository

STATIC_DIR = Path(__file__).parent / "static"


class CreateProjectRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    genre_id: str = "suspense"
    premise: str = Field(min_length=4, max_length=3000)
    style_notes: str = ""
    target_chapters: int = Field(default=6, ge=1, le=100)
    target_words_per_chapter: int | None = Field(default=None, ge=500, le=12000)
    language: Literal["zh", "en"] = "zh"
    auto_plan: bool = True


class UpdateSettingsRequest(BaseModel):
    provider: str = "demo"
    api_key: str | None = None
    base_url: str = ""
    model: str = ""
    fast_model: str = ""
    temperature: float = Field(default=0.78, ge=0.0, le=1.5)


class GenerateChapterRequest(BaseModel):
    mode: Literal["craft", "fast"] = "craft"
    auto_polish_threshold: float = Field(default=82.0, ge=50.0, le=98.0)


class BatchGenerateRequest(BaseModel):
    start_chapter: int = Field(default=1, ge=1)
    end_chapter: int = Field(default=3, ge=1)
    mode: Literal["craft", "fast"] = "craft"


class SaveChapterContentRequest(BaseModel):
    title: str | None = None
    content: str


class StandaloneAuditRequest(BaseModel):
    text: str = Field(min_length=1)
    genre_id: str | None = None


class StandalonePolishRequest(BaseModel):
    text: str = Field(min_length=1)
    genre_id: str = "suspense"


def create_app(settings: AppSettings | None = None) -> FastAPI:
    app_settings = settings or load_settings()
    app_settings.ensure_dirs()
    repo = NovelRepository(app_settings.db_path)

    app = FastAPI(
        title="InkForge 墨铸 — Anti-AI-Slop Novel Studio",
        version=__version__,
    )

    def get_pipeline() -> NovelPipeline:
        llm = create_llm_client(app_settings.llm)
        return NovelPipeline(llm=llm, repo=repo)

    # ---------------- Static UI ----------------
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        index_file = STATIC_DIR / "index.html"
        if not index_file.exists():
            return HTMLResponse("<h1>InkForge API Running</h1>")
        return HTMLResponse(index_file.read_text(encoding="utf-8"))

    # ---------------- Meta & Settings ----------------
    @app.get("/api/health")
    async def health() -> dict:
        return {
            "status": "ok",
            "version": __version__,
            "provider": app_settings.llm.resolved().provider,
            "model": app_settings.llm.resolved().model,
        }

    @app.get("/api/genres")
    async def api_list_genres() -> dict:
        return {"genres": [g.to_dict() for g in list_genres()]}

    @app.get("/api/settings")
    async def api_get_settings() -> dict:
        return {
            "current": app_settings.llm.safe_dict(),
            "presets": [asdict(p) for p in PROVIDER_PRESETS.values()],
        }

    @app.put("/api/settings")
    async def api_update_settings(body: UpdateSettingsRequest) -> dict:
        if body.provider not in PROVIDER_PRESETS:
            raise HTTPException(status_code=400, detail=f"未知模型服务商：{body.provider}")
        # Keep existing API key if user leaves api_key blank when staying on same provider
        new_key = (
            body.api_key.strip()
            if body.api_key is not None and body.api_key.strip()
            else (
                app_settings.llm.api_key
                if body.provider == app_settings.llm.provider and body.api_key is None
                else (body.api_key or "").strip()
            )
        )
        cfg = LLMConfig(
            provider=body.provider,
            api_key=new_key,
            base_url=body.base_url.strip(),
            model=body.model.strip(),
            fast_model=body.fast_model.strip(),
            temperature=body.temperature,
        )
        app_settings.save_llm_config(cfg)
        return {"current": app_settings.llm.safe_dict()}

    # ---------------- Projects ----------------
    @app.get("/api/projects")
    async def api_list_projects() -> dict:
        projects = repo.list_projects()
        items = []
        for p in projects:
            chapters = repo.list_chapters(p.id)
            written = [c for c in chapters if c.content.strip()]
            scores = [
                c.audit.metrics.humanity_score
                for c in written
                if c.audit is not None
            ]
            avg_score = round(sum(scores) / len(scores), 1) if scores else None
            total_chars = sum(len(c.content.strip()) for c in written)
            items.append(
                {
                    "id": p.id,
                    "title": p.title,
                    "genre_id": p.genre_id,
                    "premise": p.premise,
                    "target_chapters": p.target_chapters,
                    "written_chapters": len(written),
                    "total_chars": total_chars,
                    "avg_humanity_score": avg_score,
                    "updated_at": p.updated_at,
                }
            )
        return {"projects": items}

    @app.post("/api/projects")
    async def api_create_project(body: CreateProjectRequest) -> dict:
        try:
            pipeline = get_pipeline()
            project = pipeline.create_project(
                title=body.title,
                genre_id=body.genre_id,
                premise=body.premise,
                style_notes=body.style_notes,
                target_chapters=body.target_chapters,
                target_words_per_chapter=body.target_words_per_chapter,
                language=body.language,
            )
            if body.auto_plan:
                project = await pipeline.build_story_bible(project.id)
            chapters = repo.list_chapters(project.id)
            return {
                "project": project.model_dump(),
                "chapters": [c.model_dump() for c in chapters],
            }
        except (KeyError, ValueError, LLMError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/projects/{project_id}")
    async def api_get_project(project_id: str) -> dict:
        project = repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="未找到该项目。")
        chapters = repo.list_chapters(project_id)
        return {
            "project": project.model_dump(),
            "chapters": [c.model_dump() for c in chapters],
        }

    @app.delete("/api/projects/{project_id}")
    async def api_delete_project(project_id: str) -> dict:
        ok = repo.delete_project(project_id)
        if not ok:
            raise HTTPException(status_code=404, detail="未找到该项目。")
        return {"deleted": True, "project_id": project_id}

    @app.post("/api/projects/{project_id}/plan")
    async def api_plan_project(project_id: str) -> dict:
        try:
            pipeline = get_pipeline()
            project = await pipeline.build_story_bible(project_id)
            chapters = repo.list_chapters(project_id)
            return {
                "project": project.model_dump(),
                "chapters": [c.model_dump() for c in chapters],
            }
        except (ValueError, LLMError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put("/api/projects/{project_id}/bible")
    async def api_update_bible(project_id: str, bible: StoryBible) -> dict:
        project = repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="未找到该项目。")
        project.bible = bible
        repo.save_project(project)
        return {"project": project.model_dump()}

    # ---------------- Chapters ----------------
    @app.get("/api/projects/{project_id}/chapters/{chapter_number}")
    async def api_get_chapter(project_id: str, chapter_number: int) -> dict:
        project = repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="未找到该项目。")
        chapter = repo.get_chapter(project_id, chapter_number)
        if not chapter:
            raise HTTPException(status_code=404, detail=f"未找到第 {chapter_number} 章。")
        return {"chapter": chapter.model_dump()}

    @app.put("/api/projects/{project_id}/chapters/{chapter_number}")
    async def api_save_chapter_content(
        project_id: str, chapter_number: int, body: SaveChapterContentRequest
    ) -> dict:
        project = repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="未找到该项目。")
        chapter = repo.get_chapter(project_id, chapter_number) or Chapter(
            project_id=project_id,
            chapter_number=chapter_number,
            title=body.title or f"第{chapter_number}章",
        )
        if body.title is not None and body.title.strip():
            chapter.title = body.title.strip()
        chapter.content = body.content
        if not chapter.raw_content:
            chapter.raw_content = body.content
        audit = analyze_prose(
            chapter.content, genre_id=project.genre_id, language=project.language
        )
        chapter.audit = audit
        if chapter.status == "planned" and chapter.content.strip():
            chapter.status = "drafted"
        chapter.revisions.append(
            ChapterRevision(
                version=len(chapter.revisions) + 1,
                stage="manual_edit",
                content=chapter.content,
                humanity_score=audit.metrics.humanity_score,
                ai_risk_score=audit.metrics.ai_risk_score,
                note=f"人工修订：{audit.metrics.humanity_score}分",
            )
        )
        repo.save_chapter(chapter)
        return {"chapter": chapter.model_dump()}

    @app.post("/api/projects/{project_id}/chapters/{chapter_number}/beats")
    async def api_generate_beats(project_id: str, chapter_number: int) -> dict:
        try:
            pipeline = get_pipeline()
            chapter = await pipeline.generate_beats(project_id, chapter_number)
            return {"chapter": chapter.model_dump()}
        except (ValueError, LLMError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/projects/{project_id}/chapters/{chapter_number}/generate")
    async def api_generate_chapter(
        project_id: str, chapter_number: int, body: GenerateChapterRequest
    ) -> dict:
        try:
            pipeline = get_pipeline()
            chapter = await pipeline.generate_chapter(
                project_id,
                chapter_number,
                mode=body.mode,
                auto_polish_threshold=body.auto_polish_threshold,
            )
            project = repo.get_project(project_id)
            return {
                "chapter": chapter.model_dump(),
                "project": project.model_dump() if project else None,
            }
        except (ValueError, LLMError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/projects/{project_id}/chapters/{chapter_number}/polish")
    async def api_polish_chapter(project_id: str, chapter_number: int) -> dict:
        try:
            pipeline = get_pipeline()
            chapter = await pipeline.polish_chapter(project_id, chapter_number)
            return {"chapter": chapter.model_dump()}
        except (ValueError, LLMError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/projects/{project_id}/chapters/{chapter_number}/audit")
    async def api_audit_chapter(project_id: str, chapter_number: int) -> dict:
        try:
            pipeline = get_pipeline()
            report = pipeline.audit_chapter(project_id, chapter_number)
            return {"audit": report.model_dump()}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/projects/{project_id}/batch")
    async def api_batch_generate(project_id: str, body: BatchGenerateRequest) -> dict:
        if body.end_chapter < body.start_chapter:
            raise HTTPException(status_code=400, detail="结束章号不能小于起始章号。")
        if body.end_chapter - body.start_chapter >= 15:
            raise HTTPException(status_code=400, detail="单次批量生成最多 15 章，避免请求超时。")
        try:
            pipeline = get_pipeline()
            generated = []
            for num in range(body.start_chapter, body.end_chapter + 1):
                ch = await pipeline.generate_chapter(project_id, num, mode=body.mode)
                generated.append(ch.model_dump())
            project = repo.get_project(project_id)
            return {
                "generated": generated,
                "project": project.model_dump() if project else None,
            }
        except (ValueError, LLMError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    # ---------------- Export ----------------
    @app.get("/api/projects/{project_id}/export/{fmt}")
    async def api_export(
        project_id: str, fmt: Literal["md", "txt", "html", "epub"]
    ) -> FileResponse:
        project = repo.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="未找到该项目。")
        chapters = repo.list_chapters(project_id)
        out_path = export_project(project, chapters, app_settings.exports_dir, fmt=fmt)
        media_types = {
            "md": "text/markdown; charset=utf-8",
            "txt": "text/plain; charset=utf-8",
            "html": "text/html; charset=utf-8",
            "epub": "application/epub+zip",
        }
        return FileResponse(
            path=out_path,
            filename=out_path.name,
            media_type=media_types[fmt],
        )

    # ---------------- Standalone Anti-AI-Slop Tools ----------------
    @app.post("/api/tools/audit")
    async def api_standalone_audit(body: StandaloneAuditRequest) -> dict:
        report = analyze_prose(body.text, genre_id=body.genre_id)
        return {"audit": report.model_dump()}

    @app.post("/api/tools/polish")
    async def api_standalone_polish(body: StandalonePolishRequest) -> dict:
        try:
            pipeline = get_pipeline()
            return await pipeline.polish_standalone_text(body.text, genre_id=body.genre_id)
        except (KeyError, ValueError, LLMError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app
