"""Core domain models for InkForge novels, story bibles, beats, chapters, and audits."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def short_id() -> str:
    return uuid4().hex[:12]


class WorldRule(BaseModel):
    id: str = Field(default_factory=short_id)
    category: str = "核心法则"
    rule: str
    cost_or_limit: str = ""


class CharacterVoice(BaseModel):
    sentence_style: str = "短句为主，克制不绕弯"
    vocabulary_register: str = "贴合职业与年龄的口语"
    verbal_tics: str = "无明显口癖"
    conflict_style: str = "遇事反问或沉默观察，不轻易讲大道理"
    sample_lines: list[str] = Field(default_factory=list)


class CharacterCard(BaseModel):
    id: str = Field(default_factory=short_id)
    name: str
    role: str = "主要角色"
    age_or_identity: str = ""
    core_desire: str = ""
    flaw_or_fear: str = ""
    secret: str = ""
    current_state: str = "正常"
    current_location: str = ""
    inventory: list[str] = Field(default_factory=list)
    relationships: dict[str, str] = Field(default_factory=dict)
    voice: CharacterVoice = Field(default_factory=CharacterVoice)


class ForeshadowingItem(BaseModel):
    id: str = Field(default_factory=short_id)
    title: str
    description: str
    planted_chapter: int = 1
    target_payoff_chapter: int | None = None
    resolved_chapter: int | None = None
    status: Literal["open", "hinted", "resolved", "abandoned"] = "open"


class ChapterOutline(BaseModel):
    chapter_number: int
    title: str
    pov: str = ""
    summary: str = ""
    core_conflict: str = ""
    chapter_hook: str = ""
    target_words: int = 2600
    must_include_clues: list[str] = Field(default_factory=list)


class StoryBible(BaseModel):
    premise: str = ""
    logline: str = ""
    tone_and_style: str = ""
    narrative_pov: str = "第三人称有限视角"
    world_overview: str = ""
    world_rules: list[WorldRule] = Field(default_factory=list)
    characters: list[CharacterCard] = Field(default_factory=list)
    foreshadowing: list[ForeshadowingItem] = Field(default_factory=list)
    outlines: list[ChapterOutline] = Field(default_factory=list)
    timeline_log: list[str] = Field(default_factory=list)


class SceneBeat(BaseModel):
    beat_index: int
    location: str = ""
    time_marker: str = ""
    pov: str = ""
    characters_present: list[str] = Field(default_factory=list)
    goal: str = ""
    obstacle: str = ""
    turn: str = ""
    sensory_anchor: str = ""
    subtext_note: str = ""


class SlopIssue(BaseModel):
    category: Literal[
        "ai_cliche",
        "telling_emotion",
        "preachy_ending",
        "echo_repetition",
        "genre_cliche",
        "cadence_flat",
        "dialogue_issue",
    ]
    severity: Literal["high", "medium", "low"] = "medium"
    phrase: str
    start: int = -1
    end: int = -1
    line: int = 1
    explanation: str
    suggestion: str


class ContinuityIssue(BaseModel):
    category: Literal[
        "world_rule",
        "character_ooc",
        "timeline",
        "logic_gap",
        "voice_flat",
        "pacing",
    ]
    severity: Literal["high", "medium", "low"] = "medium"
    excerpt: str = ""
    explanation: str
    fix_hint: str = ""


class AuditMetrics(BaseModel):
    char_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    avg_sentence_len: float = 0.0
    sentence_len_std: float = 0.0
    burstiness_score: float = 0.0
    dialogue_ratio: float = 0.0
    slop_hits: int = 0
    slop_density_per_1k: float = 0.0
    telling_hits: int = 0
    echo_hits: int = 0
    preachy_ending_flag: bool = False
    humanity_score: float = 100.0
    ai_risk_score: float = 0.0
    grade: Literal["S", "A", "B", "C", "D"] = "A"


class AuditReport(BaseModel):
    metrics: AuditMetrics
    slop_issues: list[SlopIssue] = Field(default_factory=list)
    continuity_issues: list[ContinuityIssue] = Field(default_factory=list)
    summary: str = ""
    passed: bool = True


class ChapterRevision(BaseModel):
    id: str = Field(default_factory=short_id)
    version: int = 1
    stage: Literal["raw_draft", "polished", "manual_edit"] = "raw_draft"
    content: str
    humanity_score: float = 0.0
    ai_risk_score: float = 0.0
    note: str = ""
    created_at: str = Field(default_factory=utc_now_iso)


class Chapter(BaseModel):
    id: str = Field(default_factory=short_id)
    project_id: str
    chapter_number: int
    title: str
    status: Literal["planned", "drafted", "polished", "approved"] = "planned"
    beats: list[SceneBeat] = Field(default_factory=list)
    content: str = ""
    raw_content: str = ""
    summary: str = ""
    audit: AuditReport | None = None
    state_diff: dict[str, Any] = Field(default_factory=dict)
    revisions: list[ChapterRevision] = Field(default_factory=list)
    updated_at: str = Field(default_factory=utc_now_iso)


class NovelProject(BaseModel):
    id: str = Field(default_factory=short_id)
    title: str
    genre_id: str = "suspense"
    premise: str
    style_notes: str = ""
    target_chapters: int = 12
    target_words_per_chapter: int = 2600
    language: Literal["zh", "en"] = "zh"
    bible: StoryBible = Field(default_factory=StoryBible)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
