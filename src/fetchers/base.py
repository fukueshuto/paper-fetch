from abc import ABC, abstractmethod
from typing import List, Optional
from .models import Paper

class BaseFetcher(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        """Search for papers by query."""
        pass

    @abstractmethod
    def download_pdf(self, paper: Paper, save_dir: str) -> str:
        """Download PDF for the given paper and return the file path."""
        pass
