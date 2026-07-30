# news-watcher

Fetching and ordering recent news articles.

## Introduction
This is a personal project under development. I need regular news aalerts from various sources on specific topics. I want to develop a `python`-based toolset to retrieve and order recent news, and then put it to `cron` jobs.

## Parameters
- **keywords**: `List[str]`, a set of keywords used for news retrieval and ordering.
- **time-span**: `int`, number of hours to look back in the past during news retrieval.

## Tools
- `utils/fetch_news.py`: the main script for the "retrieval -> ordering -> report" workflow.
- `utils/fastapi_app.py`: the web-based interface for the main script.

