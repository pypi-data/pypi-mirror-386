import logging
from typing import Collection

import requests

logger = logging.getLogger(__name__)


def check_urls(urls: Collection[str], timeout: int = 5) -> dict[str, str]:
    """
    Checks a list of URLs and returns their status.

    Args:
        urls: A collection of URL strings to check.
        timeout: Maximum time in seconds to wait for each request. Default is 5.
    Returns:
        A dictionary mapping each URL to its status string.
    """

    logger.info(f"Starting check for {len(urls)} URLs with a timeout of {timeout}")
    results: dict[str, str] = {}

    for url in urls:
        status = "UNKNOWN"

        try:
            logger.debug(f"Checking URL: {url}")
            response = requests.get(url, timeout=timeout)

            if response.ok:
                status = f"{response.status_code} OK"
            else:
                status = f"{response.status_code} {response.reason}"
        except requests.exceptions.Timeout:
            status = "TIMEOUT"
            logger.warning(f"Request to {url} timed out.")
        except requests.exceptions.ConnectionError:
            status = "CONNECTION_ERROR"
            logger.warning(f"Connection error for {url}.")
        except requests.exceptions.RequestException as e:
            status = f"REQUEST_ERROR: {type(e).__name__}"
            logger.error(
                f"An unexpected request error occured for{url}: {e}", exc_info=True
            )

        results[url] = status
        logger.info(f"Checked: {url:<40} -> {status}")

    logger.info("URL Check finished.")
    return results
