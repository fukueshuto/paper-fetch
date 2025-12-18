from mcp.server.fastmcp import FastMCP
from typing import List, Optional
from .fetchers.arxiv import ArxivFetcher
from .fetchers.ieee import IeeeFetcher
from .fetchers.threegpp import ThreeGPPFetcher
from .fetchers.uspto import UsptoFetcher
from .fetchers.models import Paper
from .exporters.notebooklm import upload_to_notebooklm
from datetime import date
import re

mcp = FastMCP("paper-fetch")

# Initialize clients
arxiv_client = ArxivFetcher()
ieee_client = IeeeFetcher()
threegpp_client = ThreeGPPFetcher()
uspto_client = UsptoFetcher()


@mcp.tool()
def search_papers(
    source: str, query: str, limit: int = 5, open_access_only: bool = False
) -> str:
    """
    Search for papers from Arxiv, IEEE Xplore, 3GPP, or USPTO.

    Args:
        source: "arxiv", "ieee", "3gpp", or "uspto"
        query: Search query (For 3GPP, this must be a valid directory URL)
        limit: Maximum number of results (default 5)
        open_access_only: If True, search only for Open Access papers (IEEE only)
    """
    s = source.lower()
    if s == "arxiv":
        client = arxiv_client
    elif s == "ieee":
        client = ieee_client
    elif s == "3gpp":
        client = threegpp_client
    elif s == "uspto":
        client = uspto_client
    else:
        return f"Error: Unknown source '{source}'. Use 'arxiv', 'ieee', '3gpp', or 'uspto'."

    try:
        kwargs = {"max_results": limit}
        if s == "ieee":
            kwargs["open_access_only"] = open_access_only

        results = client.search(query, **kwargs)

        # Return a JSON string.
        import json

        return json.dumps(
            [p.to_dict() for p in results], ensure_ascii=False, default=str
        )
    except Exception as e:
        return f"Error searching {source}: {str(e)}"


@mcp.tool()
def download_paper(
    url: str,
    title: str,
    authors: List[str],
    year: Optional[int] = None,
    save_dir: str = "downloads",
) -> str:
    """
    Download a paper's PDF given its metadata.
    Automatically detects source from URL (Arxiv, IEEE, 3GPP, USPTO).

    Args:
        url: URL of the paper
        title: Title of the paper (for filename)
        authors: List of authors (for filename)
        year: Publication year (for filename)
        save_dir: Directory to save the PDF (default "downloads")
    """
    # Infer source from URL
    source = "unknown"
    client = None
    pdf_url = url
    paper_id = "unknown"

    if "arxiv.org" in url:
        source = "arxiv"
        client = arxiv_client
        pdf_url = url.replace("/abs/", "/pdf/")
        if not pdf_url.endswith(".pdf"):
            pdf_url += ".pdf"

    elif "ieeexplore.ieee.org" in url:
        source = "ieee"
        client = ieee_client
        match = re.search(r"document/(\d+)", url)
        if match:
            paper_id = match.group(1)

    elif "3gpp.org" in url:
        source = "3gpp"
        client = threegpp_client
        # 3GPP often provides direct file URLs, so paper_id is filename
        import os

        paper_id = os.path.basename(url)

    elif "patents.google.com" in url or "uspto.gov" in url or "patentsview.org" in url:
        source = "uspto"
        client = uspto_client
        # Attempt to extract ID (e.g., patent number) if possible, but optional as fetcher handles logic
        # For patents.google.com/patent/US12345/en -> US12345
        match = re.search(r"patent/([A-Za-z0-9]+)", url)
        if match:
            paper_id = match.group(1)

    else:
        return f"Error: Could not determine source from URL '{url}'"

    # Construct Paper object
    published_date = None
    if year:
        published_date = date(year, 1, 1)

    paper = Paper(
        source=source,
        id=paper_id,
        title=title,
        authors=authors,
        abstract="",
        url=url,
        pdf_url=pdf_url,
        published_date=published_date,
    )

    try:
        path = client.download_pdf(paper, save_dir)
        return f"Successfully downloaded to: {path}"
    except Exception as e:
        return f"Error downloading paper: {str(e)}"


@mcp.tool()
def upload_to_notebooklm_tool(
    upload_dir: str = "downloads",
    mode: str = "new",
    notebook_id: Optional[str] = None,
    extensions: List[str] = ["pdf"],
) -> str:
    """
    Upload files to Google NotebookLM.
    Launches a visible browser window using Playwright.

    Args:
        upload_dir: Directory containing files to upload (default "downloads")
        mode: "new" (Create new notebook) or "existing" (Add to existing).
        notebook_id: Notebook ID (required only for "existing" mode if direct navigation is desired).
        extensions: List of file extensions to upload (e.g. ["pdf", "txt", "docx"]). Default is ["pdf"].
    """
    try:
        import os

        if not os.path.exists(upload_dir):
            return f"Error: Directory '{upload_dir}' does not exist."

        print(f"Starting NotebookLM upload from {upload_dir}...")
        # Call the existing function from the exporter module
        # Note: The original function prints to stdout, which MCP captures?
        # FastMCP captures stdout/stderr, but for clarity we just call it.

        upload_to_notebooklm(
            output_dir=upload_dir,
            mode=mode,
            notebook_id=notebook_id,
            extensions=extensions,
        )

        return "NotebookLM automation script finished. Check the opened browser window for results."
    except Exception as e:
        return f"Error during NotebookLM upload: {str(e)}"


def main():
    import sys

    if sys.stdin.isatty():
        print("PaperFetch MCP Server")
        print("This is a Model Context Protocol (MCP) server.")
        print(
            "Please configure your MCP client (e.g., Claude Desktop) to use this command."
        )
        print("See README.md for details regarding configuration.")
        print("\nCommand to use in configuration:")
        print("  paper-fetch-mcp")
        sys.exit(0)

    mcp.run()


if __name__ == "__main__":
    main()
