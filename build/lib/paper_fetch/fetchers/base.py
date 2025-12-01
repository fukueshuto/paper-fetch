from abc import ABC, abstractmethod
from typing import List
from .models import Paper

class BaseFetcher(ABC):
    def __init__(self, search_delay: float = 3.0, download_delay: float = 20.0):
        self.search_delay = search_delay
        self.download_delay = download_delay
        self.last_search_time = 0.0
        self.last_download_time = 0.0

    def _wait_for_search(self):
        """Enforce rate limit for search with jitter."""
        import time
        import random

        # Jitter: 0.0 - 2.0 seconds
        jitter = random.uniform(0.0, 2.0)
        required_wait = self.search_delay + jitter

        elapsed = time.time() - self.last_search_time
        if elapsed < required_wait:
            sleep_time = required_wait - elapsed
            time.sleep(sleep_time)

        self.last_search_time = time.time()

    def _wait_for_download(self):
        """Enforce rate limit for download with significant jitter."""
        import time
        import random

        # Jitter: 10.0 - 40.0 seconds
        jitter = random.uniform(10.0, 40.0)
        required_wait = self.download_delay + jitter

        elapsed = time.time() - self.last_download_time
        if elapsed < required_wait:
            sleep_time = required_wait - elapsed
            # print(f"DEBUG: Rate limit enforcement (Download). Sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)

        self.last_download_time = time.time()

    @abstractmethod
    def search(self, query: str, max_results: int = 10, sort_by: str = "relevance", sort_order: str = "desc", start_year: int = None, end_year: int = None) -> List[Paper]:
        """Search for papers by query."""
        self._wait_for_search()
        pass

    @abstractmethod
    def download_pdf(self, paper: Paper, save_dir: str) -> str:
        """Download PDF for the given paper and return the file path."""
        self._wait_for_download()
        pass

    def get_total_results(self, query: str, start_year: int = None, end_year: int = None, **kwargs) -> int:
        """Get the total number of results for a query."""
        self._wait_for_search()
        return -1 # Default to -1 if not implemented
