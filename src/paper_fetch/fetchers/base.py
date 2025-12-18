from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Callable
import time
import random
from .models import Paper


class BaseFetcher(ABC):
    def __init__(self, search_delay: float = None, download_delay: float = None):
        from paper_fetch.config import load_config

        self.config = load_config()

        advanced_cfg = self.config.get("advanced", {})

        # Determine base delays (allow override via init but default to config/fallback)
        # However, BaseFetcher design was strict about min/max jitter.
        # New design: configurable standard delay + configuable jitter OR configurable ranges.
        # Implementation Plan says: download_wait_min / max in config.

        # Search range
        s_min = advanced_cfg.get("search_wait_min", 0.0)
        s_max = advanced_cfg.get("search_wait_max", 2.0)
        self.search_jitter_range = (float(s_min), float(s_max))
        self.search_delay = (
            search_delay if search_delay is not None else s_min
        )  # Base delay is roughly the min

        # Download range
        d_min = advanced_cfg.get("download_wait_min", 10.0)
        d_max = advanced_cfg.get("download_wait_max", 40.0)
        self.download_jitter_range = (float(d_min), float(d_max))
        self.download_delay = download_delay if download_delay is not None else d_min

        self.last_search_time = 0.0
        self.last_download_time = 0.0
        self.progress_callback: Optional[Callable[[str], None]] = None

    # Flags for UI
    supports_download_methods: bool = False
    available_download_methods: List[str] = []

    # Instance variables for ranges (replaced class constants)
    search_jitter_range: Tuple[float, float]
    download_jitter_range: Tuple[float, float]

    def set_progress_callback(self, callback: Callable[[str], None]):
        """Set a callback function to report wait progress."""
        self.progress_callback = callback

    def get_search_wait_range(self) -> Tuple[float, float]:
        """Return the range of possible wait times for search (min, max)."""
        # We assume usage is min...max, search_delay is basically obsolete if using raw ranges,
        # but let's keep logic consistent with min + jitter for now if jitter is delta.
        # WAIT: config says "min" and "max". Jitter SHOULD be uniform(min, max).
        # Old logic: delay + uniform(0, jitter_max).
        # Let's align with new "min/max" config. The range IS the min/max.
        return self.search_jitter_range

    def get_download_wait_range(self) -> Tuple[float, float]:
        """Return the range of possible wait times for download (min, max)."""
        return self.download_jitter_range

    def _wait_with_callback(
        self, required_wait: float, last_time: float, action_name: str
    ):
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
        # Use full range from config
        wait_time = random.uniform(*self.search_jitter_range)

        self._wait_with_callback(wait_time, self.last_search_time, "search")
        self.last_search_time = time.time()

    def _wait_for_download(self):
        """Enforce rate limit for download with significant jitter."""
        wait_time = random.uniform(*self.download_jitter_range)

        self._wait_with_callback(wait_time, self.last_download_time, "download")
        self.last_download_time = time.time()

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "desc",
        start_year: int = None,
        end_year: int = None,
    ) -> List[Paper]:
        """Search for papers by query."""
        self._wait_for_search()
        pass

    @abstractmethod
    @abstractmethod
    def download_pdf(self, paper: Paper, save_dir: str, method: str = "default") -> str:
        """
        Download PDF for the given paper and return the file path.
        method: The download strategy to use (if supported).
        """
        self._wait_for_download()
        pass

    def check_downloadable(self, paper: Paper, method: str = "default") -> bool:
        """
        Check if the paper can be downloaded using the specified method.
        Default implementation relies on the paper's valid property.
        """
        return paper.is_downloadable

    def get_total_results(
        self, query: str, start_year: int = None, end_year: int = None, **kwargs
    ) -> int:
        """Get the total number of results for a query."""
        self._wait_for_search()
        return -1  # Default to -1 if not implemented

    def get_query_dirname(self, query: str) -> str:
        """
        Generate a safe directory name from the query.
        Default implementation sanitizes the query string.
        """
        import re

        # Sanitize query for file path (allow alphanumeric, hyphen, underscore)
        safe_query = re.sub(r"[^\w\-_]", "_", query)[:50]
        return safe_query
