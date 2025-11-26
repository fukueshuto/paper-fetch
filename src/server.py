from mcp.server.fastmcp import FastMCP
from typing import List, Optional
from .fetchers.arxiv import ArxivFetcher
from .fetchers.ieee import IeeeFetcher
from .fetchers.models import Paper
from datetime import date

mcp = FastMCP("paper-fetch")

# Initialize clients
arxiv_client = ArxivFetcher()
ieee_client = IeeeFetcher()

@mcp.tool()
def search_papers(source: str, query: str, limit: int = 5, open_access_only: bool = False) -> str:
    """
    Search for papers from Arxiv or IEEE Xplore.

    Args:
        source: "arxiv" or "ieee"
        query: Search query
        limit: Maximum number of results (default 5)
        open_access_only: If True, search only for Open Access papers (IEEE only)
    """
    if source.lower() == "arxiv":
        client = arxiv_client
    elif source.lower() == "ieee":
        client = ieee_client
    else:
        return f"Error: Unknown source '{source}'. Use 'arxiv' or 'ieee'."

    try:
        if source.lower() == "ieee":
            results = client.search(query, max_results=limit, open_access_only=open_access_only)
        else:
            results = client.search(query, max_results=limit)
        # Return a formatted string or JSON.
        # FastMCP handles JSON serialization if we return dict/list,
        # but let's return a list of dicts for clarity.
        return [p.to_dict() for p in results]
    except Exception as e:
        return f"Error searching {source}: {str(e)}"

@mcp.tool()
def download_paper(url: str, title: str, authors: List[str], year: Optional[int] = None, save_dir: str = "downloads") -> str:
    """
    Download a paper's PDF given its metadata.

    Args:
        url: URL of the paper (used to identify source and download location)
        title: Title of the paper (for filename)
        authors: List of authors (for filename)
        year: Publication year (for filename)
        save_dir: Directory to save the PDF (default "downloads")
    """
    # Infer source from URL
    source = "unknown"
    if "arxiv.org" in url:
        source = "arxiv"
        client = arxiv_client
        # For Arxiv, we might need to reconstruct the PDF URL if the passed URL is the abstract URL
        # But ArxivClient.download_pdf uses paper.pdf_url.
        # Let's construct a Paper object.
        # Arxiv PDF URL is usually passed in search results.
        # If the LLM passes the abstract URL, we might need to convert it.
        # Arxiv abstract: arxiv.org/abs/ID, PDF: arxiv.org/pdf/ID
        pdf_url = url.replace("/abs/", "/pdf/")
        if not pdf_url.endswith(".pdf"):
            pdf_url += ".pdf"
    elif "ieeexplore.ieee.org" in url:
        source = "ieee"
        client = ieee_client
        pdf_url = url # IEEE client handles the URL (viewer or stamp)
    else:
        return f"Error: Could not determine source from URL '{url}'"

    # Construct Paper object
    published_date = None
    if year:
        published_date = date(year, 1, 1)

    paper = Paper(
        source=source,
        id="unknown", # Not critical for download
        title=title,
        authors=authors,
        abstract="",
        url=url,
        pdf_url=pdf_url,
        published_date=published_date
    )

    try:
        path = client.download_pdf(paper, save_dir)
        return f"Successfully downloaded to: {path}"
    except Exception as e:
        return f"Error downloading paper: {str(e)}"

if __name__ == "__main__":
    mcp.run()
