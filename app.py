from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import Config
from database import init_db, get_db
from services.pipeline import run_pipeline
from services.feed_fetcher import test_feed
from services.digest_builder import build_digest
from services.notifications.email_sender import send_email
from datetime import datetime, timezone
import logging
import json
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config["SECRET_KEY"]

with app.app_context():
    init_db()
    from services.seed_sources import seed_sources
    seed_sources()

@app.template_filter("from_json")
def from_json(value):
    try:
        return json.loads(value or "[]")
    except Exception:
        return []

@app.template_filter("localdate")
def localdate(value):
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%b %d, %Y %H:%M")
    except Exception:
        return value

@app.route("/")
def dashboard():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    today = datetime.now(timezone.utc).date().isoformat()
    new_today = db.execute("SELECT COUNT(*) FROM articles WHERE substr(published_at,1,10)=?", (today,)).fetchone()[0]
    enabled = db.execute("SELECT COUNT(*) FROM feed_sources WHERE enabled=1").fetchone()[0]
    latest = db.execute("SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 1").fetchone()
    top = db.execute("SELECT a.*,s.name source_name FROM articles a LEFT JOIN feed_sources s ON s.id=a.source_id ORDER BY importance_score DESC LIMIT 6").fetchall()
    categories = db.execute("SELECT category,COUNT(*) count FROM articles GROUP BY category ORDER BY count DESC").fetchall()
    return render_template("dashboard.html", total=total, new_today=new_today, enabled=enabled, latest=latest, top=top, categories=categories)

@app.route("/articles")
def articles():
    db = get_db()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    source_id = request.args.get("source_id", "")
    min_score = request.args.get("min_score", "0")
    sort = request.args.get("sort", "score")
    sql = """SELECT a.*,s.name source_name FROM articles a LEFT JOIN feed_sources s ON s.id=a.source_id WHERE 1=1"""
    args = []
    if q:
        sql += " AND (a.title LIKE ? OR a.description LIKE ? OR a.summary LIKE ? OR s.name LIKE ?)"
        args += [f"%{q}%"] * 4
    if category:
        sql += " AND a.category=?"; args.append(category)
    if source_id:
        sql += " AND a.source_id=?"; args.append(source_id)
    try:
        sql += " AND a.importance_score>=?"; args.append(max(0, min(100, int(min_score))))
    except ValueError:
        pass
    sql += " ORDER BY " + ("published_at ASC" if sort == "oldest" else "published_at DESC" if sort == "newest" else "importance_score DESC")
    rows = db.execute(sql, args).fetchall()
    sources = db.execute("SELECT id,name FROM feed_sources ORDER BY name").fetchall()
    cats = [r[0] for r in db.execute("SELECT DISTINCT category FROM articles ORDER BY category").fetchall()]
    return render_template("articles.html", articles=rows, sources=sources, categories=cats, q=q, category=category, source_id=source_id, min_score=min_score, sort=sort)

@app.route("/articles/<int:article_id>")
def article_detail(article_id):
    db = get_db()
    article = db.execute("SELECT a.*,s.name source_name,s.feed_url FROM articles a LEFT JOIN feed_sources s ON s.id=a.source_id WHERE a.id=?", (article_id,)).fetchone()
    if not article:
        flash("Article not found.", "error")
        return redirect(url_for("articles"))
    tags = db.execute("SELECT tag FROM article_tags WHERE article_id=? ORDER BY tag", (article_id,)).fetchall()
    return render_template("article_detail.html", article=article, tags=tags)

@app.route("/sources", methods=["GET", "POST"])
def sources():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()[:120]
        feed_url = request.form.get("feed_url", "").strip()
        category_hint = request.form.get("category_hint", "General Technology")
        try:
            priority = max(0, min(20, int(request.form.get("priority", "10"))))
        except ValueError:
            priority = 10
        if not name or not feed_url.startswith(("https://", "http://")):
            flash("Enter a source name and valid HTTP(S) feed URL.", "error")
        else:
            try:
                db.execute("INSERT INTO feed_sources(name,feed_url,category_hint,priority,enabled,created_at) VALUES(?,?,?,?,1,?)",
                           (name, feed_url, category_hint, priority, datetime.now(timezone.utc).isoformat()))
                db.commit()
                flash("RSS source added.", "success")
            except Exception:
                db.rollback()
                flash("That source may already exist. Check the URL and try again.", "error")
        return redirect(url_for("sources"))
    rows = db.execute("SELECT * FROM feed_sources ORDER BY enabled DESC,priority DESC,name").fetchall()
    return render_template("sources.html", sources=rows)

@app.post("/sources/<int:source_id>/toggle")
def toggle_source(source_id):
    db = get_db()
    db.execute("UPDATE feed_sources SET enabled=CASE enabled WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (source_id,))
    db.commit()
    flash("Source status updated.", "success")
    return redirect(url_for("sources"))

@app.post("/sources/<int:source_id>/delete")
def delete_source(source_id):
    db = get_db()
    db.execute("DELETE FROM feed_sources WHERE id=?", (source_id,))
    db.commit()
    flash("Source deleted. Existing articles are retained.", "success")
    return redirect(url_for("sources"))

@app.post("/sources/<int:source_id>/test")
def source_test(source_id):
    db = get_db()
    source = db.execute("SELECT * FROM feed_sources WHERE id=?", (source_id,)).fetchone()
    result = test_feed(source["feed_url"]) if source else {"ok": False, "message": "Source not found"}
    db.execute("UPDATE feed_sources SET last_status=?,last_fetched_at=? WHERE id=?",
               (("Success: " if result["ok"] else "Failed: ") + result["message"][:200], datetime.now(timezone.utc).isoformat(), source_id))
    db.commit()
    flash(result["message"], "success" if result["ok"] else "error")
    return redirect(url_for("sources"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    db = get_db()
    if request.method == "POST":
        allowed = {"TIME_ZONE", "COLLECTION_INTERVAL_HOURS", "DIGEST_HOUR", "MAX_DIGEST_ARTICLES", "MIN_DIGEST_SCORE",
                   "AI_PROVIDER", "AI_MODEL", "AI_MAX_CALLS_PER_RUN", "EMAIL_ENABLED", "DIGEST_TO_EMAIL"}
        for key in allowed:
            if key in request.form:
                db.execute("INSERT INTO app_settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                           (key, request.form[key][:300], datetime.now(timezone.utc).isoformat()))
        db.commit()
        flash("Settings saved. Provider secrets remain in your .env file.", "success")
        return redirect(url_for("settings"))
    saved = {r["key"]: r["value"] for r in db.execute("SELECT key,value FROM app_settings").fetchall()}
    return render_template("settings.html", saved=saved, config=app.config)

@app.route("/history")
def history():
    db = get_db()
    runs = db.execute("SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 100").fetchall()
    attempts = db.execute("SELECT * FROM notification_attempts ORDER BY attempted_at DESC LIMIT 50").fetchall()
    return render_template("history.html", runs=runs, attempts=attempts)

@app.post("/run")
def manual_run():
    result = run_pipeline()
    flash(f"Collection finished: {result['articles_added']} new articles; {result['errors_count']} errors.", "success" if result["status"] in ("success", "partial") else "error")
    return redirect(request.referrer or url_for("dashboard"))

@app.post("/digest")
def digest():
    result = build_digest()
    flash(f"Digest created with {result['item_count']} stories.", "success")
    if app.config["EMAIL_ENABLED"]:
        outcome = send_email(result["subject"], result["text"], result["html"])
        flash("Email delivery: " + outcome["message"], "success" if outcome["ok"] else "error")
    return redirect(url_for("history"))

@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "Daily Technology & AI Trends Intelligence"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
