"""SQLite WAL persistence layer for InkForge projects, story bibles, chapters, and revisions."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from inkforge.models import (
    AuditReport,
    Chapter,
    ChapterRevision,
    ForeshadowingItem,
    NovelProject,
    SceneBeat,
    StoryBible,
    utc_now_iso,
)


class NovelRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    genre_id TEXT NOT NULL,
                    premise TEXT NOT NULL,
                    style_notes TEXT NOT NULL DEFAULT '',
                    target_chapters INTEGER NOT NULL DEFAULT 12,
                    target_words_per_chapter INTEGER NOT NULL DEFAULT 2600,
                    language TEXT NOT NULL DEFAULT 'zh',
                    bible_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chapters (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    chapter_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'planned',
                    beats_json TEXT NOT NULL DEFAULT '[]',
                    content TEXT NOT NULL DEFAULT '',
                    raw_content TEXT NOT NULL DEFAULT '',
                    summary TEXT NOT NULL DEFAULT '',
                    audit_json TEXT,
                    state_diff_json TEXT NOT NULL DEFAULT '{}',
                    revisions_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE (project_id, chapter_number)
                );
                """
            )

    # ---------------- Projects ----------------
    def save_project(self, project: NovelProject) -> NovelProject:
        project.updated_at = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, title, genre_id, premise, style_notes,
                    target_chapters, target_words_per_chapter, language,
                    bible_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    genre_id=excluded.genre_id,
                    premise=excluded.premise,
                    style_notes=excluded.style_notes,
                    target_chapters=excluded.target_chapters,
                    target_words_per_chapter=excluded.target_words_per_chapter,
                    language=excluded.language,
                    bible_json=excluded.bible_json,
                    updated_at=excluded.updated_at
                """,
                (
                    project.id,
                    project.title,
                    project.genre_id,
                    project.premise,
                    project.style_notes,
                    project.target_chapters,
                    project.target_words_per_chapter,
                    project.language,
                    project.bible.model_dump_json(),
                    project.created_at,
                    project.updated_at,
                ),
            )
        return project

    def _row_to_project(self, row: sqlite3.Row) -> NovelProject:
        bible = StoryBible.model_validate_json(row["bible_json"])
        return NovelProject(
            id=row["id"],
            title=row["title"],
            genre_id=row["genre_id"],
            premise=row["premise"],
            style_notes=row["style_notes"],
            target_chapters=row["target_chapters"],
            target_words_per_chapter=row["target_words_per_chapter"],
            language=row["language"],
            bible=bible,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_project(self, project_id: str) -> NovelProject | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return self._row_to_project(row) if row else None

    def list_projects(self) -> list[NovelProject]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY updated_at DESC"
            ).fetchall()
        return [self._row_to_project(r) for r in rows]

    def delete_project(self, project_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cur.rowcount > 0

    # ---------------- Chapters ----------------
    def save_chapter(self, chapter: Chapter) -> Chapter:
        chapter.updated_at = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chapters (
                    id, project_id, chapter_number, title, status,
                    beats_json, content, raw_content, summary,
                    audit_json, state_diff_json, revisions_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, chapter_number) DO UPDATE SET
                    title=excluded.title,
                    status=excluded.status,
                    beats_json=excluded.beats_json,
                    content=excluded.content,
                    raw_content=excluded.raw_content,
                    summary=excluded.summary,
                    audit_json=excluded.audit_json,
                    state_diff_json=excluded.state_diff_json,
                    revisions_json=excluded.revisions_json,
                    updated_at=excluded.updated_at
                """,
                (
                    chapter.id,
                    chapter.project_id,
                    chapter.chapter_number,
                    chapter.title,
                    chapter.status,
                    json.dumps([b.model_dump() for b in chapter.beats], ensure_ascii=False),
                    chapter.content,
                    chapter.raw_content,
                    chapter.summary,
                    chapter.audit.model_dump_json() if chapter.audit else None,
                    json.dumps(chapter.state_diff, ensure_ascii=False),
                    json.dumps([r.model_dump() for r in chapter.revisions], ensure_ascii=False),
                    chapter.updated_at,
                ),
            )
            conn.execute(
                "UPDATE projects SET updated_at = ? WHERE id = ?",
                (chapter.updated_at, chapter.project_id),
            )
        return chapter

    def _row_to_chapter(self, row: sqlite3.Row) -> Chapter:
        beats = [SceneBeat.model_validate(b) for b in json.loads(row["beats_json"] or "[]")]
        audit = AuditReport.model_validate_json(row["audit_json"]) if row["audit_json"] else None
        state_diff = json.loads(row["state_diff_json"] or "{}")
        revisions = [
            ChapterRevision.model_validate(r)
            for r in json.loads(row["revisions_json"] or "[]")
        ]
        return Chapter(
            id=row["id"],
            project_id=row["project_id"],
            chapter_number=row["chapter_number"],
            title=row["title"],
            status=row["status"],
            beats=beats,
            content=row["content"],
            raw_content=row["raw_content"],
            summary=row["summary"],
            audit=audit,
            state_diff=state_diff,
            revisions=revisions,
            updated_at=row["updated_at"],
        )

    def get_chapter(self, project_id: str, chapter_number: int) -> Chapter | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM chapters WHERE project_id = ? AND chapter_number = ?",
                (project_id, chapter_number),
            ).fetchone()
        return self._row_to_chapter(row) if row else None

    def list_chapters(self, project_id: str) -> list[Chapter]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM chapters WHERE project_id = ? ORDER BY chapter_number ASC",
                (project_id,),
            ).fetchall()
        return [self._row_to_chapter(r) for r in rows]

    def apply_state_diff(self, project: NovelProject, diff: dict[str, Any]) -> NovelProject:
        """Apply chapter-end character, timeline, and foreshadowing state updates to Story Bible."""
        if not diff:
            return project

        bible = project.bible
        timeline_entry = diff.get("timeline_entry")
        if isinstance(timeline_entry, str) and timeline_entry.strip():
            if timeline_entry not in bible.timeline_log:
                bible.timeline_log.append(timeline_entry.strip())

        char_by_name = {c.name: c for c in bible.characters}
        for upd in diff.get("character_updates", []) or []:
            if not isinstance(upd, dict):
                continue
            name = upd.get("name", "")
            card = char_by_name.get(name)
            if not card:
                continue
            if upd.get("current_state"):
                card.current_state = str(upd["current_state"])
            if upd.get("current_location"):
                card.current_location = str(upd["current_location"])
            for item in upd.get("add_inventory", []) or []:
                if item and item not in card.inventory:
                    card.inventory.append(str(item))
            for item in upd.get("remove_inventory", []) or []:
                if item in card.inventory:
                    card.inventory.remove(item)
            if isinstance(upd.get("relationships"), dict):
                card.relationships.update(
                    {str(k): str(v) for k, v in upd["relationships"].items()}
                )

        clue_by_title = {f.title: f for f in bible.foreshadowing}
        for fu in diff.get("foreshadowing_updates", []) or []:
            if not isinstance(fu, dict):
                continue
            title = str(fu.get("title", "")).strip()
            if not title:
                continue
            existing = clue_by_title.get(title)
            if existing:
                status = fu.get("status")
                if status in ("open", "hinted", "resolved", "abandoned"):
                    existing.status = status
                if fu.get("resolved_chapter"):
                    existing.resolved_chapter = int(fu["resolved_chapter"])
            else:
                bible.foreshadowing.append(
                    ForeshadowingItem(
                        title=title,
                        description=str(fu.get("description", title)),
                        planted_chapter=int(fu.get("planted_chapter", 1)),
                        target_payoff_chapter=fu.get("target_payoff_chapter"),
                        status="open",
                    )
                )

        return self.save_project(project)
