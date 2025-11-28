from abc import ABC, abstractmethod
from typing import List
from .models import Paper

class BaseFetcher(ABC):
    def __init__(self, delay_seconds: float = 0.0):
        self.delay_seconds = delay_seconds
        self.last_request_time = 0.0

    def _enforce_rate_limit(self):
        """Enforce the rate limit by sleeping if necessary."""
        import time
        if self.delay_seconds > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.delay_seconds:
                sleep_time = self.delay_seconds - elapsed
                # print(f"DEBUG: Rate limit enforcement. Sleeping for {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            self.last_request_time = time.time()

    @abstractmethod
    def search(self, query: str, max_results: int = 10, sort_by: str = "relevance", sort_order: str = "desc", start_year: int = None, end_year: int = None) -> List[Paper]:
        """Search for papers by query."""
        self._enforce_rate_limit()
        pass

    @abstractmethod
    def download_pdf(self, paper: Paper, save_dir: str) -> str:
        """Download PDF for the given paper and return the file path."""
        pass

    def get_total_results(self, query: str, start_year: int = None, end_year: int = None, **kwargs) -> int:
        """Get the total number of results for a query."""
        self._enforce_rate_limit()
        return -1 # Default to -1 if not implemented
