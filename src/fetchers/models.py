from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date

@dataclass
class Paper:
    source: str
    id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    pdf_url: str
    published_date: Optional[date] = None
    is_downloadable: bool = True # Default to True (e.g. for Arxiv)

    def to_dict(self):
        return {
            "source": self.source,
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "is_downloadable": self.is_downloadable
        }
