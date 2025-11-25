import os
import time
import random
import requests
from datetime import date
from typing import List
from playwright.sync_api import sync_playwright, Page
from .base import BaseFetcher
from .models import Paper
from .utils import generate_filename
import requests
from datetime import date

class IeeeFetcher(BaseFetcher):
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = "https://ieeexplore.ieee.org"
        self.headers = {
            'Host': 'ieeexplore.ieee.org',
            'Content-Type': "application/json",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://ieeexplore.ieee.org',
            'Referer': 'https://ieeexplore.ieee.org/search/searchresult.jsp'
        }

    def search(self, query: str, max_results: int = None, open_access_only: bool = False) -> List[Paper]:
        # If max_results is None (unlimited), set a safe upper bound for IEEE API
        if max_results is None:
            max_results = 100
        # Get session cookies first
        session = requests.Session()
        try:
            session.get(self.base_url, headers=self.headers, timeout=10)
        except Exception as e:
            print(f"Warning: Failed to get initial cookies: {e}")

        payload = {
            "queryText": query,
            "returnFacets": ["ALL"],
            "returnType": "SEARCH",
            "rowsPerPage": max_results
        }

        if open_access_only:
            payload["openAccess"] = "true"

        try:
            response = session.post(
                f"{self.base_url}/rest/search",
                headers=self.headers,
                json=payload,
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error querying IEEE API: {e}")
            return []

        results = []
        if 'records' in data:
            for item in data['records']:
                try:
                    title = item.get('articleTitle', '')

                    # Authors
                    authors = []
                    if 'authors' in item:
                        for auth in item['authors']:
                            if 'preferredName' in auth:
                                authors.append(auth['preferredName'])
                            elif 'normalizedName' in auth:
                                authors.append(auth['normalizedName'])

                    abstract = item.get('abstract', '')

                    # URL & ID
                    arnumber = item.get('articleNumber', '')
                    url = f"{self.base_url}/document/{arnumber}/"

                    # PDF URL
                    # The API returns "pdfLink": "/stamp/stamp.jsp?tp=&arnumber=..."
                    pdf_link = item.get('pdfLink', '')
                    pdf_url = ""
                    if pdf_link:
                        pdf_url = self.base_url + pdf_link

                    # Year
                    year = item.get('publicationYear')
                    published_date = None
                    if year:
                        try:
                            published_date = date(int(year), 1, 1)
                        except:
                            pass

                    # Access Status
                    # accessType can be a string or a dict: {'type': 'locked', ...}
                    access_type_val = item.get('accessType')
                    is_downloadable = False

                    if isinstance(access_type_val, dict):
                        # e.g. {'type': 'locked', ...} or {'type': 'open-access', ...}
                        type_str = access_type_val.get('type', '').upper().replace('-', '_')
                        if type_str in ['OPEN_ACCESS', 'EPHEMERA']:
                            is_downloadable = True
                    elif isinstance(access_type_val, str):
                        if access_type_val.upper().replace('-', '_') in ['OPEN_ACCESS', 'EPHEMERA']:
                            is_downloadable = True

                    # If it's None or unknown, default to False (safe) or True (optimistic)?
                    # Given the user wants to filter, safe (False) is better,
                    # but if we want to show "Restricted?" we can leave it False.
                    # The CLI shows [Downloadable] if True.

                    # Remove debug print
                    # print(f"DEBUG: Title='{title[:20]}...', accessType='{access_type_val}'")

                    paper = Paper(
                        source="ieee",
                        id=arnumber,
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        url=url,
                        pdf_url=pdf_url,
                        published_date=published_date,
                        is_downloadable=is_downloadable
                    )
                    results.append(paper)
                except Exception as e:
                    print(f"Error parsing item: {e}")
                    continue

        return results

    def download_pdf(self, paper: Paper, save_dir: str) -> str:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        filename = generate_filename(paper.title, paper.authors, paper.published_date, source="ieee")
        filepath = os.path.join(save_dir, filename)

        # Try direct download first using requests (faster)
        # Reference: https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=...
        try:
            if paper.id:
                download_url = f"{self.base_url}/stampPDF/getPDF.jsp?tp=&arnumber={paper.id}"
                response = requests.get(download_url, headers=self.headers, stream=True, timeout=30)

                # Check if we got a PDF or an HTML page (login/error)
                content_type = response.headers.get('Content-Type', '')
                if 'application/pdf' in content_type:
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return filepath
        except Exception as e:
            print(f"Direct download failed: {e}, falling back to Playwright...")

        # Fallback to Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=self.headers['User-Agent']
            )
            page = context.new_page()

            try:
                page.goto(paper.pdf_url)

                # Wait for iframe
                iframe_element = page.wait_for_selector("iframe[src*='.pdf']", timeout=15000)
                pdf_src = iframe_element.get_attribute("src")

                if pdf_src:
                    response = page.request.get(pdf_src)
                    if response.status == 200:
                        with open(filepath, "wb") as f:
                            f.write(response.body())
                    else:
                        raise Exception(f"Failed to download PDF from {pdf_src}, status: {response.status}")
                else:
                    raise Exception("Could not find PDF iframe source")

            except Exception as e:
                raise e
            finally:
                browser.close()

        return filepath
