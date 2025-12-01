import json
import os
from typing import List
from datetime import date, datetime
from .fetchers.models import Paper

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def save_papers_to_json(papers: List[Paper], filename: str):
    """Save a list of Paper objects to a JSON file."""
    data = [paper.__dict__ for paper in papers]

    # Ensure directory exists
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=DateEncoder)
    print(f"Saved {len(papers)} papers to {filename}")

def load_papers_from_json(filename: str) -> List[Paper]:
    """Load a list of Paper objects from a JSON file."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    papers = []
    for item in data:
        # Handle date parsing
        if item.get('published_date'):
            try:
                # Try parsing as datetime first, then date
                # ISO format for date is YYYY-MM-DD
                dt = date.fromisoformat(item['published_date'])
                item['published_date'] = dt
            except ValueError:
                # Fallback or keep as string if parsing fails (though Paper expects date)
                pass

        # Reconstruct Paper object
        # We filter out keys that might not be in __init__ if strictly typed,
        # but Paper is likely a dataclass or simple class.
        # Assuming Paper is a dataclass or has a flexible init.
        # Let's check Paper definition if possible, but for now assume it matches.
        # Actually, let's just pass the dict if it's a dataclass.
        # If it's a Pydantic model, we'd use parse_obj.
        # Based on previous file views, Paper seemed to be imported from .models.
        # Let's assume standard class.

        # We need to make sure we don't pass extra fields if __init__ doesn't take **kwargs
        # But let's try to instantiate it.
        try:
            paper = Paper(**item)
            papers.append(paper)
        except TypeError as e:
            # If __init__ got an unexpected keyword argument
            print(f"Warning: Error loading paper: {e}")
            # Try to handle manually if needed, or just skip

    return papers
