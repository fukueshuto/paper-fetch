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

    def search(self, query: str, max_results: int = None) -> List[Paper]:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
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

        filename = generate_filename(paper.title, paper.authors, paper.published_date)
        filepath = os.path.join(save_dir, filename)

        # Use requests to download to have full control over the file creation
        # arxiv library's download_pdf sometimes has issues with custom filenames or paths
        response = requests.get(paper.pdf_url, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath
