import requests

from app.parsing.og import parse_og
from app.crawlers.proxy import get_requests_proxies


class StaticCrawlError(Exception):
    pass


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def static_crawl(url: str):
    try:
        request_kwargs = {"headers": HEADERS, "timeout": 8}
        proxies = get_requests_proxies()
        if proxies:
            request_kwargs["proxies"] = proxies

        res = requests.get(url, **request_kwargs)
        if res.status_code >= 400:
            raise StaticCrawlError(f"HTTP {res.status_code}")

        return parse_og(res.text, url)

    except Exception as e:
        raise StaticCrawlError(str(e))
