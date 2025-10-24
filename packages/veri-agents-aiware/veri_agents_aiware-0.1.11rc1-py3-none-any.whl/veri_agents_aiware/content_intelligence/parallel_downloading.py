import logging

import asyncio
from asyncio import Semaphore
import aiohttp

logger = logging.getLogger(__name__)


def in_ipython() -> bool:
    try:
        from IPython.core.getipython import get_ipython

        return get_ipython() is not None
    except ImportError:
        return False


if in_ipython():
    # Patch event loop so run_until_complete works in Jupyter
    import nest_asyncio

    nest_asyncio.apply()


async def adownload_all(
    urls: list[str],
    max_concurrent: int = 10,
    timeout: int = 10,
) -> list[dict | None]:
    semaphore = Semaphore(max_concurrent)

    async def fetch(session: aiohttp.ClientSession, url: str) -> dict | None:
        async with semaphore:
            try:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response.raise_for_status()
                    # maybe a bad idea to assume JSON here:
                    content = await response.json()
                    # logger.info("Downloaded %s", url)
                    return content
            except Exception as e:
                logger.error("Error fetching %s: %s", url, str(e))
                return None

    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        return await asyncio.gather(*tasks)


def download_all(
    urls: list[str],
    max_concurrent: int = 10,
    timeout: int = 10,
) -> list[dict | None]:
    loop = asyncio.get_running_loop()  # Python 3.7+
    try:
        result = loop.run_until_complete(adownload_all(urls, max_concurrent, timeout))
    except RuntimeError:  # no loop running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(adownload_all(urls, max_concurrent, timeout))
    return result
