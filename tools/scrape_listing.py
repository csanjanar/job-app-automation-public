#!/usr/bin/env python3
"""Scrape a job listing URL using Firecrawl → clean markdown saved to .tmp/"""
import argparse
import sys
import os
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()

# Real listing pages run 10k-17k chars; an un-hydrated SPA shell (e.g. MyCareersFuture
# serving its bare app skeleton before Angular/React renders, sometimes triggered by
# bot-detection degrading a proxy session mid-run) comes back around 81 chars.
SHELL_MARKDOWN_MAX_LEN = 200
SHELL_TITLE = "MyCareersFuture Singapore"


def is_shell_page(markdown: str, title: str) -> bool:
    """Detect an un-hydrated SPA shell response rather than real listing content."""
    if markdown is None:
        return True
    stripped = markdown.strip()
    if len(stripped) < SHELL_MARKDOWN_MAX_LEN:
        return True
    if title.strip() == SHELL_TITLE and len(stripped) < 1000:
        return True
    return False


def scrape_listing(url: str, max_retries: int = 3, backoff_base: int = 15) -> dict:
    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
    last_result = None
    for attempt in range(max_retries):
        kwargs = {"formats": ["markdown"]}
        if attempt > 0:
            kwargs["wait_for"] = 3000  # let the SPA hydrate before snapshotting
            kwargs["proxy"] = "stealth"  # request a fresh proxy identity

        result = app.scrape_url(url, **kwargs)
        markdown = result.markdown
        title = (result.metadata.title if hasattr(result.metadata, "title") else "") if result.metadata else ""
        last_result = {
            "url": url,
            "markdown": markdown,
            "title": title,
            "source": url.split("/")[2] if "/" in url else url,
        }

        if not is_shell_page(markdown, title):
            if attempt > 0:
                print(f"Recovered on attempt {attempt + 1}", file=sys.stderr)
            return last_result

        if attempt < max_retries - 1:
            delay = backoff_base * (attempt + 1)
            print(f"Shell page detected (attempt {attempt + 1}/{max_retries}), retrying in {delay}s", file=sys.stderr)
            time.sleep(delay)

    last_result["shell_page_detected"] = True
    return last_result


def url_to_filename(url: str) -> str:
    safe = re.sub(r"[^\w]", "_", url.replace("https://", "").replace("http://", ""))
    return safe[:80]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--max-retries", type=int, default=3, help="Max scrape attempts before giving up (default: 3)")
    parser.add_argument("--backoff-base", type=int, default=15, help="Base backoff seconds between retries (default: 15)")
    args = parser.parse_args()

    print(f"Scraping: {args.url}", file=sys.stderr)

    data = scrape_listing(args.url, max_retries=args.max_retries, backoff_base=args.backoff_base)

    tmp_dir = Path(".tmp")
    tmp_dir.mkdir(exist_ok=True)
    output_path = tmp_dir / f"{url_to_filename(args.url)}.json"

    output_path.write_text(json.dumps(data, indent=2))
    print(f"Saved to {output_path}", file=sys.stderr)
    print(json.dumps(data, indent=2))
