from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Callable
import time
import random
from .models import Paper

class BaseFetcher(ABC):
    # Jitter ranges (min, max) in seconds
    SEARCH_JITTER_RANGE = (0.0, 2.0)
    DOWNLOAD_JITTER_RANGE = (10.0, 40.0)

    def __init__(self, search_delay: float = 3.0, download_delay: float = 20.0):
        self.search_delay = search_delay
        self.download_delay = download_delay
        self.last_search_time = 0.0
        self.last_download_time = 0.0
        self.progress_callback: Optional[Callable[[str], None]] = None

    def set_progress_callback(self, callback: Callable[[str], None]):
        """Set a callback function to report wait progress."""
        self.progress_callback = callback

    def get_search_wait_range(self) -> Tuple[float, float]:
        """Return the range of possible wait times for search (min, max)."""
        min_wait = self.search_delay + self.SEARCH_JITTER_RANGE[0]
        max_wait = self.search_delay + self.SEARCH_JITTER_RANGE[1]
        return min_wait, max_wait

    def get_download_wait_range(self) -> Tuple[float, float]:
        """Return the range of possible wait times for download (min, max)."""
        min_wait = self.download_delay + self.DOWNLOAD_JITTER_RANGE[0]
        max_wait = self.download_delay + self.DOWNLOAD_JITTER_RANGE[1]
        return min_wait, max_wait

    def _wait_with_callback(self, required_wait: float, last_time: float, action_name: str):
        """Common wait logic with callback support."""
        elapsed = time.time() - last_time
        if elapsed < required_wait:
            sleep_time = required_wait - elapsed

            # If we have a callback and sleep time is significant, show countdown
            if self.progress_callback and sleep_time > 0.5:
                remaining = sleep_time
                while remaining > 0:
                    # Update message
                    msg = f"Rate limit: Waiting for {action_name}... ({remaining:.1f}s)"
                    self.progress_callback(msg)

                    # Sleep in small chunks
                    chunk = min(0.1, remaining)
                    time.sleep(chunk)
                    remaining -= chunk

                # Clear message after done
                self.progress_callback("")
            else:
                time.sleep(sleep_time)

    def _wait_for_search(self):
        """Enforce rate limit for search with jitter."""
        jitter = random.uniform(*self.SEARCH_JITTER_RANGE)
        required_wait = self.search_delay + jitter

        self._wait_with_callback(required_wait, self.last_search_time, "search")
        self.last_search_time = time.time()

    def _wait_for_download(self):
        """Enforce rate limit for download with significant jitter."""
        jitter = random.uniform(*self.DOWNLOAD_JITTER_RANGE)
        required_wait = self.download_delay + jitter

        self._wait_with_callback(required_wait, self.last_download_time, "download")
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

    def get_query_dirname(self, query: str) -> str:
        """
        Generate a safe directory name from the query.
        Default implementation sanitizes the query string.
        """
        import re
        # Sanitize query for file path (allow alphanumeric, hyphen, underscore)
        safe_query = re.sub(r'[^\w\-_]', '_', query)[:50]
        return safe_query
