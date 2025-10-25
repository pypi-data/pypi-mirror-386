# 11.03.24

# External library
from rich.console import Console


# Logic class
from .serie import download_episode
from .util.ScrapeSerie import ScrapeSerieAnime
from StreamingCommunity.Api.Template.config_loader import site_constant
from StreamingCommunity.Api.Template.Class.SearchType import MediaItem


# Player
from StreamingCommunity.Api.Player.vixcloud import VideoSourceAnime


# Variable
console = Console()


def download_film(select_title: MediaItem):
    """
    Function to download a film.

    Parameters:
        - id_film (int): The ID of the film.
        - title_name (str): The title of the film.
    """

    # Init class
    scrape_serie = ScrapeSerieAnime(site_constant.FULL_URL)
    video_source = VideoSourceAnime(site_constant.FULL_URL)

    # Set up video source (only configure scrape_serie now)
    scrape_serie.setup(None, select_title.id, select_title.slug)
    scrape_serie.is_series = False

    # Start download
    download_episode(0, scrape_serie, video_source)