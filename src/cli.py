import argparse
import os
import sys
from typing import List
from .fetchers.arxiv import ArxivFetcher
from .fetchers.ieee import IeeeFetcher
from .fetchers.models import Paper

def main():
    parser = argparse.ArgumentParser(description="PaperFetch CLI")
    parser.add_argument("--source", choices=["arxiv", "ieee"], required=True, help="Source to crawl from")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--limit", type=int, default=10, help="Max results to fetch")
    parser.add_argument("--output", default="downloads", help="Output directory")
    parser.add_argument("--downloadable-only", action="store_true", help="Filter results to show only downloadable papers")
    parser.add_argument("--open-access-only", action="store_true", help="Search for Open Access papers only (IEEE only)")

    args = parser.parse_args()

    print(f"Searching {args.source} for '{args.query}'...")

    client = None
    if args.source == "arxiv":
        client = ArxivFetcher()
    elif args.source == "ieee":
        client = IeeeFetcher(headless=True)

    try:
        # Pass open_access_only to search if supported (IEEE)
        if args.source == "ieee":
            results = client.search(args.query, max_results=args.limit, open_access_only=args.open_access_only)
        else:
            results = client.search(args.query, max_results=args.limit)
    except Exception as e:
        print(f"Error during search: {e}")
        return

    if not results:
        print("No results found.")
        return

    # Filter if requested (Client-side filter)
    if args.downloadable_only:
        results = [p for p in results if p.is_downloadable]
        if not results:
            print("No downloadable results found in the search results.")
            return

    print(f"\nFound {len(results)} papers:")
    for i, paper in enumerate(results):
        status = "[Downloadable]" if paper.is_downloadable else "[Restricted?]"
        print(f"[{i+1}] {status} {paper.title}")
        print(f"    Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
        print(f"    Year: {paper.published_date.year if paper.published_date else 'Unknown'}")
        print(f"    URL: {paper.url}")
        print("-" * 40)

    print("\nEnter numbers to download (e.g., '1 3 5'), 'all' for all, or 'q' to quit:")
    choice = input("> ").strip().lower()

    if choice == 'q':
        print("Exiting.")
        return

    selected_indices = []
    if choice == 'all':
        selected_indices = range(len(results))
    else:
        try:
            parts = choice.split()
            for part in parts:
                idx = int(part) - 1
                if 0 <= idx < len(results):
                    selected_indices.append(idx)
                else:
                    print(f"Warning: Invalid index {part}")
        except ValueError:
            print("Invalid input.")
            return

    if not selected_indices:
        print("No papers selected.")
        return

    print(f"\nDownloading {len(selected_indices)} papers to '{args.output}'...")

    for idx in selected_indices:
        paper = results[idx]
        print(f"Downloading: {paper.title}...")
        try:
            path = client.download_pdf(paper, args.output)
            print(f"  -> Saved to: {path}")
        except Exception as e:
            print(f"  -> Failed: {e}")

    print("\nDone.")

if __name__ == "__main__":
    main()
