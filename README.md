# Campus Feedback Bot 💬

An anonymous student feedback and quick-poll chatbot for classes, labs, and
campus facilities — built with Streamlit and plain (non-agentic) AI.

## Why this isn't "agentic AI"

The only AI in this app is a single-purpose, single-call sentiment
classifier (`ai_helpers.py`) and a deterministic keyword counter. Neither
function plans, chains tool calls, remembers past runs, or takes actions on
its own — they just take text in and return a label/number. There is no
autonomous loop deciding what to do next; every action (submitting feedback,
voting, creating a poll) is triggered directly by a human clicking a button.

## Features

- **Anonymous feedback**: students submit ratings + comments on Classes,
  Labs, or Facilities. No name, email, or login is ever stored.
- **Automatic sentiment tagging**: every comment is scored as
  Positive / Neutral / Negative using TextBlob (a pretrained, static model).
- **Admin dashboard**: password-protected view for faculty/admin with:
  - Sentiment breakdown chart
  - Average rating per category
  - Top keywords across all comments (spot recurring issues fast)
  - Full filterable feedback table + CSV export
- **Quick polls**: admin creates a poll with 2–4 options; students vote;
  live results as a bar chart.

## Setup

```bash
cd feedback_bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

TextBlob needs a small corpus download the first time:

```bash
python -m textblob.download_corpora
```

## Run

```bash
streamlit run app.py
```

This opens the app at `http://localhost:8501`.

- **Student View** is the default landing tab.
- **Admin View** requires a password (default: `admin123` — change the
  `ADMIN_PASSWORD` variable at the top of `app.py` before any real deployment).

## Data storage

All data lives in a local SQLite file, `feedback_bot.db`, created
automatically on first run. Delete this file to reset all data.

## Possible extensions

- Deploy on Streamlit Community Cloud for free public hosting.
- Swap TextBlob for a transformer-based sentiment model (e.g. via
  `transformers`) if you want higher accuracy — still a single-shot
  classification call, still non-agentic.
- Add a simple bar/line chart of feedback volume over time.
- Add category-specific poll targeting (e.g. only show a lab poll to
  students who selected "Lab" recently).
