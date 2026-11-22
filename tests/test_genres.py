"""Tests for multi-genre blueprints integrity and differentiation."""

import pytest

from inkforge.genres.blueprints import GENRE_BLUEPRINTS, get_genre, list_genres


def test_ten_distinct_genres_available() -> None:
    genres = list_genres()
    assert len(genres) >= 10
    expected_ids = {
        "suspense",
        "xianxia",
        "scifi",
        "urban_drama",
        "romance_emotional",
        "historical",
        "horror_weird",
        "light_comedy",
        "wuxia",
        "literary_short",
    }
    assert expected_ids.issubset(set(GENRE_BLUEPRINTS.keys()))


def test_every_blueprint_has_rich_craft_rules_and_cliche_bans() -> None:
    for g in list_genres():
        assert g.name
        assert g.tagline
        assert len(g.prose_craft_rules) >= 3
        assert len(g.banned_cliches) >= 4
        assert len(g.world_rule_categories) >= 3
        assert len(g.sample_premise) >= 20
        low, high = g.dialogue_ratio_range
        assert 0.0 < low < high <= 1.0


def test_unknown_genre_raises_key_error() -> None:
    with pytest.raises(KeyError):
        get_genre("nonexistent_genre")
