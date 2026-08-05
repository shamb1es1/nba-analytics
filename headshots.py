import base64
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from io import BytesIO

import requests
from PIL import Image


HEADSHOT_URL_TEMPLATE = (
    "https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
)
POWER_BI_TEXT_LIMIT = 32_766
THUMBNAIL_SIZES = ((96, 70), (80, 58), (64, 47), (55, 40))


def get_headshot_from_player_id(player_id: int) -> str:
    """Return the NBA CDN headshot URL for a player ID."""

    return HEADSHOT_URL_TEMPLATE.format(player_id=int(player_id))


@lru_cache(maxsize=None)
def get_headshot_data_uri_from_player_id(player_id: int) -> str:
    """Download a player headshot and return a Power BI-safe data URI."""

    response = requests.get(
        get_headshot_from_player_id(player_id),
        timeout=30,
    )
    response.raise_for_status()

    with Image.open(BytesIO(response.content)) as source_image:
        image = source_image.convert("RGBA")

    for size in THUMBNAIL_SIZES:
        thumbnail = image.copy()
        thumbnail.thumbnail(size, Image.Resampling.LANCZOS)

        output = BytesIO()
        thumbnail.save(output, format="PNG", optimize=True)

        encoded = base64.b64encode(output.getvalue()).decode("ascii")
        data_uri = f"data:image/png;base64,{encoded}"

        if len(data_uri) <= POWER_BI_TEXT_LIMIT:
            return data_uri

    raise ValueError(
        f"Headshot for player {player_id} exceeds Power BI's text limit."
    )


def add_headshot_attributes(
    data_frame,
    player_id_column: str,
    max_workers: int = 8,
) -> None:
    """Add URL and embedded-image columns to a player DataFrame in place."""

    data_frame["HEADSHOT_URL"] = data_frame[player_id_column].map(
        get_headshot_from_player_id
    )

    player_ids = data_frame[player_id_column].dropna().unique()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        data_uris = dict(
            zip(
                player_ids,
                executor.map(
                    get_headshot_data_uri_from_player_id,
                    player_ids,
                ),
            )
        )

    data_frame["HEADSHOT_DATA_URI"] = data_frame[player_id_column].map(
        data_uris
    )
