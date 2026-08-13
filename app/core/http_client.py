# core/http_client.py
import httpx

def get_http_client(base_url: str = "", timeout: float = 180.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(timeout),
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        follow_redirects=True,
    )