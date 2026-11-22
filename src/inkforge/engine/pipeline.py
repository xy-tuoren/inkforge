"""Multi-stage anti-AI-slop novel generation pipeline.

Stages:
1. Architect       -> Builds Story Bible (world rules, voice cards, clue ledger, outlines)
2. Scene Director  -> Generates concrete 3-5 Scene Beats per chapter
3. Prose Drafter   -> Drafts chapter with strict genre + voice + anti-slop constraints
4. Dual Auditor    -> Deterministic AI-Slop Analyzer + optional LLM Continuity Critic
5. Surgical Polish -> Targeted de-AI rewrite guided by exact red-pen spans & logic notes
6. State Sync      -> Updates Story Bible continuity archive (locations, injuries, items, clues)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal

from inkforge.analyzer.slop_detector import analyze_prose
from inkforge.engine.prompts import (
    build_architect_prompts,
    build_continuity_critic_prompts,
    build_drafter_prompts,
    build_polisher_prompts,
    build_scene_director_prompts,
    build_state_extractor_prompts,
    parse_safe_list,
)
from inkforge.genres.blueprints import get_genre
from inkforge.llm.base import LLMClient
from inkforge.models import (
    AuditReport,
    Chapter,
    ChapterOutline,
    ChapterRevision,
    CharacterCard,
    CharacterVoice,
    ContinuityIssue,
    ForeshadowingItem,
    NovelProject,
    SceneBeat,
    StoryBible,
    WorldRule,
)
from inkforge.storage.repository import NovelRepository

ProgressCallback = Callable[[str, str], Awaitable[None] | None]


async def _emit(cb: ProgressCallback | None, stage: str, message: str) -> None:
    if cb is None:
        return
    res = cb(stage, message)
    if res is not None:
        await res


class NovelPipeline:
    def __init__(self, llm: LLMClient, repo: NovelRepository) -> None:
        self.llm = llm
        self.repo = repo

    # ---------------- Project Creation ----------------
    def create_project(
        self,
        title: str,
        genre_id: str,
        premise: str,
        *,
        style_notes: str = "",
        target_chapters: int = 8,
        target_words_per_chapter: int | None = None,
        language: Literal["zh", "en"] = "zh",
    ) -> NovelProject:
        bp = get_genre(genre_id)
        project = NovelProject(
            title=title.strip(),
            genre_id=bp.id,
            premise=premise.strip(),
            style_notes=style_notes.strip(),
            target_chapters=max(1, min(100, target_chapters)),
            target_words_per_chapter=target_words_per_chapter or bp.default_words_per_chapter,
            language=language,
            bible=StoryBible(
                premise=premise.strip(),
                tone_and_style=bp.tagline,
                narrative_pov=bp.default_pov,
            ),
        )
        return self.repo.save_project(project)

    # ---------------- Stage 1: Architect ----------------
    async def build_story_bible(
        self,
        project_id: str,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> NovelProject:
        project = self._require_project(project_id)
        bp = get_genre(project.genre_id)
        await _emit(on_progress, "architect", f"正在构建【{bp.name}】世界观铁律、人物声纹卡与 {project.target_chapters} 章大纲…")

        system, user = build_architect_prompts(project, bp)
        data = await self.llm.complete_json(
            system,
            user,
            task="architect",
            temperature=0.65,
            max_tokens=4096,
            metadata={
                "genre_id": project.genre_id,
                "title": project.title,
                "premise": project.premise,
                "target_chapters": project.target_chapters,
            },
        )
        if not isinstance(data, dict):
            data = {}

        world_rules = [
            WorldRule(
                category=str(r.get("category", "核心法则")),
                rule=str(r.get("rule", "")),
                cost_or_limit=str(r.get("cost_or_limit", "")),
            )
            for r in parse_safe_list(data, "world_rules")
            if r.get("rule")
        ]

        characters: list[CharacterCard] = []
        for c in parse_safe_list(data, "characters"):
            if not c.get("name"):
                continue
            raw_voice = c.get("voice") if isinstance(c.get("voice"), dict) else {}
            voice = CharacterVoice(
                sentence_style=str(raw_voice.get("sentence_style", "短句为主，克制自然")),
                vocabulary_register=str(raw_voice.get("vocabulary_register", "贴合身份口语")),
                verbal_tics=str(raw_voice.get("verbal_tics", "无明显口癖")),
                conflict_style=str(raw_voice.get("conflict_style", "实事求是，留有余地")),
                sample_lines=[str(x) for x in (raw_voice.get("sample_lines") or [])[:4]],
            )
            characters.append(
                CharacterCard(
                    name=str(c["name"]),
                    role=str(c.get("role", "主要角色")),
                    age_or_identity=str(c.get("age_or_identity", "")),
                    core_desire=str(c.get("core_desire", "")),
                    flaw_or_fear=str(c.get("flaw_or_fear", "")),
                    secret=str(c.get("secret", "")),
                    current_state=str(c.get("current_state", "正常")),
                    current_location=str(c.get("current_location", "")),
                    inventory=[str(x) for x in (c.get("inventory") or [])],
                    relationships={
                        str(k): str(v)
                        for k, v in (c.get("relationships") or {}).items()
                        if isinstance(c.get("relationships"), dict)
                    },
                    voice=voice,
                )
            )

        foreshadowing = [
            ForeshadowingItem(
                title=str(f.get("title", "未命名伏笔")),
                description=str(f.get("description", "")),
                planted_chapter=int(f.get("planted_chapter") or 1),
                target_payoff_chapter=(
                    int(f["target_payoff_chapter"])
                    if f.get("target_payoff_chapter")
                    else None
                ),
                status="open",
            )
            for f in parse_safe_list(data, "foreshadowing")
            if f.get("title")
        ]

        outlines: list[ChapterOutline] = []
        for idx, o in enumerate(parse_safe_list(data, "outlines"), 1):
            outlines.append(
                ChapterOutline(
                    chapter_number=int(o.get("chapter_number") or idx),
                    title=str(o.get("title") or f"第{idx}章"),
                    pov=str(o.get("pov", "")),
                    summary=str(o.get("summary", "")),
                    core_conflict=str(o.get("core_conflict", "")),
                    chapter_hook=str(o.get("chapter_hook", "")),
                    target_words=int(o.get("target_words") or project.target_words_per_chapter),
                    must_include_clues=[str(x) for x in (o.get("must_include_clues") or [])],
                )
            )

        # Guarantee we have outlines up to target_chapters
        if not outlines:
            for idx in range(1, project.target_chapters + 1):
                outlines.append(
                    ChapterOutline(
                        chapter_number=idx,
                        title=f"第{idx}章",
                        summary=project.premise,
                        target_words=project.target_words_per_chapter,
                    )
                )

        project.bible = StoryBible(
            premise=project.premise,
            logline=str(data.get("logline") or project.premise),
            tone_and_style=str(data.get("tone_and_style") or bp.tagline),
            narrative_pov=str(data.get("narrative_pov") or bp.default_pov),
            world_overview=str(data.get("world_overview") or ""),
            world_rules=world_rules,
            characters=characters,
            foreshadowing=foreshadowing,
            outlines=outlines,
            timeline_log=[],
        )
        self.repo.save_project(project)

        # Ensure placeholder chapter rows exist for every outline
        for o in outlines:
            existing = self.repo.get_chapter(project.id, o.chapter_number)
            if not existing:
                self.repo.save_chapter(
                    Chapter(
                        project_id=project.id,
                        chapter_number=o.chapter_number,
                        title=o.title,
                        status="planned",
                    )
                )

        await _emit(
            on_progress,
            "architect_done",
            f"设定集构建完成：{len(world_rules)} 条铁律、{len(characters)} 位人物声纹卡、{len(foreshadowing)} 条伏笔、{len(outlines)} 章大纲。",
        )
        return project

    # ---------------- Stage 2: Scene Director ----------------
    async def generate_beats(
        self,
        project_id: str,
        chapter_number: int,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> Chapter:
        project = self._require_project(project_id)
        bp = get_genre(project.genre_id)
        outline = self._get_or_create_outline(project, chapter_number)
        recent_summaries, prev_closing = self._collect_prior_context(project.id, chapter_number)

        await _emit(on_progress, "scene_director", f"正在拆解第 {chapter_number} 章《{outline.title}》场景分镜…")
        system, user = build_scene_director_prompts(
            project, bp, outline, recent_summaries, prev_closing
        )
        data = await self.llm.complete_json(
            system,
            user,
            task="scene_director",
            use_fast_model=True,
            temperature=0.55,
            metadata={
                "genre_id": project.genre_id,
                "chapter_number": chapter_number,
                "chapter_title": outline.title,
                "premise": project.premise,
            },
        )
        raw_beats = parse_safe_list(data, "beats")
        beats = [
            SceneBeat(
                beat_index=int(b.get("beat_index") or idx),
                location=str(b.get("location", "")),
                time_marker=str(b.get("time_marker", "")),
                pov=str(b.get("pov") or outline.pov),
                characters_present=[str(x) for x in (b.get("characters_present") or [])],
                goal=str(b.get("goal", "")),
                obstacle=str(b.get("obstacle", "")),
                turn=str(b.get("turn", "")),
                sensory_anchor=str(b.get("sensory_anchor", "")),
                subtext_note=str(b.get("subtext_note", "")),
            )
            for idx, b in enumerate(raw_beats, 1)
        ]

        chapter = self.repo.get_chapter(project.id, chapter_number) or Chapter(
            project_id=project.id,
            chapter_number=chapter_number,
            title=outline.title,
        )
        chapter.title = outline.title
        chapter.beats = beats
        self.repo.save_chapter(chapter)
        await _emit(on_progress, "scene_director_done", f"已生成 {len(beats)} 个场景节拍。")
        return chapter

    # ---------------- Stage 3-6: Full Chapter Generation ----------------
    async def generate_chapter(
        self,
        project_id: str,
        chapter_number: int,
        *,
        mode: Literal["craft", "fast"] = "craft",
        auto_polish_threshold: float = 82.0,
        on_progress: ProgressCallback | None = None,
    ) -> Chapter:
        """Run full multi-stage generation for a single chapter.

        - craft mode: Scene Beats -> Draft -> Deterministic Audit + LLM Continuity Critic -> Surgical Polish (if needed) -> State Sync
        - fast mode:  Scene Beats -> Draft -> Deterministic Audit -> Surgical Polish (only if humanity_score < threshold) -> State Sync
        """
        project = self._require_project(project_id)
        if not project.bible.outlines:
            project = await self.build_story_bible(project_id, on_progress=on_progress)

        bp = get_genre(project.genre_id)
        outline = self._get_or_create_outline(project, chapter_number)
        chapter = self.repo.get_chapter(project.id, chapter_number)

        if not chapter or not chapter.beats:
            chapter = await self.generate_beats(project.id, chapter_number, on_progress=on_progress)

        recent_summaries, prev_closing = self._collect_prior_context(project.id, chapter_number)

        # Stage 3: Draft
        await _emit(on_progress, "drafter", f"正在执笔第 {chapter_number} 章《{outline.title}》初稿…")
        d_sys, d_usr = build_drafter_prompts(
            project, bp, outline, chapter.beats, recent_summaries, prev_closing
        )
        raw_draft = await self.llm.complete(
            d_sys,
            d_usr,
            task="drafter",
            temperature=0.82,
            max_tokens=4096,
            metadata={
                "genre_id": project.genre_id,
                "title": project.title,
                "premise": project.premise,
                "chapter_number": chapter_number,
                "chapter_title": outline.title,
            },
        )
        chapter.raw_content = raw_draft
        chapter.content = raw_draft
        chapter.status = "drafted"

        # Stage 4: Dual Auditor
        await _emit(on_progress, "auditor", "正在执行去AI味红笔体检与逻辑一致性审查…")
        continuity_issues: list[ContinuityIssue] = []
        if mode == "craft":
            c_sys, c_usr = build_continuity_critic_prompts(
                project, bp, chapter, recent_summaries
            )
            c_data = await self.llm.complete_json(
                c_sys,
                c_usr,
                task="continuity_critic",
                use_fast_model=True,
                temperature=0.2,
                metadata={
                    "genre_id": project.genre_id,
                    "chapter_number": chapter_number,
                },
            )
            for item in parse_safe_list(c_data, "continuity_issues"):
                cat = str(item.get("category", "logic_gap"))
                if cat not in ("world_rule", "character_ooc", "timeline", "logic_gap", "voice_flat", "pacing"):
                    cat = "logic_gap"
                sev = str(item.get("severity", "medium"))
                if sev not in ("high", "medium", "low"):
                    sev = "medium"
                continuity_issues.append(
                    ContinuityIssue(
                        category=cat,  # type: ignore[arg-type]
                        severity=sev,  # type: ignore[arg-type]
                        excerpt=str(item.get("excerpt", "")),
                        explanation=str(item.get("explanation", "")),
                        fix_hint=str(item.get("fix_hint", "")),
                    )
                )

        raw_audit = analyze_prose(
            raw_draft,
            genre_id=project.genre_id,
            language=project.language,
            continuity_issues=continuity_issues,
        )
        chapter.audit = raw_audit
        chapter.revisions.append(
            ChapterRevision(
                version=len(chapter.revisions) + 1,
                stage="raw_draft",
                content=raw_draft,
                humanity_score=raw_audit.metrics.humanity_score,
                ai_risk_score=raw_audit.metrics.ai_risk_score,
                note=f"初稿体检：{raw_audit.metrics.humanity_score}分（AI味风险 {raw_audit.metrics.ai_risk_score}）",
            )
        )
        self.repo.save_chapter(chapter)

        # Stage 5: Surgical Anti-AI Polish
        needs_polish = (
            mode == "craft"
            or raw_audit.metrics.humanity_score < auto_polish_threshold
            or raw_audit.metrics.preachy_ending_flag
            or bool(continuity_issues)
        )
        if needs_polish:
            await _emit(
                on_progress,
                "polisher",
                f"初稿自然度 {raw_audit.metrics.humanity_score} 分，正在执行「去AI味外科手术精修」…",
            )
            chapter = await self.polish_chapter(project.id, chapter_number, on_progress=on_progress)

        # Stage 6: State Sync
        await _emit(on_progress, "state_sync", "正在同步本章人物状态、时间线与伏笔账本…")
        s_sys, s_usr = build_state_extractor_prompts(project, chapter)
        s_data = await self.llm.complete_json(
            s_sys,
            s_usr,
            task="state_extractor",
            use_fast_model=True,
            temperature=0.2,
            metadata={
                "genre_id": project.genre_id,
                "chapter_number": chapter_number,
                "chapter_title": chapter.title,
            },
        )
        if isinstance(s_data, dict):
            chapter.summary = str(s_data.get("summary") or outline.summary)
            chapter.state_diff = s_data
            self.repo.save_chapter(chapter)
            self.repo.apply_state_diff(project, s_data)

        await _emit(
            on_progress,
            "chapter_done",
            f"第 {chapter_number} 章《{chapter.title}》定稿完成！自然度 {chapter.audit.metrics.humanity_score if chapter.audit else '-'} 分。",
        )
        return chapter

    async def polish_chapter(
        self,
        project_id: str,
        chapter_number: int,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> Chapter:
        project = self._require_project(project_id)
        chapter = self.repo.get_chapter(project.id, chapter_number)
        if not chapter or not chapter.content.strip():
            raise ValueError(f"第 {chapter_number} 章尚无正文，请先执笔初稿。")

        bp = get_genre(project.genre_id)
        before_audit = chapter.audit or analyze_prose(
            chapter.content, genre_id=project.genre_id, language=project.language
        )

        p_sys, p_usr = build_polisher_prompts(project, bp, chapter.content, before_audit)
        polished = await self.llm.complete(
            p_sys,
            p_usr,
            task="polisher",
            temperature=0.72,
            max_tokens=4096,
            metadata={
                "genre_id": project.genre_id,
                "chapter_number": chapter_number,
                "chapter_title": chapter.title,
                "mode": "chapter",
                "source_text": chapter.content,
            },
        )

        after_audit = analyze_prose(
            polished,
            genre_id=project.genre_id,
            language=project.language,
        )
        chapter.content = polished
        chapter.status = "polished"
        chapter.audit = after_audit
        delta = round(after_audit.metrics.humanity_score - before_audit.metrics.humanity_score, 1)
        sign = "+" if delta >= 0 else ""
        chapter.revisions.append(
            ChapterRevision(
                version=len(chapter.revisions) + 1,
                stage="polished",
                content=polished,
                humanity_score=after_audit.metrics.humanity_score,
                ai_risk_score=after_audit.metrics.ai_risk_score,
                note=f"去AI精修：{before_audit.metrics.humanity_score} → {after_audit.metrics.humanity_score}（{sign}{delta}分）",
            )
        )
        self.repo.save_chapter(chapter)
        await _emit(
            on_progress,
            "polisher_done",
            f"精修完成：自然度 {before_audit.metrics.humanity_score} → {after_audit.metrics.humanity_score}（{sign}{delta}分）。",
        )
        return chapter

    async def polish_standalone_text(
        self,
        text: str,
        genre_id: str = "suspense",
    ) -> dict[str, Any]:
        """Audit and surgically de-AI any standalone text outside a project."""
        bp = get_genre(genre_id)
        before_audit = analyze_prose(text, genre_id=bp.id)
        p_sys, p_usr = build_polisher_prompts(None, bp, text, before_audit)
        polished = await self.llm.complete(
            p_sys,
            p_usr,
            task="polisher",
            temperature=0.7,
            max_tokens=4096,
            metadata={
                "genre_id": bp.id,
                "mode": "standalone",
                "source_text": text,
            },
        )
        after_audit = analyze_prose(polished, genre_id=bp.id)
        return {
            "original_text": text,
            "polished_text": polished,
            "before_audit": before_audit.model_dump(),
            "after_audit": after_audit.model_dump(),
            "score_delta": round(
                after_audit.metrics.humanity_score - before_audit.metrics.humanity_score, 1
            ),
        }

    def audit_chapter(self, project_id: str, chapter_number: int) -> AuditReport:
        project = self._require_project(project_id)
        chapter = self.repo.get_chapter(project.id, chapter_number)
        if not chapter:
            raise ValueError(f"未找到第 {chapter_number} 章。")
        report = analyze_prose(
            chapter.content,
            genre_id=project.genre_id,
            language=project.language,
            continuity_issues=chapter.audit.continuity_issues if chapter.audit else [],
        )
        chapter.audit = report
        self.repo.save_chapter(chapter)
        return report

    # ---------------- Helpers ----------------
    def _require_project(self, project_id: str) -> NovelProject:
        project = self.repo.get_project(project_id)
        if not project:
            raise ValueError(f"未找到项目：{project_id}")
        return project

    def _get_or_create_outline(
        self, project: NovelProject, chapter_number: int
    ) -> ChapterOutline:
        for o in project.bible.outlines:
            if o.chapter_number == chapter_number:
                return o
        outline = ChapterOutline(
            chapter_number=chapter_number,
            title=f"第{chapter_number}章",
            summary=f"承接前文推进《{project.title}》主线剧情。",
            target_words=project.target_words_per_chapter,
        )
        project.bible.outlines.append(outline)
        self.repo.save_project(project)
        return outline

    def _collect_prior_context(
        self, project_id: str, chapter_number: int
    ) -> tuple[list[str], str]:
        chapters = self.repo.list_chapters(project_id)
        prior = [c for c in chapters if c.chapter_number < chapter_number and c.content.strip()]
        summaries = [
            f"第{c.chapter_number}章《{c.title}》：{c.summary or c.content[:140]}"
            for c in prior
        ]
        prev_closing = ""
        if prior:
            last_text = prior[-1].content.strip()
            prev_closing = last_text[-420:] if len(last_text) > 420 else last_text
        return summaries, prev_closing
