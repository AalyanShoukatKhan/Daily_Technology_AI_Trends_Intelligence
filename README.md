# Daily Technology & AI Trends Intelligence System

A local-first Python/Flask application that automatically discovers technology news from a broad built-in RSS/Atom and Google News feed catalogue, normalizes and deduplicates stories, classifies topics, creates AI summaries when configured, calculates transparent importance scores, stores run history in SQLite, and provides a dashboard and daily digest. Optional NewsAPI integration adds API-based article discovery. Once the scheduler is running, collection and digest generation happen on a schedule without manually adding each story.

## Requirements
- Python 3.11 or 3.12 recommended
- Internet connection for public RSS feeds and optional AI/email integrations
- Optional OpenAI API account/key for AI-generated summaries
- Optional SMTP credentials for email delivery

## Windows PowerShell setup
```powershell
cd technology_intelligence
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` only for optional integrations: `NEWS_API_KEY` adds NewsAPI discovery; `AI_API_KEY` enables AI-generated summaries; SMTP settings enable email digests. The built-in RSS/Google News sources work without API keys. Leave credentials blank to run in fallback mode. Never commit `.env`.

## Run the application
```powershell
python -m database
python app.py
```
Open http://127.0.0.1:5000

## Collect articles
In the dashboard, click **Run collection**, or use a second terminal:
```powershell
.\.venv\Scripts\Activate.ps1
python run_pipeline.py --once
python run_pipeline.py --dry-run
python run_pipeline.py --source-test "OpenAI News"
```
The first collection can take time depending on feed response times and the configured AI provider. Each source is handled independently. Feed errors are recorded without intentionally stopping other sources.

## Scheduler
To start the dashboard and scheduler together on Windows, use this helper after setup:
```powershell
.\start_automated_system.ps1
```
This opens separate windows for the dashboard and scheduler. Keep both open while you want the local system running. Alternatively, start `python run_scheduler.py` in its own terminal. Keep only one scheduler process active. Default collection is every 3 hours and the digest is generated at 08:00 Asia/Karachi. The computer must be on and connected to the internet; this local scheduler is not a cloud service.

## API-based news discovery

RSS and Google News topic feeds are enabled by default and need no API key. To add NewsAPI discovery, create a key at https://newsapi.org/, set `NEWS_API_KEY` in `.env`, then restart the app. The application will register the API source on startup. NewsAPI access and limits depend on its current plan and terms. The query can be changed using `NEWS_API_QUERY`; `NEWS_API_PAGE_SIZE` is capped at 100.

## AI summaries
Set `AI_PROVIDER=openai`, `AI_MODEL` to a model available to your account, and `AI_API_KEY` in `.env`. Only bounded RSS excerpts are sent. Summaries are generated content, not independent verification. Without credentials or when AI calls fail, the app retains the excerpt and records fallback status. Configure provider costs and limits in your provider account.

## Email digest
Set `EMAIL_ENABLED=true`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `DIGEST_FROM_EMAIL`, and `DIGEST_TO_EMAIL` in `.env` only after your provider has approved the credentials. Generate a digest from the Run History page. Delivery attempts are logged independently. Never share your secret values.

## Tests
```powershell
pytest -q
```

## Backups
Stop collection/scheduler before making a simple copy of `data/technology_news.db`. For a live database, use SQLite's backup API. Periodically test restoring a backup.

## Project layout
- `app.py`: Flask routes and dashboard
- `database.py`: SQLite schema, indexes, and connection lifecycle
- `services/feed_fetcher.py`: RSS fetching, URL checks, limits, timeouts
- `services/article_normalizer.py`: URL/text/date normalization
- `services/classifier.py`: configurable categories and rule-based fallback
- `services/ai_client.py`: optional provider adapter and safe fallback
- `services/importance_ranker.py`: explainable 0–100 score
- `services/pipeline.py`: pipeline orchestration and run metrics
- `services/digest_builder.py`: digest selection and rendering
- `services/notifications/email_sender.py`: SMTP delivery tracking
- `run_scheduler.py`: separate scheduler process
- `tests/`: automated unit tests

## Known limitations
- RSS endpoints and third-party API plans can change or be retired; individual sources may fail temporarily. The pipeline records per-source failures and continues with the other sources.
- Rule-based classification is a fallback, not a guarantee of perfect topic assignment.
- Importance scores are heuristic and do not establish truth or quality.
- AI and email functionality require user-owned, correctly configured credentials and can incur provider charges.
- This local dashboard is intended for `127.0.0.1`; do not expose it publicly without authentication, secure cookies, CSRF protection, rate limiting, and production deployment configuration.
- Telegram/Discord adapters, multi-user accounts, cloud deployment, semantic clustering, and exports are not enabled in this first local release.


## GitHub Actions daily email automation

The repository includes `.github/workflows/daily-digest.yml`. Once pushed to the default branch and configured with repository Actions secrets, GitHub Actions runs the collection pipeline and sends a digest daily at 03:00 UTC (08:00 in Pakistan). You can also start a run manually from the repository's **Actions** tab. GitHub may delay scheduled runs during periods of high load.

### Required repository secrets

In GitHub, open **Settings → Secrets and variables → Actions → New repository secret** and add:

- `SMTP_USERNAME`: the Gmail address used to send the email (recommended: `aalyanofficial40@gmail.com`)
- `SMTP_PASSWORD`: a Google **App Password**, not your normal Gmail password
- `DIGEST_FROM_EMAIL`: the same Gmail sender address
- `FLASK_SECRET_KEY`: a long random secret value

The workflow sends the digest to `aalyanofficial40@gmail.com`. If you want AI summaries, also add `AI_PROVIDER` (`openai`), `AI_MODEL` (a model available to your API account), and `AI_API_KEY`. `NEWS_API_KEY` is optional; RSS sources work without it. Never commit `.env`, API keys, or Gmail app passwords.

For Gmail, enable 2-Step Verification on the sender account and create an App Password in the Google Account security settings if that option is available. If the App Password option is unavailable, use another SMTP provider.

### Push this project to GitHub (PowerShell)

Run these commands from the project directory, after creating an **empty** repository named `Daily_Technology_AI_Trends_Intelligence` under your GitHub account. Do not add a README or license when creating the remote repository.

```powershell
git init
git add .
git status
# Confirm .env and .venv are NOT listed before committing
git commit -m "Add technology intelligence system and daily email automation"
git branch -M main
git remote add origin https://github.com/AalyanShoukatKhan/Daily_Technology_AI_Trends_Intelligence.git
git push -u origin main
```

If Git says a remote named `origin` already exists, inspect it with `git remote -v` instead of adding it again. Authenticate with GitHub when prompted; never put a password or token in the remote URL.

**Important:** GitHub Actions runs the scheduled collection and email job; it does not keep the Flask dashboard continuously running or provide persistent SQLite history between fresh runners. To make the dashboard publicly accessible, deploy the Flask web app separately to a suitable hosting service and use a persistent database.
