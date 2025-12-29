import os
import random
import threading
from typing import Dict, List, Optional
from urllib.parse import urlparse


def _normalize_proxy_url(proxy_url: str) -> str:
    if "://" in proxy_url:
        return proxy_url
    return f"http://{proxy_url}"


_rr_lock = threading.Lock()
_rr_candidates: List[str] = []
_rr_index = 0


def _split_proxy_list(raw_list: str) -> List[str]:
    normalized = raw_list.replace(",", "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def _apply_auth_if_missing(proxy_url: str, username: Optional[str], password: Optional[str]) -> str:
    if not (username and password):
        return proxy_url

    parsed = urlparse(proxy_url)
    if parsed.username or parsed.password:
        return proxy_url

    if not parsed.netloc:
        return proxy_url

    return parsed._replace(netloc=f"{username}:{password}@{parsed.netloc}").geturl()


def _build_proxy_url(host: str, scheme: str, username: Optional[str], password: Optional[str]) -> str:
    auth = ""
    if username and password:
        auth = f"{username}:{password}@"
    return f"{scheme}://{auth}{host}"


def _select_proxy_url(candidates: List[str]) -> Optional[str]:
    if not candidates:
        return None

    strategy = os.getenv("WEBSHARE_PROXY_STRATEGY", "round_robin").lower()
    if strategy == "random":
        return random.choice(candidates)

    global _rr_candidates, _rr_index
    with _rr_lock:
        if candidates != _rr_candidates:
            _rr_candidates = list(candidates)
            _rr_index = 0
        proxy_url = _rr_candidates[_rr_index % len(_rr_candidates)]
        _rr_index += 1
        return proxy_url


def _get_list_proxy_url() -> Optional[str]:
    raw_list = os.getenv("WEBSHARE_PROXY_LIST")
    if not raw_list:
        return None

    scheme = os.getenv("WEBSHARE_PROXY_SCHEME", "http")
    username = os.getenv("WEBSHARE_PROXY_USERNAME") or os.getenv("WEBSHARE_PROXY_USER")
    password = os.getenv("WEBSHARE_PROXY_PASSWORD") or os.getenv("WEBSHARE_PROXY_PASS")

    candidates: List[str] = []
    for item in _split_proxy_list(raw_list):
        if "://" in item:
            proxy_url = _apply_auth_if_missing(item, username, password)
        else:
            proxy_url = _build_proxy_url(item, scheme, username, password)

        parsed = urlparse(proxy_url)
        if parsed.hostname:
            candidates.append(proxy_url)

    return _select_proxy_url(candidates)


def get_proxy_url() -> Optional[str]:
    list_proxy = _get_list_proxy_url()
    if list_proxy:
        return list_proxy

    proxy_url = os.getenv("WEBSHARE_PROXY_URL")
    if proxy_url:
        return _normalize_proxy_url(proxy_url)

    host = os.getenv("WEBSHARE_PROXY_HOST")
    if not host:
        return None

    scheme = os.getenv("WEBSHARE_PROXY_SCHEME", "http")
    port = os.getenv("WEBSHARE_PROXY_PORT")
    username = os.getenv("WEBSHARE_PROXY_USERNAME") or os.getenv("WEBSHARE_PROXY_USER")
    password = os.getenv("WEBSHARE_PROXY_PASSWORD") or os.getenv("WEBSHARE_PROXY_PASS")
    auth = ""
    if username and password:
        auth = f"{username}:{password}@"

    if port:
        return f"{scheme}://{auth}{host}:{port}"
    return f"{scheme}://{auth}{host}"


def get_requests_proxies() -> Optional[Dict[str, str]]:
    proxy_url = get_proxy_url()
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def get_playwright_proxy() -> Optional[Dict[str, str]]:
    proxy_url = get_proxy_url()
    if not proxy_url:
        return None

    parsed = urlparse(proxy_url)
    if not parsed.hostname:
        return None

    server = f"{parsed.scheme}://{parsed.hostname}"
    if parsed.port:
        server = f"{server}:{parsed.port}"

    proxy: Dict[str, str] = {"server": server}
    if parsed.username:
        proxy["username"] = parsed.username
    if parsed.password:
        proxy["password"] = parsed.password

    return proxy
