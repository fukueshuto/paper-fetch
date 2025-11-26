import arxiv
import os
import requests
from typing import List
from datetime import date
from .base import BaseFetcher
from .models import Paper
from .utils import generate_filename

class ArxivFetcher(BaseFetcher):
    def __init__(self):
        self.client = arxiv.Client(
            page_size=10,
            delay_seconds=3.0,
            num_retries=3
        )

    def search(self, query: str, max_results: int = None, sort_by: str = "relevance", sort_order: str = "desc", start_year: int = None, end_year: int = None) -> List[Paper]:
        # Map sort_by
        criterion = arxiv.SortCriterion.Relevance
        if sort_by == "date":
            criterion = arxiv.SortCriterion.SubmittedDate

        # Map sort_order
        order = arxiv.SortOrder.Descending
        if sort_order == "asc":
            order = arxiv.SortOrder.Ascending

        # Handle date filtering
        final_query = query
        if start_year or end_year:
            # Default to a wide range if one side is missing
            start_str = f"{start_year}01010000" if start_year else "190001010000"
            end_str = f"{end_year}12312359" if end_year else "209912312359"
            final_query = f"{query} AND submittedDate:[{start_str} TO {end_str}]"

        search = arxiv.Search(
            query=final_query,
            max_results=max_results,
            sort_by=criterion,
            sort_order=order
        )

        results = []
        for result in self.client.results(search):
            # Convert arxiv.Result to our Paper model
            published_date = result.published.date() if result.published else None

            paper = Paper(
                source="arxiv",
                id=result.entry_id.split('/')[-1], # Extract ID from URL
                title=result.title,
                authors=[a.name for a in result.authors],
                abstract=result.summary,
                url=result.entry_id,
                pdf_url=result.pdf_url,
                published_date=published_date
            )
            results.append(paper)

        return results

    def download_pdf(self, paper: Paper, save_dir: str) -> str:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        filename = generate_filename(paper.title, paper.authors, paper.published_date, source="arxiv")
        filepath = os.path.join(save_dir, filename)

        # Use requests to download to have full control over the file creation
        # arxiv library's download_pdf sometimes has issues with custom filenames or paths
        response = requests.get(paper.pdf_url, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath
