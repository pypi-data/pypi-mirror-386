# 16.03.25


# External libraries
from rich.console import Console


# Internal utilities
from StreamingCommunity.Util.config_json import config_manager
from StreamingCommunity.Util.http_client import create_client_curl
from StreamingCommunity.Util.table import TVShowManager


# Logic class
from StreamingCommunity.Api.Template.config_loader import site_constant
from StreamingCommunity.Api.Template.Class.SearchType import MediaManager
from .util.get_license import CrunchyrollClient


# Variable
console = Console()
media_search_manager = MediaManager()
table_show_manager = TVShowManager()


def title_search(query: str) -> int:
    """
    Search for titles based on a search query.
      
    Parameters:
        - query (str): The query to search for.

    Returns:
        int: The number of titles found.
    """
    media_search_manager.clear()
    table_show_manager.clear()

    # Check if device_id or etp_rt is present
    config = config_manager.get_dict("SITE_LOGIN", "crunchyroll")
    if not config.get('device_id') or not config.get('etp_rt'):
        console.print("[bold red] device_id or etp_rt is missing or empty in config.json.[/bold red]")
        raise Exception("device_id or etp_rt is missing or empty in config.json.")

    # Initialize Crunchyroll client
    client = CrunchyrollClient()
    if not client.start():
        console.print("[bold red] Failed to authenticate with Crunchyroll.[/bold red]")
        raise Exception("Failed to authenticate with Crunchyroll.")

    # Build new Crunchyroll API search URL
    api_url = "https://www.crunchyroll.com/content/v2/discover/search"

    params = {
        "q": query,
        "n": 20,
        "type": "series,movie_listing",
        "ratings": "true",
        "preferred_audio_language": "it-IT",
        "locale": "it-IT"
    }

    headers = client._get_headers()

    console.print(f"[cyan]Search url: [yellow]{api_url}")

    try:
        response = create_client_curl(headers=headers).get(api_url, params=params)
        response.raise_for_status()

    except Exception as e:
        console.print(f"[red]Site: {site_constant.SITE_NAME}, request search error: {e}")
        return 0

    data = response.json()
    found = 0

    # Parse results
    for block in data.get("data", []):
        if block.get("type") not in ("series", "movie_listing", "top_results"):
            continue

        for item in block.get("items", []):
            tipo = None

            if item.get("type") == "movie_listing":
                tipo = "film"
            elif item.get("type") == "series":
                meta = item.get("series_metadata", {})

                if meta.get("episode_count") == 1 and meta.get("season_count", 1) == 1 and meta.get("series_launch_year"):
                    tipo = "film" if "film" in item.get("description", "").lower() or "movie" in item.get("description", "").lower() else "tv"
                else:
                    tipo = "tv"

            else:
                continue

            url = ""
            if tipo == "tv":
                url = f"https://www.crunchyroll.com/series/{item.get('id')}"
            elif tipo == "film":
                url = f"https://www.crunchyroll.com/series/{item.get('id')}"
            else:
                continue

            title = item.get("title", "")

            media_search_manager.add_media({
                'url': url,
                'name': title,
                'type': tipo
            })
            found += 1

    return media_search_manager.get_length()