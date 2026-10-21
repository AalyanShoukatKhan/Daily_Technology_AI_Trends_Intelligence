import logging
from datetime import datetime, timezone
from flask import current_app
from database import get_db
from services.feed_fetcher import fetch_feed
from services.article_normalizer import normalize_entry
from services.classifier import classify, tags_for
from services.ai_client import summarize_article
from services.importance_ranker import score_article
logger=logging.getLogger(__name__)
def run_pipeline():
    db=get_db(); started=datetime.now(timezone.utc).isoformat()
    cur=db.execute("INSERT INTO pipeline_runs(started_at,status) VALUES(?,?)",(started,"running"))
    run_id=cur.lastrowid; db.commit()
    result={"id":run_id,"status":"success","feeds_attempted":0,"feeds_succeeded":0,"articles_seen":0,"articles_added":0,"duplicates_skipped":0,"ai_calls":0,"errors_count":0,"error_summary":""}
    errors=[]
    sources=db.execute("SELECT * FROM feed_sources WHERE enabled=1 ORDER BY priority DESC").fetchall()
    result["feeds_attempted"]=len(sources)
    ai_calls=0
    for source in sources:
        try:
            entries=fetch_feed(source["feed_url"])
            result["feeds_succeeded"]+=1
            for entry in entries:
                result["articles_seen"]+=1
                normalized=normalize_entry(entry)
                if not normalized:
                    result["errors_count"]+=1
                    continue
                exists=db.execute("SELECT id FROM articles WHERE canonical_url=? OR (?<>'' AND source_id=? AND guid=?)",
                                  (normalized["canonical_url"],normalized["guid"],source["id"],normalized["guid"])).fetchone()
                if exists:
                    result["duplicates_skipped"]+=1
                    continue
                category=classify(normalized["title"],normalized["description"],source["category_hint"])
                if ai_calls < current_app.config["AI_MAX_CALLS_PER_RUN"]:
                    summary=summarize_article(normalized["title"],normalized["description"],category); ai_calls+=1; result["ai_calls"]+=1
                else:
                    summary={"summary":normalized["description"][:600],"key_points":[],"why_it_matters":"AI call cap reached; verify original source.","status":"fallback"}
                score,factors=score_article(normalized["published_at"],category,normalized["title"],normalized["description"],source["priority"])
                try:
                    cur=db.execute("""INSERT INTO articles(source_id,guid,title,url,canonical_url,published_at,fetched_at,description,summary,key_points,why_it_matters,category,importance_score,recency_score,relevance_score,source_priority_score,signal_score,summary_status,content_hash)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (source["id"],normalized["guid"],normalized["title"],normalized["url"],normalized["canonical_url"],normalized["published_at"],started,normalized["description"],summary["summary"],__import__("json").dumps(summary.get("key_points",[])),summary.get("why_it_matters",""),category,score,factors["recency"],factors["relevance"],factors["source_priority"],factors["signals"],summary["status"],normalized["content_hash"]))
                    article_id=cur.lastrowid
                    for tag in tags_for(normalized["title"],normalized["description"]):
                        db.execute("INSERT OR IGNORE INTO article_tags(article_id,tag) VALUES(?,?)",(article_id,tag))
                    result["articles_added"]+=1
                except Exception:
                    result["duplicates_skipped"]+=1
            db.execute("UPDATE feed_sources SET last_fetched_at=?,last_status=? WHERE id=?",(datetime.now(timezone.utc).isoformat(),f"Success: {len(entries)} entries",source["id"]))
            db.commit()
        except Exception as exc:
            db.rollback()
            result["errors_count"]+=1
            message=f"{source['name']}: {str(exc)[:180]}"
            errors.append(message)
            logger.warning("Feed failed: %s", message)
            db.execute("UPDATE feed_sources SET last_fetched_at=?,last_status=? WHERE id=?",(datetime.now(timezone.utc).isoformat(),f"Failed: {str(exc)[:160]}",source["id"]))
            db.commit()
    result["status"]="success" if result["errors_count"]==0 else ("partial" if result["feeds_succeeded"] else "failed")
    result["error_summary"]="; ".join(errors)[:1000]
    db.execute("""UPDATE pipeline_runs SET finished_at=?,status=?,feeds_attempted=?,feeds_succeeded=?,articles_seen=?,articles_added=?,duplicates_skipped=?,ai_calls=?,errors_count=?,error_summary=? WHERE id=?""",
      (datetime.now(timezone.utc).isoformat(),result["status"],result["feeds_attempted"],result["feeds_succeeded"],result["articles_seen"],result["articles_added"],result["duplicates_skipped"],result["ai_calls"],result["errors_count"],result["error_summary"],run_id))
    db.commit()
    return result
