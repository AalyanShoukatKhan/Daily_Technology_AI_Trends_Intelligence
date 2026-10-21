from datetime import datetime, timedelta, timezone
from flask import current_app
from database import get_db
import json, html
def build_digest():
    db=get_db()
    end=datetime.now(timezone.utc); start=end-timedelta(days=1)
    min_score=current_app.config["MIN_DIGEST_SCORE"]; max_items=current_app.config["MAX_DIGEST_ARTICLES"]
    rows=db.execute("""SELECT a.*,s.name source_name FROM articles a LEFT JOIN feed_sources s ON s.id=a.source_id
      WHERE a.published_at>=? AND a.published_at<=? AND a.importance_score>=?
      AND a.id NOT IN (SELECT di.article_id FROM digest_items di JOIN digest_runs dr ON dr.id=di.digest_run_id WHERE dr.created_at>=?)
      ORDER BY a.importance_score DESC LIMIT ?""",(start.isoformat(),end.isoformat(),min_score,start.isoformat(),max_items)).fetchall()
    cur=db.execute("INSERT INTO digest_runs(created_at,date_window_start,date_window_end,status,item_count) VALUES(?,?,?,?,?)",
       (end.isoformat(),start.isoformat(),end.isoformat(),"created",len(rows)))
    digest_id=cur.lastrowid
    for row in rows:
        db.execute("INSERT OR IGNORE INTO digest_items(digest_run_id,article_id,included_at) VALUES(?,?,?)",(digest_id,row["id"],end.isoformat()))
    db.commit()
    lines=["Daily Technology & AI Intelligence Digest",f"Window: {start:%Y-%m-%d %H:%M UTC} to {end:%Y-%m-%d %H:%M UTC}",""]
    blocks=[]
    for i,row in enumerate(rows,1):
        lines += [f"{i}. {row['title']} [{row['importance_score']}/100]",f"Source: {row['source_name'] or 'Unknown'} | {row['published_at']}",row["summary"],row["url"],""]
        blocks.append(
            '<article><h3>' + html.escape(row['title']) + ' <small>(' + str(row['importance_score']) +
            '/100)</small></h3><p>' + html.escape(row['summary']) + '</p><p><a href="' +
            html.escape(row['url'], quote=True) + '">Read original source</a> · ' +
            html.escape(row['source_name'] or 'Unknown') + '</p></article>'
        )
    return {"id":digest_id,"item_count":len(rows),"subject":f"Technology Intelligence Digest — {end:%Y-%m-%d}","text":"\\n".join(lines),
            "html":"<html><body><h1>Daily Technology & AI Intelligence Digest</h1>"+("".join(blocks) if blocks else "<p>No qualifying stories in this window.</p>")+"</body></html>"}
