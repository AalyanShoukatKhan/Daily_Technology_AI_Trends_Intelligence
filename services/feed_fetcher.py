import feedparser, httpx
from flask import current_app
from urllib.parse import urlparse
def validate_feed_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Only valid HTTP(S) feed URLs are allowed.")
    if parsed.hostname.lower() in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Localhost feed URLs are not allowed.")
    return url
def fetch_feed(url):
    if url.startswith("newsapi://"):
        api_key = current_app.config.get("NEWS_API_KEY", "")
        if not api_key:
            raise ValueError("NEWS_API_KEY is not configured; add it to .env and restart the app.")
        params = {
            "q": current_app.config.get("NEWS_API_QUERY", "technology OR artificial intelligence"),
            "language": current_app.config.get("NEWS_API_LANGUAGE", "en"),
            "sortBy": "publishedAt",
            "pageSize": current_app.config.get("NEWS_API_PAGE_SIZE", 100),
            "apiKey": api_key,
        }
        with httpx.Client(timeout=httpx.Timeout(20.0), follow_redirects=True,
                           headers={"User-Agent": "TechnologyIntelligence/1.0"}) as client:
            response = client.get("https://newsapi.org/v2/everything", params=params)
            response.raise_for_status()
            payload = response.json()
        if payload.get("status") != "ok":
            raise ValueError(str(payload.get("message", "NewsAPI returned an error"))[:180])
        return [{"title": a.get("title"), "link": a.get("url"), "id": a.get("url"),
                 "published": a.get("publishedAt"), "summary": a.get("description") or a.get("content") or ""}
                for a in payload.get("articles", []) if a.get("title") and a.get("url")]
    validate_feed_url(url)
    with httpx.Client(timeout=httpx.Timeout(12.0), follow_redirects=True, headers={"User-Agent":"TechnologyIntelligence/1.0 RSS reader"}) as client:
        response = client.get(url)
        response.raise_for_status()
        if len(response.content) > 2_000_000:
            raise ValueError("Feed response exceeds the 2 MB limit.")
        parsed = feedparser.parse(response.content)
        if not parsed.entries and getattr(parsed, "bozo", False):
            raise ValueError("Feed could not be parsed.")
        return parsed.entries
def test_feed(url):
    try:
        entries = fetch_feed(url)
        return {"ok": True, "message": f"Feed parsed successfully ({len(entries)} entries)."}
    except Exception as exc:
        return {"ok": False, "message": str(exc)[:180]}
