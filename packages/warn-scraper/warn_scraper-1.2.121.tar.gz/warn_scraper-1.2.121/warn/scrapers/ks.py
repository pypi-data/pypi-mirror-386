from pathlib import Path

from warn.platforms.job_center.utils import scrape_state

from .. import utils

__authors__ = ["zstumgoren", "Dilcia19"]
__tags__ = ["jobcenter"]
__source__ = {
    "name": "Kansas Department of Commerce",
    "url": "https://www.kansasworks.com/search/warn_lookups/new",
}


def scrape(
    data_dir: Path = utils.WARN_DATA_DIR,
    cache_dir: Path = utils.WARN_CACHE_DIR,
    use_cache: bool = True,
) -> Path:
    """
    Scrape data from Kansas.

    Arguments:
    output_dir -- the Path were the result will be saved

    Keyword arguments:
    data_dir -- the Path were the result will be saved (default WARN_DATA_DIR)
    cache_dir -- the Path where results can be cached (default WARN_CACHE_DIR)
    use_cache -- a Boolean indicating whether the cache should be used (default True)

    Returns: the Path where the file is written
    """
    output_csv = data_dir / "ks.csv"
    search_url = "https://www.kansasworks.com/search/warn_lookups"
    # Date chosen based on manual research
    stop_year = 1998
    # Use cache for years before current and prior year
    scrape_state(
        "KS", search_url, output_csv, stop_year, cache_dir, use_cache=use_cache
    )
    return output_csv


if __name__ == "__main__":
    scrape()
