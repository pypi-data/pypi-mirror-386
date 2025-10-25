#!/usr/bin/env python3
"""
Fetch and display top Hacker News headlines in a clean, robust, and Pythonic way.

Features:
- Type hints
- Error handling
- Configurable via CLI
- Logging instead of print
- Separation of concerns
- PEP 8 compliance
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.logging import RichHandler

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("hn_headlines")

# Constants
BASE_URL = "https://news.ycombinator.com"
DEFAULT_LIMIT = 5
MAX_LIMIT = 30  # HN front page typically shows 30 items


class HeadlineFetcher:
    """Encapsulates fetching logic with proper error handling and structure."""

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or httpx.Client(timeout=10.0)

    def fetch_headlines(self, limit: int) -> List[str]:
        """
        Fetch the top `limit` headlines from Hacker News.

        Args:
            limit: Number of headlines to return (capped at MAX_LIMIT).

        Returns:
            List of headline strings.

        Raises:
            RuntimeError: If request fails or parsing errors occur.
        """
        limit = min(limit, MAX_LIMIT)
        log.debug("Fetching headlines (limit=%d)", limit)

        try:
            response = self.client.get(BASE_URL)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            log.error("HTTP error occurred: %s", exc)
            raise RuntimeError(f"Failed to fetch page: {exc}") from exc
        except httpx.RequestError as exc:
            log.error("Request failed: %s", exc)
            raise RuntimeError(f"Network error: {exc}") from exc

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            title_elements = soup.select(".titleline > a")
            headlines = []
            for elem in title_elements[:limit]:
                title = elem.get_text(strip=True)
                href = elem.get("href")
                # Some links are relative (e.g. "item?id=..."), so normalize them
                if href and href.startswith("item?id="):
                    href = f"{BASE_URL}/{href}"
                headlines.append((title, href or BASE_URL))
            return headlines
        except Exception as exc:
            log.error("Failed to parse HTML: %s", exc)
            raise RuntimeError("Failed to extract headlines") from exc

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch top Hacker News headlines",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        default=DEFAULT_LIMIT,
        help="Number of headlines to display",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def display_headlines(console: Console, headlines: List[str]) -> None:
    """Display headlines in a formatted, rich-styled list."""
    if not headlines:
        console.print("[yellow]No headlines found.[/yellow]")
        return

    console.rule(f"[bold blue]Top {len(headlines)} Hacker News Headlines[/bold blue]")
    for idx, (title, link) in enumerate(headlines, start=1):
        console.print(f"[green]{idx:2}.[/green] [link={link}]{title}[/link]")


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    limit = max(1, args.number)  # Ensure at least 1
    console = Console()

    fetcher = HeadlineFetcher()
    try:
        headlines = fetcher.fetch_headlines(limit)
        display_headlines(console, headlines)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1
    finally:
        fetcher.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
