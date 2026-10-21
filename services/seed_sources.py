from database import get_db
from datetime import datetime, timezone

# Public RSS/Atom feeds and Google News topic feeds run without API credentials.
DEFAULTS = [
    ("OpenAI News", "https://openai.com/news/rss.xml", "Artificial Intelligence and Machine Learning", 20),
    ("Google AI Blog", "https://blog.research.google/feeds/posts/default", "Artificial Intelligence and Machine Learning", 18),
    ("Google News - Artificial Intelligence", "https://news.google.com/rss/search?q=artificial+intelligence+when:2d&hl=en-US&gl=US&ceid=US:en", "Artificial Intelligence and Machine Learning", 19),
    ("Google News - Generative AI", "https://news.google.com/rss/search?q=generative+AI+when:2d&hl=en-US&gl=US&ceid=US:en", "Artificial Intelligence and Machine Learning", 18),
    ("Google News - Technology", "https://news.google.com/rss/search?q=technology+industry+when:2d&hl=en-US&gl=US&ceid=US:en", "Technology Industry", 17),
    ("Google News - Startups and Big Tech", "https://news.google.com/rss/search?q=technology+startups+OR+Big+Tech+when:2d&hl=en-US&gl=US&ceid=US:en", "Technology Industry", 15),
    ("Google News - Cybersecurity", "https://news.google.com/rss/search?q=cybersecurity+OR+data+breach+when:2d&hl=en-US&gl=US&ceid=US:en", "Cybersecurity", 18),
    ("Google News - Cloud and DevOps", "https://news.google.com/rss/search?q=cloud+computing+OR+DevOps+when:2d&hl=en-US&gl=US&ceid=US:en", "Cloud Computing and DevOps", 15),
    ("Google News - Robotics", "https://news.google.com/rss/search?q=robotics+OR+humanoid+robots+when:2d&hl=en-US&gl=US&ceid=US:en", "Robotics and Automation", 14),
    ("Google News - Semiconductors", "https://news.google.com/rss/search?q=semiconductors+OR+chips+when:2d&hl=en-US&gl=US&ceid=US:en", "Semiconductors and Hardware", 15),
    ("Google News - Space Technology", "https://news.google.com/rss/search?q=space+technology+OR+satellites+when:2d&hl=en-US&gl=US&ceid=US:en", "Science and Space Technology", 12),
    ("Google News - Research and Science", "https://news.google.com/rss/search?q=technology+research+science+when:2d&hl=en-US&gl=US&ceid=US:en", "Science and Research", 12),
    ("Google News - Pakistan Technology", "https://news.google.com/rss/search?q=Pakistan+technology+OR+AI+when:2d&hl=en-PK&gl=PK&ceid=PK:en", "Regional Technology News", 13),
    ("Microsoft Security Blog", "https://www.microsoft.com/en-us/security/blog/feed/", "Cybersecurity", 16),
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews", "Cybersecurity", 16),
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "Artificial Intelligence and Machine Learning", 15),
    ("Cloudflare Blog", "https://blog.cloudflare.com/rss/", "Cloud Computing and DevOps", 14),
    ("MIT Technology Review", "https://www.technologyreview.com/feed/", "Technology Industry", 14),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index", "Technology Industry", 14),
    ("TechCrunch", "https://techcrunch.com/feed/", "Technology Industry", 14),
    ("The Verge", "https://www.theverge.com/rss/index.xml", "Technology Industry", 13),
    ("Wired", "https://www.wired.com/feed/rss", "Technology Industry", 13),
    ("NASA Technology", "https://www.nasa.gov/technology/feed/", "Science and Space Technology", 12),
]

def seed_sources():
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    for name, url, category, priority in DEFAULTS:
        db.execute("INSERT OR IGNORE INTO feed_sources(name,feed_url,category_hint,priority,enabled,created_at) VALUES(?,?,?,?,1,?)",
                   (name, url, category, priority, now))
    # NewsAPI is an optional extra discovery provider; RSS remains fully usable without a key.
    from flask import current_app
    if current_app.config.get("NEWS_API_KEY"):
        db.execute("INSERT OR IGNORE INTO feed_sources(name,feed_url,category_hint,priority,enabled,created_at) VALUES(?,?,?,?,1,?)",
                   ("NewsAPI - Global Technology Discovery", "newsapi://everything", "General Technology", 18, now))
    db.commit()
