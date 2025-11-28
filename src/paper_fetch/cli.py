import argparse
import os
import sys
import datetime
import re
import questionary
from .fetchers.arxiv import ArxivFetcher
from .fetchers.ieee import IeeeFetcher

def get_default_output_dir(query: str) -> str:
    """Generate default output directory based on date and query."""
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    # Sanitize query for file path
    safe_query = re.sub(r'[^\w\-_]', '_', query)[:50]
    return os.path.join("downloads", f"{date_str}_{safe_query}")

def interactive_mode():
    """Run the CLI in interactive mode using questionary."""
    print("Welcome to PaperFetch Interactive Mode!")

    # 1. Source Selection
    source = questionary.select(
        "Select source:",
        choices=["arxiv", "ieee"]
    ).ask()

    if not source:
        return # Cancelled

    # 2. Query
    query = questionary.text("Search query:").ask()
    if not query:
        return

    # Default settings
    settings = {
        "search_limit": 10,
        "download_limit": None,
        "start_year": None,
        "end_year": None,
        "sort_by": "relevance",
        "sort_order": "desc",
        "open_access_only": False,
        "downloadable_only": False,
        "output_dir": None, # Will be set dynamically if None
        "use_source_subdir": True
    }

    # Helper to get hit count
    def check_hits(current_query):
        print(f"Checking potential hits for '{current_query}'...")
        temp_client = ArxivFetcher() if source == "arxiv" else IeeeFetcher()
        try:
            total = temp_client.get_total_results(
                query=current_query,
                start_year=settings["start_year"],
                end_year=settings["end_year"],
                open_access_only=settings["open_access_only"]
            )
            return total
        except Exception as e:
            print(f"Error checking hits: {e}")
            return -1

    # Initial Hit Count
    total_hits = check_hits(query)
    print(f"Found {total_hits if total_hits >= 0 else 'Unknown'} potential papers.")

    # 3. Main Menu Loop
    while True:
        # Resolve current output dir for display
        current_out_dir = settings['output_dir'] if settings['output_dir'] else get_default_output_dir(query)
        if settings['use_source_subdir']:
            display_path = os.path.join(current_out_dir, source)
        else:
            display_path = current_out_dir

        print("\n--- Current Settings ---")
        print(f"Source:          {source}")
        print(f"Query:           {query} (Hits: {total_hits if total_hits >= 0 else 'Unknown'})")
        print(f"Search Limit:    {settings['search_limit'] if settings['search_limit'] is not None else 'Unlimited'}")
        print(f"Sort:            {settings['sort_by']} ({settings['sort_order']})")
        filters = []
        if source == "ieee" and settings['open_access_only']:
            filters.append("Open Access")
        if settings['downloadable_only']:
            filters.append("Downloadable Only")
        if settings['start_year'] or settings['end_year']:
            filters.append(f"Year: {settings['start_year'] or '*'} - {settings['end_year'] or '*'}")
        print(f"Filters:         {', '.join(filters) if filters else 'None'}")
        print(f"Output Dir:      {display_path} (Auto-generated)" if settings['output_dir'] is None else f"Output Dir:      {display_path}")
        print("------------------------")

        action = questionary.select(
            "What would you like to do?",
            choices=[
                questionary.Choice("🚀 Start Search", value="search"),
                questionary.Choice("🔢 Change Limit", value="limit"),
                questionary.Choice("🔃 Change Sort", value="sort"),
                questionary.Choice("🔍 Change Query", value="query"),
                questionary.Choice("⚙️ Other Filters", value="filters"),
                questionary.Choice("📂 Change Output Dir", value="output"),
                questionary.Choice("❌ Quit", value="quit")
            ]
        ).ask()

        if action == "quit":
            print("Exiting.")
            return

        elif action == "search":
            break

        elif action == "limit":
            limit_str = questionary.text("Search limit (empty for 10, '0' or 'all' for unlimited):").ask()
            if limit_str and limit_str.lower() in ['0', 'all']:
                print("Warning: Unlimited search selected. This may trigger rate limits.")
                settings["search_limit"] = None
            elif limit_str and limit_str.isdigit():
                settings["search_limit"] = int(limit_str)
            else:
                settings["search_limit"] = 10

            dl_limit_str = questionary.text("Download limit (empty for unlimited):").ask()
            if dl_limit_str and dl_limit_str.isdigit():
                settings["download_limit"] = int(dl_limit_str)
            else:
                settings["download_limit"] = None

        elif action == "sort":
            settings["sort_by"] = questionary.select(
                "Sort by:",
                choices=["relevance", "date"],
                default=settings["sort_by"]
            ).ask()
            settings["sort_order"] = questionary.select(
                "Sort order:",
                choices=["desc", "asc"],
                default=settings["sort_order"]
            ).ask()

        elif action == "query":
            new_query = questionary.text("New search query:", default=query).ask()
            if new_query:
                query = new_query
                total_hits = check_hits(query)

        elif action == "filters":
            if source == "ieee":
                settings["open_access_only"] = questionary.confirm("Open Access only?", default=settings["open_access_only"]).ask()

            settings["downloadable_only"] = questionary.confirm("Show downloadable papers only?", default=settings["downloadable_only"]).ask()

            sy = questionary.text("Start year (optional, empty to clear):", default=str(settings["start_year"]) if settings["start_year"] else "").ask()
            if sy and sy.isdigit():
                settings["start_year"] = int(sy)
            else:
                settings["start_year"] = None

            ey = questionary.text("End year (optional, empty to clear):", default=str(settings["end_year"]) if settings["end_year"] else "").ask()
            if ey and ey.isdigit():
                settings["end_year"] = int(ey)
            else:
                settings["end_year"] = None

            # Re-check hits if filters changed (especially date/OA)
            total_hits = check_hits(query)

        elif action == "output":
            out_input = questionary.text("Output directory (empty for default):", default=settings["output_dir"] if settings["output_dir"] else "").ask()
            if out_input:
                settings["output_dir"] = out_input
            else:
                settings["output_dir"] = None # Reset to default

            settings["use_source_subdir"] = questionary.confirm("Create source subdirectory (e.g. /arxiv)?", default=settings["use_source_subdir"]).ask()

    # 4. Search Execution
    print(f"\nSearching {source} for '{query}'...")
    client = ArxivFetcher() if source == "arxiv" else IeeeFetcher()

    try:
        # Construct args for search
        search_args = {
            "query": query,
            "sort_by": settings["sort_by"],
            "sort_order": settings["sort_order"],
            "start_year": settings["start_year"],
            "end_year": settings["end_year"]
        }
        if settings["search_limit"] is not None:
            search_args["max_results"] = settings["search_limit"]

        if source == "ieee":
            search_args["open_access_only"] = settings["open_access_only"]

        results = client.search(**search_args)
    except Exception as e:
        print(f"Error during search: {e}")
        return

    if not results:
        print("No results found.")
        return

    # Filter if requested
    if settings["downloadable_only"]:
        results = [p for p in results if p.is_downloadable]
        if not results:
            print("No downloadable results found.")
            return

    # 5. Select Papers
    choices = []
    for p in results:
        status = "[DL]" if p.is_downloadable else "[--]"
        # Limit title length for display
        title_display = (p.title[:60] + '..') if len(p.title) > 60 else p.title
        label = f"{status} {title_display} ({p.published_date.year if p.published_date else '?'})"
        choices.append(questionary.Choice(label, value=p))

    if not choices:
        print("No papers to display.")
        return

    selected_papers = questionary.checkbox(
        f"Found {len(results)} papers. Select to download (Space to select, Enter to confirm):",
        choices=choices
    ).ask()

    if not selected_papers:
        print("No papers selected.")
        return

    # Apply download limit if set
    if settings["download_limit"] is not None and len(selected_papers) > settings["download_limit"]:
        print(f"\nWarning: Selection ({len(selected_papers)}) exceeds limit ({settings['download_limit']}). Truncating.")
        selected_papers = selected_papers[:settings["download_limit"]]

    # 6. Download
    # Determine final output directory
    base_output_dir = settings['output_dir'] if settings['output_dir'] else get_default_output_dir(query)
    if settings['use_source_subdir']:
        final_output_dir = os.path.join(base_output_dir, source)
    else:
        final_output_dir = base_output_dir

    print(f"\nDownloading {len(selected_papers)} papers to '{final_output_dir}'...")

    for paper in selected_papers:
        print(f"Downloading: {paper.title}...")
        try:
            path = client.download_pdf(paper, final_output_dir)
            print(f"  -> Saved to: {path}")
        except Exception as e:
            print(f"  -> Failed: {e}")

    print("\nDone.")

def main():
    parser = argparse.ArgumentParser(description="PaperFetch CLI")
    parser.add_argument("--source", choices=["arxiv", "ieee"], required=False, help="Source to fetch from")
    parser.add_argument("--query", required=False, help="Search query")
    parser.add_argument("--search-limit", type=int, default=10, help="Max results to search (default: 10, 0 for unlimited)")
    parser.add_argument("--download-limit", type=int, default=None, help="Max results to download (default: unlimited)")
    parser.add_argument("--output", default=None, help="Output directory (default: ./downloads/{YYYYMMDD}_{Query})")
    parser.add_argument("--no-source-subdir", action="store_true", help="Do not create a source-specific subdirectory (e.g. /arxiv)")
    parser.add_argument("--downloadable-only", action="store_true", help="Filter results to show only downloadable papers")
    parser.add_argument("--open-access-only", action="store_true", help="Search for Open Access papers only (IEEE only)")
    parser.add_argument("--sort-by", choices=["relevance", "date"], default="relevance", help="Sort by relevance or date")
    parser.add_argument("--sort-order", choices=["desc", "asc"], default="desc", help="Sort order (descending or ascending)")
    parser.add_argument("--start-year", type=int, help="Filter by start year")
    parser.add_argument("--end-year", type=int, help="Filter by end year")

    # Check if any args are passed. If not, go interactive.
    if len(sys.argv) == 1:
        interactive_mode()
        return

    args = parser.parse_args()

    # If args are provided but source/query are missing, we might need to error or fallback.
    # But since we made them optional in add_argument to support the "no args = interactive" check above,
    # we must enforce them here if we are NOT in interactive mode.
    if not args.source or not args.query:
        print("Error: --source and --query are required in non-interactive mode.")
        parser.print_help()
        return

    print(f"Searching {args.source} for '{args.query}'...")

    client = None
    if args.source == "arxiv":
        client = ArxivFetcher()
    elif args.source == "ieee":
        client = IeeeFetcher()

    # Handle 0 as unlimited
    search_limit_val = args.search_limit
    if search_limit_val == 0:
        print("Warning: Unlimited search selected. This may trigger rate limits.")
        search_limit_val = None

    try:
        # Pass open_access_only to search if supported (IEEE)
        if args.source == "ieee":
            results = client.search(
                args.query,
                max_results=search_limit_val,
                open_access_only=args.open_access_only,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
                start_year=args.start_year,
                end_year=args.end_year
            )
        else:
            results = client.search(
                args.query,
                max_results=search_limit_val,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
                start_year=args.start_year,
                end_year=args.end_year
            )
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

    # Apply download limit if set
    if args.download_limit is not None and len(selected_indices) > args.download_limit:
        print(f"\nWarning: Selection ({len(selected_indices)}) exceeds download limit ({args.download_limit}).")
        print(f"Truncating to first {args.download_limit} papers.")
        selected_indices = selected_indices[:args.download_limit]

    # Determine final output directory
    base_output_dir = args.output if args.output else get_default_output_dir(args.query)
    if not args.no_source_subdir:
        final_output_dir = os.path.join(base_output_dir, args.source)
    else:
        final_output_dir = base_output_dir

    print(f"\nDownloading {len(selected_indices)} papers to '{final_output_dir}'...")

    for idx in selected_indices:
        paper = results[idx]
        print(f"Downloading: {paper.title}...")
        try:
            path = client.download_pdf(paper, final_output_dir)
            print(f"  -> Saved to: {path}")
        except Exception as e:
            print(f"  -> Failed: {e}")

    print("\nDone.")

if __name__ == "__main__":
    main()
