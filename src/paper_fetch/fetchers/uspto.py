import os
import requests
import json
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from .base import BaseFetcher
from .models import Paper
from .utils import generate_filename


class UsptoFetcher(BaseFetcher):
    """
    USPTO PatentsView API Fetcher.
    """

    supports_download_methods = True
    available_download_methods = ["Google Patents", "USPTO Direct"]

    def __init__(self):
        super().__init__(
            search_delay=2.0, download_delay=15.0
        )  # Default delays, override via config
        self.api_url = "https://search.patentsview.org/api/v1/patent/query/"
        # API Key is optional for basic use but recommended for higher limits.
        self.api_key = self.config.get("api_keys", {}).get("uspto")

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

        # Build PatentsView Query
        # We search in title or abstract
        # Reference: https://patentsview.org/apis/search/query

        criteria = [
            {"_text_phrase": {"patent_title": query}},
            {"_text_phrase": {"patent_abstract": query}},
        ]
        q_obj = {"_or": criteria}

        # Date filtering
        if start_year or end_year:
            date_criteria = []
            if start_year:
                date_criteria.append({"_gte": {"patent_date": f"{start_year}-01-01"}})
            if end_year:
                date_criteria.append({"_lte": {"patent_date": f"{end_year}-12-31"}})

            if date_criteria:
                q_obj = {"_and": [q_obj] + date_criteria}

        params = {
            "q": json.dumps(q_obj),
            "f": json.dumps(
                [
                    "patent_number",
                    "patent_title",
                    "patent_abstract",
                    "patent_date",
                    "inventors",
                    "patent_kind",
                ]
            ),
            "o": json.dumps({"per_page": max_results}),
        }

        # Sorting
        # PatentsView sort fields: https://patentsview.org/apis/search/sort
        # Default is usually patent_number? relevance is not strictly supported by API except via text score,
        # but the API doesn't expose strict "relevance" sort param easily in this wrapper.
        # We will use patent_date if requested, otherwise let API default (often patent_number).
        if sort_by == "date":
            # API expects "s": [{"patent_date": "desc"}]
            direction = "desc" if sort_order == "desc" else "asc"
            params["s"] = json.dumps([{"patent_date": direction}])

        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key

        try:
            # POST is also supported and safer for long queries, but GET is standard for this API
            # We use POST to avoid URL length issues
            response = requests.post(
                self.api_url, json=params, headers=headers, timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403]:
                print(f"USPTO API Authentication Error: {e}")
                print(
                    "Please set your API key in config.toml under [api_keys] section."
                )
                print("Ref: https://patentsview.org/apis/purpose")
            else:
                print(f"Error querying USPTO API: {e}")
            return []
        except Exception as e:
            print(f"Error querying USPTO API: {e}")
            return []

        results = []
        patents = data.get("patents", [])
        if not patents:
            return []

        for item in patents:
            title = item.get("patent_title", "No Title")
            abstract = item.get("patent_abstract", "")
            patent_number = item.get("patent_number", "")
            patent_kind = item.get("patent_kind", "")

            # Authors (Inventors)
            inventors = []
            for inv in item.get("inventors", []):
                fname = inv.get("inventor_name_first", "")
                lname = inv.get("inventor_name_last", "")
                if fname or lname:
                    inventors.append(f"{fname} {lname}".strip())

            # Date
            pub_date_str = item.get("patent_date")
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d").date()
                except Exception:
                    pass

            # ID construction
            # We store the raw number as ID, but for Google Patents we need US prefix and Kind
            # But Kind is sometimes missing or complex.
            # Base ID: patent_number

            # Construct Google Patents URL for "View Online"
            # Format: US<NUMBER><KIND> e.g. US1234567B2
            # If kind is missing, Google often redirects correctly with just US + Number
            gp_id = (
                f"US{patent_number}{patent_kind}"
                if patent_kind
                else f"US{patent_number}"
            )
            url = f"https://patents.google.com/patent/{gp_id}/en"

            paper = Paper(
                source="uspto",
                id=patent_number,  # Keep raw number as ID
                title=title,
                authors=inventors,
                abstract=abstract,
                url=url,
                pdf_url="",  # Determined dynamically
                published_date=pub_date,
                is_downloadable=True,
            )
            # Store gp_id in paper object? Paper model is rigid.
            # We can re-construct it in download method or use ID.
            # Let's attach it to the object as a dynamic attribute for internal use not serialized?
            # Or just recompute it. Recomputing is safer.

            results.append(paper)

        return results

    def check_downloadable(self, paper: Paper, method: str = "default") -> bool:
        # Both methods assume we have a valid patent number.
        return bool(paper.id)

    def download_pdf(self, paper: Paper, save_dir: str, method: str = "default") -> str:
        self._wait_for_download()
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        filename = generate_filename(
            paper.title, paper.authors, paper.published_date, source="uspto"
        )
        filepath = os.path.join(save_dir, filename)

        if method == "USPTO Direct":
            return self._download_direct(paper, filepath)
        else:
            # Default: Google Patents
            return self._download_google_patents(paper, filepath)

    def _download_direct(self, paper: Paper, filepath: str) -> str:
        # https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/#######
        url = f"https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/{paper.id}"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            r = requests.get(url, headers=headers, stream=True, timeout=60)
            r.raise_for_status()

            # Check content type if possible, though USPTO API might just return raw stream
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath
        except Exception as e:
            print(f"USPTO Direct download failed: {e}")
            raise e

    def _download_google_patents(self, paper: Paper, filepath: str) -> str:
        # We need to construct the URL again.
        # Note: We lost the 'kind' code if we didn't store it.
        # Using paper.url (which has GP ID) fits best!
        target_url = paper.url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            r = requests.get(target_url, headers=headers, timeout=20)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            pdf_link = None

            # Attempt to find "Download PDF" link
            # Scrape specific to patents.google.com structure
            # Often <a href="...">Download PDF</a> or icon

            # Strategy 1: Look for links ending in .pdf
            # Google patents often serves PDFs from patentimages.storage.googleapis.com
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "patentimages.storage.googleapis.com" in href:
                    pdf_link = href
                    break

            if not pdf_link:
                # Strategy 2: Check for specific class or structure (simpler is better first)
                pass

            if not pdf_link:
                raise ValueError("Could not find PDF link on Google Patents page.")

            # Download
            pdf_r = requests.get(pdf_link, headers=headers, stream=True, timeout=60)
            pdf_r.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in pdf_r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath

        except Exception as e:
            print(f"Google Patents download failed: {e}")
            raise e
