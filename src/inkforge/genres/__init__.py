"""Genre blueprint registry."""

from inkforge.genres.blueprints import (
    GENRE_BLUEPRINTS,
    GenreBlueprint,
    get_genre,
    list_genres,
)

__all__ = ["GENRE_BLUEPRINTS", "GenreBlueprint", "get_genre", "list_genres"]
