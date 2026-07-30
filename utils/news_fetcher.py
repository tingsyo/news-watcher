import os
import re
import datetime
import requests
from typing import List, Dict, Any

class NewsAlertFetcher:
    """
    Fetches news from NewsAPI or Google RSS, ranks articles according to:
    1. Keyword order index match
    2. Match multiplicity boost
    3. Temporal proximity
    4. Popularity / view metrics
    Saves an HTML report locally with a timestamp filename.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY", "")

    def fetch_news(self, keywords: List[str], time_span_hours: int = 72) -> List[Dict[str, Any]]:
        query = " OR ".join(keywords)
        from_date = (datetime.datetime.now() - datetime.timedelta(hours=time_span_hours)).isoformat()
        
        if self.api_key:
            url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=popularity&apiKey={self.api_key}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("articles", [])
            except Exception as e:
                print(f"[Warning] Failed to fetch from NewsAPI: {e}")
        
        # Fallback sample news articles if API key is missing or request fails
        return self._generate_sample_articles(keywords, time_span_hours)

    def rank_articles(self, articles: List[Dict[str, Any]], keywords: List[str], time_span_hours: int) -> List[Dict[str, Any]]:
        now = datetime.datetime.now()
        time_span_seconds = time_span_hours * 3600
        normalized_keywords = [k.strip().lower() for k in keywords if k.strip()]
        
        ranked = []
        for art in articles:
            # Parse published date
            pub_str = art.get("publishedAt", "")
            try:
                pub_dt = datetime.datetime.fromisoformat(pub_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                pub_dt = now

            age_seconds = (now - pub_dt).total_seconds()
            if age_seconds > time_span_seconds and time_span_hours > 0:
                continue # Filter out articles outside timespan

            title = art.get("title", "") or ""
            desc = art.get("description", "") or ""
            full_text = f"{title} {desc}".lower()

            matched_keywords = []
            multiplicity_count = 0
            keyword_order_score = 0

            # 1. Keyword Order & Multiplicity
            for idx, kw in enumerate(normalized_keywords):
                matches = re.findall(re.escape(kw), full_text)
                if matches:
                    matched_keywords.append(keywords[idx])
                    multiplicity_count += len(matches)
                    order_weight = max(1, len(normalized_keywords) - idx)
                    keyword_order_score += order_weight * len(matches) * 10

            multiplicity_boost = 1 + (len(matched_keywords) * 0.5) + (multiplicity_count * 0.2)

            # 2. Temporal Proximity Score (0 - 100)
            hours_old = age_seconds / 3600
            temporal_score = max(0, 100 * (1 - hours_old / max(1, time_span_hours)))

            # 3. Popularity Score (0 - 100)
            #popularity_raw = art.get("popularity", 5000)
            popularity_raw = articles.index(art)
            popularity_score = (1 - (popularity_raw/len(articles)))*100

            # Final Composite Score
            composite_score = round(
                (keyword_order_score * multiplicity_boost) + 
                (temporal_score * 0.8) + 
                (popularity_score * 0.4)
            )

            art_entry = dict(art)
            art_entry.update({
                "matchedKeywords": matched_keywords,
                "multiplicityCount": multiplicity_count,
                "keywordOrderScore": round(keyword_order_score),
                "temporalScore": round(temporal_score),
                "popularityScore": round(popularity_score),
                "compositeScore": composite_score
            })
            ranked.append(art_entry)

        # Sort descending by composite score
        ranked.sort(key=lambda x: x["compositeScore"], reverse=True)
        return ranked

    def generate_html_report(self, articles: List[Dict[str, Any]], keywords: List[str], time_span_hours: int, period_hours: int) -> str:
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_alert_{timestamp_file}.html"

        kw_pills = "".join([f'<span style="background:#e0e7ff;color:#3730a3;padding:4px 10px;border-radius:12px;font-size:12px;margin-right:4px;">#{i+1} {kw}</span>' for i, kw in enumerate(keywords)])

        cards_html = ""
        for idx, art in enumerate(articles):
            matches_html = "".join([f'<span style="background:#dcfce7;color:#166534;padding:2px 6px;border-radius:4px;font-size:11px;margin-right:4px;">✓ {m}</span>' for m in art.get("matchedKeywords", [])])
            
            cards_html += f"""
            <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-size:12px;color:#64748b;font-weight:600;">{art.get('source', {}).get('name', 'News')}</span>
                    <span style="background:#fef3c7;color:#78350f;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:bold;">Rank #{idx+1} (Score: {art.get('compositeScore')})</span>
                </div>
                <h2 style="font-size:18px;margin:0 0 8px 0;"><a href="{art.get('url', '#')}" target="_blank" style="color:#0f172a;text-decoration:none;">{art.get('title')}</a></h2>
                <p style="color:#475569;font-size:14px;line-height:1.5;">{art.get('description')}</p>
                <div style="margin-top:12px;padding-top:12px;border-top:1px solid #f1f5f9;display:flex;justify-content:space-between;font-size:12px;color:#64748b;">
                    <div>Matched: {matches_html}</div>
                    <div>Matches: {art.get('multiplicityCount')} | Freshness: {art.get('temporalScore')}% | Popularity: {art.get('popularityScore')}/100</div>
                </div>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>News Alert Report - {timestamp_str}</title>
    <style>body {{ font-family: system-ui, sans-serif; background: #f8fafc; padding: 32px; max-width: 900px; margin: 0 auto; color: #1e293b; }}</style>
</head>
<body>
    <div style="background:white;border:1px solid #e2e8f0;border-radius:16px;padding:24px;margin-bottom:24px;">
        <h1 style="margin:0 0 8px 0;font-size:24px;">News Alert Digest</h1>
        <p style="color:#64748b;font-size:13px;margin:0 0 16px 0;">Generated: {timestamp_str} | Timespan: {time_span_hours}h | Period: {period_hours}h</p>
        <div>Keywords: {kw_pills}</div>
    </div>
    {cards_html}
</body>
</html>"""

        # Save to file
        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        # For publishing
        with open('temp.html', "w", encoding="utf-8") as f:
            f.write(html_content)

        return filepath, filename, html_content

    def _generate_sample_articles(self, keywords: List[str], time_span_hours: int) -> List[Dict[str, Any]]:
        now = datetime.datetime.now()
        return [
            {
                "title": f"New Advances in {' and '.join(keywords[:2])} Transform Global Markets",
                "description": f"An in-depth analysis on how {keywords[0]} and {keywords[1]} interact with modern technology and education standards.",
                "url": "https://example.com/news/1",
                "source": {"name": "Tech Weekly"},
                "publishedAt": (now - datetime.timedelta(hours=4)).isoformat() + "Z",
                "popularity": 8500
            },
            {
                "title": f"Future of {keywords[0].capitalize()} and Economy Infrastructure",
                "description": f"Experts evaluate technology breakthroughs impacting both local education institutions and international economy stability.",
                "url": "https://example.com/news/2",
                "source": {"name": "Global Economy Review"},
                "publishedAt": (now - datetime.timedelta(hours=14)).isoformat() + "Z",
                "popularity": 12000
            }
        ]

if __name__ == "__main__":
    fetcher = NewsAlertFetcher()
    raw = fetcher.fetch_news(["education", "AI", "technology", "economy"], time_span_hours=72)
    #print("RAW DATA: "+str(len(raw)))
    ranked = fetcher.rank_articles(raw, ["education", "AI", "schools", "university", "parenting"], time_span_hours=72)
    #print("RANKED DATA: "+str(len(ranked)))
    path, fname, _ = fetcher.generate_html_report(ranked, ["education", "AI", "technology", "economy"], 72, 24)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+f"\tSaved news alert report to {path}")
