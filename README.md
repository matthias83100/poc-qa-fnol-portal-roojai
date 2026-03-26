# QA Portal - FNOL POC

This is a Proof of Concept (POC) for an AI-powered Quality Assurance (QA) Dashboard designed to process and analyze FNOL (First Notice of Loss) call recordings. It uses LLMs to evaluate agent performance, extract customer emotions, and track processing costs.

## 🏗 Architecture

The system is designed with a **Three-Tier Database Architecture** using Django's Database Routers to separate concerns and ensure high performance:

1.  **Application Database (`db.sqlite3`)**: Stores native Django data (Migrations, Admin, App Settings).
2.  **Raw AI Data (`raw_data.sqlite3`)**: Stores the massive logs of AI-processed transcripts, utterances, and question-by-question evaluations. (Optimized for Read-Only in production).
3.  **Aggregated Statistics (`aggregated_data.sqlite3`)**: Stores pre-computed daily metrics for agents and the general overview. This ensures the dashboard charts load instantly without recalculating raw data on every request.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- `pip install -r requirements.txt`

### 2. Database Setup
You must initialize all three databases using the following migration commands:
```bash
python manage.py migrate
python manage.py migrate --database=raw_data
python manage.py migrate --database=aggregated_data
```

### 3. Populating Mock Data (Development)
To see the dashboard in action with sample data:
```bash
# 1. Generate Raw Call Logs
python manage.py generate_mock_data

# 2. Process Aggregations for the Dashboard
python manage.py generate_aggregated_mocks
```

## 📊 Key Features

- **Overview Dashboard**: High-level metrics including total calls, agent counts, average QA scores, category breakdowns (Plotly.js), and cost tracking.
- **Agent Detail View**: Granular performance tracking for individual agents, including QA progression, speaker distribution, language usage, and emotion analysis.
- **Cost Analysis**: Transparency into LLM API expenditure.
- **Webhook API**: An endpoint (`/api/trigger-aggregation/`) designed for external cronjobs to trigger immediate stat updates every 15 minutes as new raw data arrives.

## 🛠 Tech Stack
- **Backend**: Django (Python)
- **Frontend**: Vanilla JS, HTML5, CSS3 (Premium Dark Theme)
- **Charting**: Plotly.js
- **Database**: Multiple SQLite instances (Configured for easy migration to SQL Server/Postgres)

## 🐳 External Data Integration
In a production setup, the `raw_data` database is populated by an external AI pipeline. After the pipeline inserts new records, it should trigger the aggregation refresh via the API:
```bash
curl -X POST http://your-app/api/trigger-aggregation/ -d '{"date": "2024-03-26"}'
```
