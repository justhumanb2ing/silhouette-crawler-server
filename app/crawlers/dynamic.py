from playwright.sync_api import sync_playwright

from app.parsing.og import parse_og
from app.crawlers.proxy import get_playwright_proxy


class DynamicCrawlError(Exception):
    pass


def dynamic_crawl(url: str):
    try:
        with sync_playwright() as p:
            launch_kwargs = {"headless": True}
            proxy = get_playwright_proxy()
            if proxy:
                launch_kwargs["proxy"] = proxy

            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page()

            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_load_state("networkidle")

            html = page.content()
            browser.close()

            return parse_og(html, url)

    except Exception as e:
        raise DynamicCrawlError(str(e))
