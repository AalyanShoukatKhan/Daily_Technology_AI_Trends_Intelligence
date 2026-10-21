from datetime import datetime, timezone
import re
def score_article(published_at, category, title, description, priority=10, topic_keywords=None):
    try:
        dt=datetime.fromisoformat(published_at.replace("Z","+00:00"))
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        age=max(0,(datetime.now(timezone.utc)-dt.astimezone(timezone.utc)).total_seconds()/3600)
    except Exception: age=72
    recency=round(40 * (2.718281828 ** (-age/(24*5))))
    text=(title+" "+description).lower()
    keywords=topic_keywords or ["ai","security","release","research","vulnerability","open source"]
    relevance=min(25, 8 + 4*sum(1 for k in keywords if k.lower() in text))
    source_priority=max(0,min(20,int(priority)))
    signals= min(15, sum(5 for term in ["critical","zero-day","major release"] if term in text) + sum(2 for term in ["launch","breakthrough","acquisition","regulation"] if term in text))
    total=max(0,min(100,recency+relevance+source_priority+signals))
    return total, {"recency":recency,"relevance":relevance,"source_priority":source_priority,"signals":signals}
