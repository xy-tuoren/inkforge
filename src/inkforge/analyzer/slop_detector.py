"""Deterministic quantitative Anti-AI-Slop & Literary Rhythm Analyzer.

Runs locally in milliseconds with zero LLM tokens:
- Pinpoints exact character spans & line numbers of AI-slop clichés
- Detects Tell-don't-Show abstract emotion narration
- Flags preachy / sermonizing chapter endings
- Measures sentence-length burstiness (human cadence vs robotic uniformity)
- Detects local phrase echoes (unintentional AI repetition within ~180 chars)
- Checks genre-specific clichés and dialogue ratio balance
- Computes reproducible Humanity Score (0-100) and AI-Taste Risk Index (0-100)
"""

from __future__ import annotations

import math
import re
from collections import Counter

from inkforge.analyzer.lexicons import (
    CN_AI_CLICHES,
    CN_PREACHY_ENDINGS,
    CN_TELLING_PATTERNS,
    EN_AI_CLICHES,
    SlopPattern,
)
from inkforge.genres.blueprints import GENRE_BLUEPRINTS
from inkforge.models import AuditMetrics, AuditReport, ContinuityIssue, SlopIssue


def _detect_language(text: str) -> str:
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    return "zh" if cjk_count >= max(10, len(text) * 0.15) else "en"


def _line_number_at(text: str, pos: int) -> int:
    return text.count("\n", 0, max(0, pos)) + 1


def _split_sentences(text: str, lang: str) -> list[str]:
    if lang == "zh":
        parts = re.split(r"[。！？!?…\n]+", text)
        return [p.strip() for p in parts if len(re.sub(r"\s+", "", p)) >= 2]
    parts = re.split(r"[.!?\n]+", text)
    return [p.strip() for p in parts if len(p.strip().split()) >= 2]


def _sentence_length(sentence: str, lang: str) -> int:
    if lang == "zh":
        # Count meaningful non-whitespace characters
        return len(re.sub(r"[\s“”\"'‘’《》【】（）()、，,:：;；—-]", "", sentence))
    return len(sentence.split())


def _dialogue_ratio(text: str) -> float:
    total = len(re.sub(r"\s+", "", text))
    if total == 0:
        return 0.0
    quoted = re.findall(r"“[^”\n]{1,400}”|「[^」\n]{1,400}」|\"[^\"\n]{1,400}\"", text)
    q_len = sum(len(re.sub(r"\s+", "", q)) for q in quoted)
    return round(min(1.0, q_len / total), 3)


def _find_pattern_issues(
    text: str,
    patterns: list[SlopPattern],
    search_offset: int = 0,
    flags: int = 0,
) -> list[SlopIssue]:
    issues: list[SlopIssue] = []
    segment = text[search_offset:]
    for item in patterns:
        for m in re.finditer(item.pattern, segment, flags=flags):
            abs_start = search_offset + m.start()
            abs_end = search_offset + m.end()
            issues.append(
                SlopIssue(
                    category=item.category,  # type: ignore[arg-type]
                    severity=item.severity,  # type: ignore[arg-type]
                    phrase=m.group(0),
                    start=abs_start,
                    end=abs_end,
                    line=_line_number_at(text, abs_start),
                    explanation=item.explanation,
                    suggestion=item.suggestion,
                )
            )
    return issues


def _find_genre_cliches(text: str, genre_id: str | None) -> list[SlopIssue]:
    if not genre_id or genre_id not in GENRE_BLUEPRINTS:
        return []
    blueprint = GENRE_BLUEPRINTS[genre_id]
    issues: list[SlopIssue] = []
    for cliché in blueprint.banned_cliches:
        # Strip parenthetical guidance notes if present
        clean = re.sub(r"（[^）]*）|\([^)]*\)", "", cliché).strip()
        if len(clean) < 3:
            continue
        for m in re.finditer(re.escape(clean), text):
            issues.append(
                SlopIssue(
                    category="genre_cliche",
                    severity="high",
                    phrase=m.group(0),
                    start=m.start(),
                    end=m.end(),
                    line=_line_number_at(text, m.start()),
                    explanation=f"命中【{blueprint.name}】题材禁用套话，极易引发读者审美疲劳。",
                    suggestion="改用本作品世界观与人物处境专属的具体动作、细节或台词。",
                )
            )
    return issues


def _find_local_echoes(text: str, lang: str) -> list[SlopIssue]:
    """Detect unintentional close-range repetition of distinctive 4+ char phrases or words."""
    issues: list[SlopIssue] = []
    seen_phrases: set[str] = set()

    if lang == "zh":
        # Extract meaningful 3-to-4 char CJK chunks inside sentences (excluding common particles)
        stopwords = {
            "的时候", "一个人", "不知道", "没有什", "没有什么", "看着他", "看着她",
            "这一刻", "并不是", "已经不", "还是没", "什么也", "看起来", "在这个",
            "自己也", "我们都", "他们都", "这件事", "为什么",
        }
        window = 220
        tokens = list(re.finditer(r"[\u4e00-\u9fff]{4}", text))
        # Slide through 4-grams with stride 1 and flag repeats within 220 chars
        last_pos: dict[str, int] = {}
        for m in tokens:
            gram = m.group(0)
            if gram in stopwords or len(set(gram)) <= 2:
                continue
            prev = last_pos.get(gram)
            if prev is not None and 8 < (m.start() - prev) <= window and gram not in seen_phrases:
                seen_phrases.add(gram)
                issues.append(
                    SlopIssue(
                        category="echo_repetition",
                        severity="low",
                        phrase=gram,
                        start=m.start(),
                        end=m.end(),
                        line=_line_number_at(text, m.start()),
                        explanation=f"短语“{gram}”在约 {m.start() - prev} 字内重复出现，AI 文本常出现局部回声。",
                        suggestion="检查前后两处是否属于刻意呼应；若无必要，将其中一处改为更具体的表达。",
                    )
                )
            last_pos[gram] = m.start()
    else:
        words = list(re.finditer(r"\b[a-zA-Z]{6,}\b", text))
        en_stop = {
            "before", "around", "through", "because", "without", "nothing",
            "something", "against", "between", "another", "thought", "looked",
        }
        last_pos = {}
        for m in words:
            w = m.group(0).lower()
            if w in en_stop:
                continue
            prev = last_pos.get(w)
            if prev is not None and 20 < (m.start() - prev) <= 320 and w not in seen_phrases:
                seen_phrases.add(w)
                issues.append(
                    SlopIssue(
                        category="echo_repetition",
                        severity="low",
                        phrase=m.group(0),
                        start=m.start(),
                        end=m.end(),
                        line=_line_number_at(text, m.start()),
                        explanation=f"Distinctive word '{m.group(0)}' echoed within ~{m.start() - prev} chars.",
                        suggestion="Vary verb/noun choice unless repetition is deliberate rhythm.",
                    )
                )
            last_pos[w] = m.start()

    # Cap noisy echo flags to the top 8 so reports stay actionable
    return issues[:8]


def _compute_burstiness(lengths: list[int]) -> tuple[float, float, float]:
    """Compute mean, std, and normalized burstiness score (0-100).

    Human literary prose mixes crisp short punches with flowing longer sentences
    (coefficient of variation typically 0.45 - 0.85). Robotic AI prose clusters
    tightly around a uniform length (CV < 0.30).
    """
    if len(lengths) < 3:
        mean_val = sum(lengths) / max(1, len(lengths))
        return round(mean_val, 2), 0.0, 65.0

    mean_val = sum(lengths) / len(lengths)
    variance = sum((x - mean_val) ** 2 for x in lengths) / len(lengths)
    std_val = math.sqrt(variance)
    cv = std_val / max(1.0, mean_val)

    # Ideal CV sits around 0.48 - 0.90
    if cv < 0.25:
        burst = 30.0 + (cv / 0.25) * 25.0
    elif cv <= 0.85:
        burst = 55.0 + ((cv - 0.25) / 0.60) * 42.0
    else:
        # Extremely erratic fragments slightly taper off
        burst = max(72.0, 97.0 - (cv - 0.85) * 20.0)

    # Bonus if both short punches and medium-long sentences coexist
    has_short = any(x <= 8 for x in lengths)
    has_long = any(x >= 26 for x in lengths)
    if has_short and has_long:
        burst = min(100.0, burst + 5.0)

    return round(mean_val, 2), round(std_val, 2), round(burst, 1)


def _deduplicate_overlapping_issues(issues: list[SlopIssue]) -> list[SlopIssue]:
    severity_rank = {"high": 3, "medium": 2, "low": 1}
    ordered = sorted(
        issues,
        key=lambda i: (i.start if i.start >= 0 else 10**9, -severity_rank[i.severity]),
    )
    kept: list[SlopIssue] = []
    for item in ordered:
        if item.start < 0:
            kept.append(item)
            continue
        overlap = False
        for prev in kept:
            if prev.start < 0:
                continue
            if not (item.end <= prev.start or item.start >= prev.end):
                overlap = True
                break
        if not overlap:
            kept.append(item)
    return kept


def analyze_prose(
    text: str,
    genre_id: str | None = None,
    language: str | None = None,
    continuity_issues: list[ContinuityIssue] | None = None,
) -> AuditReport:
    """Analyze a chapter or arbitrary prose text for AI-slop and literary rhythm."""
    cleaned = text.strip()
    if not cleaned:
        empty_metrics = AuditMetrics(
            humanity_score=0.0,
            ai_risk_score=100.0,
            grade="D",
        )
        return AuditReport(
            metrics=empty_metrics,
            summary="正文为空，请先生成或输入文本。",
            passed=False,
        )

    lang = language or _detect_language(cleaned)
    char_count = len(re.sub(r"\s+", "", cleaned))
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n+", cleaned) if p.strip()]
    sentences = _split_sentences(cleaned, lang)
    lengths = [_sentence_length(s, lang) for s in sentences]

    avg_len, std_len, burstiness = _compute_burstiness(lengths)
    d_ratio = _dialogue_ratio(cleaned)

    issues: list[SlopIssue] = []

    if lang == "zh":
        issues.extend(_find_pattern_issues(cleaned, CN_AI_CLICHES))
        issues.extend(_find_pattern_issues(cleaned, CN_TELLING_PATTERNS))
        # Scan the final 2 paragraphs (or final 320 chars) for preachy endings
        tail_offset = max(0, len(cleaned) - 360)
        issues.extend(_find_pattern_issues(cleaned, CN_PREACHY_ENDINGS, search_offset=tail_offset))
    else:
        issues.extend(_find_pattern_issues(cleaned, EN_AI_CLICHES, flags=re.IGNORECASE))

    issues.extend(_find_genre_cliches(cleaned, genre_id))
    issues.extend(_find_local_echoes(cleaned, lang))

    # Deduplicate overlapping spans before scoring
    issues = _deduplicate_overlapping_issues(issues)

    # Check flat cadence when enough sentences exist
    if len(lengths) >= 8 and burstiness < 52.0:
        issues.append(
            SlopIssue(
                category="cadence_flat",
                severity="medium",
                phrase=f"平均句长 {avg_len} / 离散度偏低",
                start=-1,
                end=-1,
                line=1,
                explanation="全文句式长度过于均匀，缺乏短句顿挫与长句铺陈的呼吸感，读起来有机器匀速感。",
                suggestion="在冲突或情绪转折处果断加入 3~8 字短句，打断工整的排比节奏。",
            )
        )

    # Check dialogue ratio against genre expectation (only on medium/long chapters >= 450 chars)
    if char_count >= 450 and genre_id and genre_id in GENRE_BLUEPRINTS:
        low_r, high_r = GENRE_BLUEPRINTS[genre_id].dialogue_ratio_range
        if d_ratio < max(0.03, low_r - 0.14):
            issues.append(
                SlopIssue(
                    category="dialogue_issue",
                    severity="low",
                    phrase=f"对话占比 {int(d_ratio * 100)}%",
                    start=-1,
                    end=-1,
                    line=1,
                    explanation=f"本章几乎全是旁白叙述，低于【{GENRE_BLUEPRINTS[genre_id].name}】建议对话占比（{int(low_r*100)}%-{int(high_r*100)}%）。",
                    suggestion="把部分心理说明转化为角色之间带潜台词的直接交锋。",
                )
            )

    cat_counts = Counter(i.category for i in issues)
    slop_hits = cat_counts["ai_cliche"] + cat_counts["genre_cliche"]
    telling_hits = cat_counts["telling_emotion"]
    echo_hits = cat_counts["echo_repetition"]
    preachy_flag = cat_counts["preachy_ending"] > 0

    scale_k = max(0.35, char_count / 1000.0)
    slop_density = round((slop_hits + telling_hits) / scale_k, 2)

    # Compute AI Risk Score (0-100, lower is better)
    severity_weights = {"high": 9.5, "medium": 5.5, "low": 2.5}
    raw_penalty = 0.0
    for issue in issues:
        if issue.category == "preachy_ending":
            raw_penalty += 14.0
        elif issue.category == "echo_repetition":
            raw_penalty += 2.2
        elif issue.category in ("cadence_flat", "dialogue_issue"):
            raw_penalty += 7.0
        else:
            # Normalize phrase penalties by chapter length so long chapters aren't unfairly destroyed
            raw_penalty += severity_weights[issue.severity] / max(0.75, math.sqrt(scale_k))

    # Add penalty for continuity/logic defects if LLM critic ran
    c_issues = continuity_issues or []
    for ci in c_issues:
        raw_penalty += {"high": 14.0, "medium": 7.0, "low": 3.0}[ci.severity]

    # Small cadence penalty/bonus
    if len(lengths) >= 6:
        if burstiness < 50:
            raw_penalty += (50 - burstiness) * 0.25
        elif burstiness >= 76:
            raw_penalty = max(0.0, raw_penalty - 4.0)

    # Smooth saturating curve for AI risk (0-96) so extreme slop reads realistically (~15-35 humanity)
    # rather than flatly hard-clamping to 0, while crisp zero-slop prose reflects burstiness craft (~89-98).
    ai_risk = round(100.0 * (1.0 - math.exp(-raw_penalty / 62.0)), 1)
    ai_risk = min(96.0, max(0.0, ai_risk))

    # Craft ceiling reflects sentence burstiness & prose rhythm (88..98 when AI risk is 0)
    if len(lengths) >= 6:
        rhythm_ceiling = 86.0 + min(12.0, max(0.0, (burstiness - 45.0) * 0.24))
    else:
        rhythm_ceiling = 92.0

    humanity = round(max(4.0, min(98.5, rhythm_ceiling - ai_risk * 0.92)), 1)

    if humanity >= 88:
        grade = "S"
    elif humanity >= 78:
        grade = "A"
    elif humanity >= 65:
        grade = "B"
    elif humanity >= 50:
        grade = "C"
    else:
        grade = "D"

    high_continuity = any(c.severity == "high" for c in c_issues)
    passed = humanity >= 76.0 and not preachy_flag and not high_continuity

    notes: list[str] = []
    if slop_hits:
        notes.append(f"检出 {slop_hits} 处 AI/题材高频套话")
    if telling_hits:
        notes.append(f"{telling_hits} 处情绪直白播报")
    if preachy_flag:
        notes.append("章末存在说教/总结式收尾")
    if echo_hits:
        notes.append(f"{echo_hits} 处局部用词回声")
    if c_issues:
        notes.append(f"{len(c_issues)} 处逻辑/设定连续性隐患")

    if not notes:
        summary = f"文笔自然度 {humanity} 分（{grade} 级）：句式有呼吸感，未检出明显 AI 套话与结尾说教。"
    else:
        summary = (
            f"文笔自然度 {humanity} 分（{grade} 级，AI味风险 {ai_risk}）："
            + "；".join(notes)
            + "。建议执行「去AI味精修」定点替换。"
        )

    metrics = AuditMetrics(
        char_count=char_count,
        sentence_count=len(sentences),
        paragraph_count=len(paragraphs),
        avg_sentence_len=avg_len,
        sentence_len_std=std_len,
        burstiness_score=burstiness,
        dialogue_ratio=d_ratio,
        slop_hits=slop_hits,
        slop_density_per_1k=slop_density,
        telling_hits=telling_hits,
        echo_hits=echo_hits,
        preachy_ending_flag=preachy_flag,
        humanity_score=humanity,
        ai_risk_score=ai_risk,
        grade=grade,  # type: ignore[arg-type]
    )

    return AuditReport(
        metrics=metrics,
        slop_issues=issues,
        continuity_issues=c_issues,
        summary=summary,
        passed=passed,
    )
