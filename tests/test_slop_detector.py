"""Tests for the deterministic Anti-AI-Slop & Literary Rhythm Analyzer."""

from pathlib import Path

from inkforge.analyzer.slop_detector import analyze_prose

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def test_ai_slop_sample_scores_low_with_exact_spans() -> None:
    text = (EXAMPLES_DIR / "sample_ai_slop_chapter.txt").read_text(encoding="utf-8")
    report = analyze_prose(text, genre_id="suspense")

    assert report.metrics.slop_hits >= 8
    assert report.metrics.preachy_ending_flag is True
    assert report.metrics.telling_hits >= 2
    assert report.metrics.ai_risk_score >= 55.0
    assert report.metrics.humanity_score <= 45.0
    assert report.passed is False

    # Verify every indexed span maps exactly back to the source string
    for issue in report.slop_issues:
        if issue.start >= 0:
            assert text[issue.start : issue.end] == issue.phrase
            assert issue.line >= 1


def test_human_craft_sample_scores_high() -> None:
    text = (EXAMPLES_DIR / "sample_human_craft_chapter.txt").read_text(encoding="utf-8")
    report = analyze_prose(text, genre_id="suspense")

    assert report.metrics.slop_hits == 0
    assert report.metrics.preachy_ending_flag is False
    assert report.metrics.humanity_score >= 88.0
    assert report.metrics.grade == "S"
    assert report.passed is True


def test_genre_cliche_detection() -> None:
    xianxia_text = (
        "大殿之上，青年紧握双拳，怒吼道：“三十年河东，莫欺少年穷！”\n"
        "台下长老闻言纷纷倒吸一口凉气，低语道：“此子断不可留，当真恐怖如斯！”"
    )
    report = analyze_prose(xianxia_text, genre_id="xianxia")
    genre_hits = [i for i in report.slop_issues if i.category == "genre_cliche"]
    assert len(genre_hits) >= 3
    assert report.metrics.humanity_score < 65.0


def test_english_ai_slop_detection() -> None:
    en_slop = (
        "She let out a breath she didn't know she was holding. A tapestry of shadows "
        "sent shivers down her spine as palpable tension filled the hallway. "
        "Moreover, she couldn't help but wonder. Little did she know, the journey had only just begun."
    )
    report = analyze_prose(en_slop, language="en")
    assert report.metrics.slop_hits >= 4
    assert report.metrics.preachy_ending_flag is True
    assert report.metrics.humanity_score < 50.0


def test_empty_text_handled_safely() -> None:
    report = analyze_prose("   ")
    assert report.metrics.char_count == 0
    assert report.passed is False
