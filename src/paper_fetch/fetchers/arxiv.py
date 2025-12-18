import arxiv
import os
import requests
from typing import List
from .base import BaseFetcher
from .models import Paper
from .utils import generate_filename

from ..converter import Converter


class ArxivFetcher(BaseFetcher):
    def __init__(self):
        super().__init__(search_delay=3.0, download_delay=20.0)
        self.client = arxiv.Client(
            page_size=10,
            delay_seconds=3.0,  # arxiv library also has its own delay, but we enforce ours globally
            num_retries=3,
        )
        self.converter = Converter()

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        start_year: int = None,
        end_year: int = None,
    ) -> List[Paper]:
        self._wait_for_search()
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
            sort_order=order,
        )

        results = []
        for result in self.client.results(search):
            # Convert arxiv.Result to our Paper model
            published_date = result.published.date() if result.published else None

            paper = Paper(
                source="arxiv",
                id=result.entry_id.split("/")[-1],  # Extract ID from URL
                title=result.title,
                authors=[a.name for a in result.authors],
                abstract=result.summary,
                url=result.entry_id,
                pdf_url=result.pdf_url,
                published_date=published_date,
            )
            results.append(paper)

        return results

    def get_total_results(
        self, query: str, start_year: int = None, end_year: int = None, **kwargs
    ) -> int:
        self._wait_for_search()
        import xml.etree.ElementTree as ET

        # Handle date filtering for query construction
        final_query = query
        if start_year or end_year:
            start_str = f"{start_year}01010000" if start_year else "190001010000"
            end_str = f"{end_year}12312359" if end_year else "209912312359"
            final_query = f"{query} AND submittedDate:[{start_str} TO {end_str}]"

        url = "http://export.arxiv.org/api/query"
        params = {"search_query": final_query, "start": 0, "max_results": 1}

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            ns = {"opensearch": "http://a9.com/-/spec/opensearch/1.1/"}
            total_results = root.find("opensearch:totalResults", ns)
            if total_results is not None:
                return int(total_results.text)
        except Exception as e:
            print(f"Error getting total results: {e}")

        return -1

    def download_pdf(
        self,
        paper: Paper,
        save_dir: str,
        convert_to_md: bool = False,
        method: str = "default",
        **kwargs,
    ) -> str:
        self._wait_for_download()
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        filename = generate_filename(
            paper.title, paper.authors, paper.published_date, source="arxiv"
        )
        filepath = os.path.join(save_dir, filename)

        # Use requests to download to have full control over the file creation
        # arxiv library's download_pdf sometimes has issues with custom filenames or paths
        response = requests.get(paper.pdf_url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if convert_to_md:
            self.converter.convert_to_markdown(filepath, save_dir)

        return filepath
