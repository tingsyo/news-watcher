from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import datetime
from news_fetcher import NewsAlertFetcher

app = FastAPI(
    title="News Alert Workflow API",
    description="Trigger news alert generation based on ordered keywords, multiplicity boost, and temporal proximity."
)

fetcher = NewsAlertFetcher()

class AlertRequest(BaseModel):
    keywords: List[str] = ["education", "AI", "technology", "economy"]
    time_span_hours: int = 72
    period_hours: int = 24
    news_api_key: Optional[str] = None

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "News Alert Workflow Agent API",
        "endpoints": {
            "trigger_alert": "POST /trigger-news-alert",
            "list_reports": "GET /reports",
            "get_report_html": "GET /reports/{filename}"
        }
    }

@app.post("/trigger-news-alert")
def trigger_news_alert(req: AlertRequest):
    """
    On-Demand trigger (e.g., invoked via Crontab or Webhook).
    Fetches articles, ranks by ordered keyword priority + multiplicity boost + age + popularity,
    and generates a timestamped HTML file saved locally and rendered via endpoint.
    """
    if req.news_api_key:
        fetcher.api_key = req.news_api_key

    raw_articles = fetcher.fetch_news(req.keywords, req.time_span_hours)
    ranked = fetcher.rank_articles(raw_articles, req.keywords, req.time_span_hours)
    
    filepath, filename, html_content = fetcher.generate_html_report(
        ranked, req.keywords, req.time_span_hours, req.period_hours
    )

    return {
        "success": True,
        "filename": filename,
        "filepath": filepath,
        "render_url": f"/reports/{filename}",
        "articles_matched": len(ranked),
        "generated_at": datetime.datetime.now().isoformat()
    }

@app.get("/reports", response_model=List[str])
def list_reports():
    """Lists all saved timestamped HTML reports."""
    reports_dir = "reports"
    if not os.path.exists(reportsDir := "reports"):
        return []
    files = [f for f in os.listdir(reports_dir) if f.endswith(".html")]
    return sorted(files, reverse=True)

@app.get("/reports/{filename}", response_class=HTMLResponse)
def get_report_html(filename: str):
    """Render saved HTML report directly in the browser."""
    filepath = os.path.join("reports", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
