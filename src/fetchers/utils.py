import re
from datetime import date
from typing import Optional

def sanitize_filename(text: str) -> str:
    """Sanitize text for use in filenames."""
    # Remove invalid characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    # Replace spaces with underscores
    text = text.replace(' ', '_')
    # Limit length
    return text[:100]

def generate_filename(paper_title: str, authors: list[str], published_date: Optional[date]) -> str:
    """Generate filename based on the convention: {Year}_{Month}_{FirstAuthor}_{Title}.pdf"""
    year = "0000"
    month = "00"

    if published_date:
        year = str(published_date.year)
        month = f"{published_date.month:02d}"

    first_author = "Unknown"
    if authors:
        # Get last name of the first author
        first_author = authors[0].split()[-1]

    sanitized_title = sanitize_filename(paper_title)
    sanitized_author = sanitize_filename(first_author)

    return f"{year}_{month}_{sanitized_author}_{sanitized_title}.pdf"
