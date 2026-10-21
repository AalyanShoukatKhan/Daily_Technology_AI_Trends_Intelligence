import re, hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from datetime import datetime, timezone
TRACKING = ("utm_", "fbclid", "gclid", "mc_")
def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", value).strip()
def canonicalize_url(url):
    parts = urlsplit(url.strip())
    query = [(k,v) for k,v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith(TRACKING)]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))
def parse_date(value):
    if not value: return datetime.now(timezone.utc).isoformat()
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z","+00:00"))
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()
def content_hash(title, description):
    return hashlib.sha256((clean_text(title)+"|"+clean_text(description)).encode()).hexdigest()
def normalize_entry(entry):
    title = clean_text(entry.get("title"))
    link = str(entry.get("link") or "").strip()
    if not title or not link.startswith(("http://","https://")):
        return None
    description = clean_text(entry.get("summary") or entry.get("description") or "")[:4000]
    return {"guid": str(entry.get("id") or entry.get("guid") or "")[:500], "title": title[:500],
            "url": link, "canonical_url": canonicalize_url(link),
            "published_at": parse_date(entry.get("published") or entry.get("updated")),
            "description": description, "content_hash": content_hash(title, description)}
