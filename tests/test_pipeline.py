"""End-to-end tests for the multi-stage InkForge pipeline and Story Bible continuity sync."""

from pathlib import Path

import pytest

from inkforge.engine.pipeline import NovelPipeline
from inkforge.llm.demo_provider import DemoLLMClient
from inkforge.storage.repository import NovelRepository


@pytest.mark.asyncio
async def test_full_pipeline_craft_mode_improves_humanity_and_syncs_state(
    tmp_path: Path,
) -> None:
    repo = NovelRepository(tmp_path / "test.db")
    pipeline = NovelPipeline(DemoLLMClient(), repo)

    project = pipeline.create_project(
        title="雨夜十五分钟",
        genre_id="suspense",
        premise="梅雨季老城区药房停电十五分钟，老板死在反锁库房里，账本缺了一页。",
        target_chapters=4,
    )

    planned = await pipeline.build_story_bible(project.id)
    assert len(planned.bible.world_rules) >= 2
    assert len(planned.bible.characters) >= 2
    assert len(planned.bible.outlines) == 4
    assert len(planned.bible.foreshadowing) >= 2

    ch1 = await pipeline.generate_chapter(project.id, 1, mode="craft")
    assert ch1.status == "polished"
    assert len(ch1.beats) >= 3
    assert len(ch1.revisions) == 2

    raw_score = ch1.revisions[0].humanity_score
    polished_score = ch1.revisions[1].humanity_score
    assert polished_score > raw_score + 30.0
    assert polished_score >= 88.0
    assert ch1.audit is not None
    assert ch1.audit.passed is True

    # Verify Story Bible continuity state diff was synced
    updated_project = repo.get_project(project.id)
    assert updated_project is not None
    assert len(updated_project.bible.timeline_log) == 1
    lead = updated_project.bible.characters[0]
    assert any("第1章" in item for item in lead.inventory)

    # Generate chapter 2 using chapter 1 summary & state
    ch2 = await pipeline.generate_chapter(project.id, 2, mode="craft")
    assert ch2.chapter_number == 2
    assert ch2.audit is not None
    assert ch2.audit.metrics.humanity_score >= 82.0


@pytest.mark.asyncio
@pytest.mark.parametrize("genre_id", ["xianxia", "scifi", "urban_drama", "historical"])
async def test_multiple_genres_generate_high_craft_chapters(
    tmp_path: Path, genre_id: str
) -> None:
    repo = NovelRepository(tmp_path / f"{genre_id}.db")
    pipeline = NovelPipeline(DemoLLMClient(), repo)

    project = pipeline.create_project(
        title=f"测试-{genre_id}",
        genre_id=genre_id,
        premise="一段关于现实代价与暗线博弈的多题材测试故事。",
        target_chapters=3,
    )
    await pipeline.build_story_bible(project.id)
    ch1 = await pipeline.generate_chapter(project.id, 1, mode="craft")
    assert ch1.audit is not None
    assert ch1.audit.metrics.humanity_score >= 85.0
    assert ch1.audit.metrics.preachy_ending_flag is False
