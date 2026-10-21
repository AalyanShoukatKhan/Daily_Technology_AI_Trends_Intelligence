import sqlite3, os
from flask import current_app, g
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS feed_sources (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, feed_url TEXT NOT NULL UNIQUE,
 category_hint TEXT NOT NULL DEFAULT 'General Technology', priority INTEGER NOT NULL DEFAULT 10,
 enabled INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, last_fetched_at TEXT, last_status TEXT
);
CREATE TABLE IF NOT EXISTS articles (
 id INTEGER PRIMARY KEY AUTOINCREMENT, source_id INTEGER NOT NULL REFERENCES feed_sources(id) ON DELETE CASCADE,
 guid TEXT, title TEXT NOT NULL, url TEXT NOT NULL, canonical_url TEXT NOT NULL UNIQUE,
 published_at TEXT NOT NULL, fetched_at TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 summary TEXT NOT NULL DEFAULT '', key_points TEXT NOT NULL DEFAULT '[]', why_it_matters TEXT NOT NULL DEFAULT '',
 category TEXT NOT NULL DEFAULT 'General Technology', importance_score INTEGER NOT NULL DEFAULT 0,
 recency_score INTEGER NOT NULL DEFAULT 0, relevance_score INTEGER NOT NULL DEFAULT 0,
 source_priority_score INTEGER NOT NULL DEFAULT 0, signal_score INTEGER NOT NULL DEFAULT 0,
 summary_status TEXT NOT NULL DEFAULT 'pending', content_hash TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_article_guid_source ON articles(source_id,guid) WHERE guid IS NOT NULL AND guid<>'';
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_score ON articles(importance_score);
CREATE TABLE IF NOT EXISTS article_tags (
 id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
 tag TEXT NOT NULL, UNIQUE(article_id,tag)
);
CREATE TABLE IF NOT EXISTS pipeline_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL,
 feeds_attempted INTEGER NOT NULL DEFAULT 0, feeds_succeeded INTEGER NOT NULL DEFAULT 0,
 articles_seen INTEGER NOT NULL DEFAULT 0, articles_added INTEGER NOT NULL DEFAULT 0,
 duplicates_skipped INTEGER NOT NULL DEFAULT 0, ai_calls INTEGER NOT NULL DEFAULT 0,
 errors_count INTEGER NOT NULL DEFAULT 0, error_summary TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS digest_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, date_window_start TEXT NOT NULL,
 date_window_end TEXT NOT NULL, status TEXT NOT NULL, item_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS digest_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT, digest_run_id INTEGER NOT NULL REFERENCES digest_runs(id) ON DELETE CASCADE,
 article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE, included_at TEXT NOT NULL,
 UNIQUE(digest_run_id,article_id)
);
CREATE TABLE IF NOT EXISTS notification_attempts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, digest_run_id INTEGER REFERENCES digest_runs(id) ON DELETE SET NULL,
 channel TEXT NOT NULL, recipient_label TEXT NOT NULL DEFAULT '', attempted_at TEXT NOT NULL,
 status TEXT NOT NULL, provider_message_id TEXT, error_summary TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS app_settings (
 key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL
);
"""
def get_db():
    if "db" not in g:
        path = current_app.config["DATABASE_PATH"]
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        conn = sqlite3.connect(path, timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=20000")
        g.db = conn
    return g.db
def close_db(_=None):
    db = g.pop("db", None)
    if db is not None: db.close()
def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
    current_app.teardown_appcontext(close_db)
if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object("config.Config")
    with app.app_context():
        init_db()
        print("Database initialized.")
