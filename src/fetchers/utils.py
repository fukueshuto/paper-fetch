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

def generate_filename(paper_title: str, authors: list[str], published_date: Optional[date], source: str = "") -> str:
    """Generate filename based on the convention: {Year}_{Month}_{Source}_{FirstAuthor}_{LastAuthor}_{Title}.pdf"""
    year = "0000"
    month = "00"

    if published_date:
        year = str(published_date.year)
        month = f"{published_date.month:02d}"

    first_author = "Unknown"
    last_author = ""

    if authors:
        # Get last name of the first author
        first_author = authors[0].split()[-1]
        if len(authors) > 1:
            last_author = authors[-1].split()[-1]

    sanitized_title = sanitize_filename(paper_title)
    sanitized_first = sanitize_filename(first_author)
    sanitized_last = sanitize_filename(last_author)
    sanitized_source = sanitize_filename(source)

    components = [year, month]
    if sanitized_source:
        components.append(sanitized_source)

    components.append(sanitized_first)
    if sanitized_last:
        components.append(sanitized_last)

    components.append(sanitized_title)

    filename = "_".join(components)
    return f"{filename}.pdf"
