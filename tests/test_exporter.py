"""Tests for Markdown, TXT, HTML, and EPUB3 exporters."""

import zipfile
from pathlib import Path

import pytest

from inkforge.engine.exporter import export_project
from inkforge.engine.pipeline import NovelPipeline
from inkforge.llm.demo_provider import DemoLLMClient
from inkforge.storage.repository import NovelRepository


@pytest.mark.asyncio
async def test_export_all_formats_and_valid_epub3(tmp_path: Path) -> None:
    repo = NovelRepository(tmp_path / "export.db")
    pipeline = NovelPipeline(DemoLLMClient(), repo)

    project = pipeline.create_project(
        title="铁砧七号轨道",
        genre_id="scifi",
        premise="近地轨道回收站焊工发现一具藏有轨道偏置指令的旧维护舱。",
        target_chapters=2,
    )
    await pipeline.build_story_bible(project.id)
    await pipeline.generate_chapter(project.id, 1, mode="craft")

    chapters = repo.list_chapters(project.id)
    out_dir = tmp_path / "out"

    md_path = export_project(project, chapters, out_dir, fmt="md")
    txt_path = export_project(project, chapters, out_dir, fmt="txt")
    html_path = export_project(project, chapters, out_dir, fmt="html")
    epub_path = export_project(project, chapters, out_dir, fmt="epub")

    assert "# 铁砧七号轨道" in md_path.read_text(encoding="utf-8")
    assert "《铁砧七号轨道》" in txt_path.read_text(encoding="utf-8")
    assert "<article id=\"ch-1\">" in html_path.read_text(encoding="utf-8")

    # Verify EPUB3 specification compliance
    assert epub_path.exists()
    with zipfile.ZipFile(epub_path, "r") as zf:
        names = zf.namelist()
        assert names[0] == "mimetype"
        assert zf.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert zf.read("mimetype") == b"application/epub+zip"
        assert "META-INF/container.xml" in names
        assert "OEBPS/content.opf" in names
        assert "OEBPS/nav.xhtml" in names
        assert "OEBPS/chapter_001.xhtml" in names
