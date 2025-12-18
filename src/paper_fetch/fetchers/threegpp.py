import os
import re
import requests
import logging
import shutil
from typing import List
from urllib.parse import unquote, urljoin

from .base import BaseFetcher
from .models import Paper
from ..converter import Converter

logger = logging.getLogger(__name__)


class ThreeGPPFetcher(BaseFetcher):
    def __init__(self):
        super().__init__(
            search_delay=1.0, download_delay=1.0
        )  # 3GPP FTP might not need strict rate limiting, but good to have
        self.converter = Converter()

    def search(self, query: str, max_results: int = 10, **kwargs) -> List[Paper]:
        """
        Search for files in a 3GPP directory URL.
        'query' is expected to be a URL.
        """
        url = query.strip()
        if not url.startswith("http"):
            # If not a URL, maybe we can support a default or error out.
            # For now, assume it must be a URL as per plan.
            logger.warning("Query is not a URL. Returning empty list.")
            return []

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            return []

        # Parse HTML to find file links
        # Pattern to match: <a class="file" href="..."> or just href ending in .zip/.doc/.docx
        # The script used: grep '<a class="file"'
        # But standard Apache directory listing might not have class="file".
        # 3GPP site seems to use a specific styling.
        # Let's try a generic regex for hrefs that look like files.

        # Regex to capture href content
        # We look for href="filename"
        # We filter for common document extensions

        papers = []

        # Simple regex for hrefs.
        # 3GPP directory listings usually have simple filenames in hrefs.
        # Example: <a href="R1-200001.zip">R1-200001.zip</a>

        # If the script relied on class="file", it might be important.
        # Let's try to be slightly robust.

        # Find all hrefs
        links = re.findall(r'href=["\']([^"\']+)["\']', html_content)

        # Filter links
        valid_extensions = (
            ".zip",
            ".doc",
            ".docx",
            ".ppt",
            ".pptx",
            ".xls",
            ".xlsx",
            ".pdf",
        )

        for link in links:
            if link.lower().endswith(valid_extensions) and not link.startswith("?"):
                # Decode URL encoded characters (e.g. %20)
                filename = unquote(link)
                # Ensure filename is safe (basename only) to prevent directory traversal
                filename = os.path.basename(filename)

                full_url = urljoin(url, link)

                # Create Paper object
                # We don't have metadata, so use filename for title/id
                paper = Paper(
                    source="3gpp",
                    id=filename,
                    title=filename,
                    authors=["3GPP"],  # Placeholder
                    abstract="No abstract available.",
                    url=full_url,
                    pdf_url=full_url,  # It's the source file
                    published_date=None,
                    is_downloadable=True,
                )
                papers.append(paper)

        # Apply limit
        if max_results:
            papers = papers[:max_results]

        return papers

    def _get_folder_name_from_url(self, url: str) -> str:
        """
        Extract a meaningful folder name from the 3GPP URL.
        Examples:
        .../TSGR1_122b/Docs/ -> TSGR1_122b
        .../Rel-19/38_series/ -> Rel-19_38_series
        """
        # Remove trailing slash
        url = url.rstrip("/")
        parts = url.split("/")

        # Strategy 1: Meeting Docs (usually ends with Docs, parent is meeting name)
        if parts[-1].lower() == "docs":
            return parts[-2]

        # Strategy 2: Specs Series (usually ends with series number, parent is Release)
        # e.g. .../Rel-19/38_series
        if "series" in parts[-1].lower():
            # Combine release and series
            return f"{parts[-2]}_{parts[-1]}"

        # Fallback: Use the last part
        return parts[-1]

    def get_query_dirname(self, query: str) -> str:
        """
        Override to provide meaningful folder name from URL.
        """
        # If query is a URL, use the helper
        if query.startswith("http"):
            return self._get_folder_name_from_url(query)

        # Otherwise fallback to default sanitization
        return super().get_query_dirname(query)

    def download_pdf(
        self,
        paper: Paper,
        save_dir: str,
        convert_to_md: bool = False,
        convert_to_pdf: bool = True,
        method: str = "default",
        **kwargs,
    ) -> str:
        """
        Download and process 3GPP document.
        save_dir: The base directory to save to (e.g. downloads/3gpp)
        convert_to_md: Whether to convert to Markdown.
        convert_to_pdf: Whether to convert Office documents to PDF.
        """
        # Determine specific subdirectory based on URL logic
        # We assume paper.url is the file URL, but we need the directory URL context.
        # Ideally, the caller passes the base directory, and we append the meeting name.
        # But here save_dir is passed from CLI/GUI.
        # If CLI/GUI passes "downloads/3gpp", we should append the meeting name.
        # If CLI/GUI passes "downloads/3gpp/MeetingName" (because it did the logic), we use it.

        # However, the current CLI/GUI logic is:
        # download_dir = output_dir / source
        # So save_dir is likely ".../downloads/3gpp".

        # We need to extract the meeting name from the paper URL (parent dir).
        # paper.url is like ".../TSGR1_122b/Docs/R1-200001.zip"
        parent_url = os.path.dirname(paper.url)
        folder_name = self._get_folder_name_from_url(parent_url)

        # Final base directory for this paper
        target_base_dir = os.path.join(save_dir, folder_name)

        # Determine subdirectories
        archive_dir = os.path.join(target_base_dir, "archive")
        source_dir = os.path.join(target_base_dir, "source")
        pdf_dir = os.path.join(target_base_dir, "pdf")
        md_dir = os.path.join(target_base_dir, "markdown")

        # Create directories as needed
        for d in [archive_dir, source_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

        if convert_to_pdf and not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)

        if convert_to_md and not os.path.exists(md_dir):
            os.makedirs(md_dir)

        filename = paper.id  # This is the filename from search
        local_path = os.path.join(
            target_base_dir, filename
        )  # Temporary download location

        # Check if already processed (in archive or pdf)
        # But paper-fetch usually expects us to download if called.

        # Download file
        try:
            logger.info(f"Downloading {paper.url}...")
            response = requests.get(paper.url, stream=True, timeout=30)
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise e

        final_pdf_path = ""

        # Process based on extension
        if filename.lower().endswith(".zip"):
            # Extract
            # We extract to a temp dir first to see what's inside
            import tempfile

            with tempfile.TemporaryDirectory() as temp_extract_dir:
                success = self.converter.extract_zip(local_path, temp_extract_dir)
                if success:
                    # Move ZIP to archive
                    shutil.move(local_path, os.path.join(archive_dir, filename))

                    # Process extracted files
                    found_office_file = False
                    for root, _, files in os.walk(temp_extract_dir):
                        for file in files:
                            # Skip macOS metadata
                            if file.startswith("._") or "__MACOSX" in root:
                                continue

                            file_path = os.path.join(root, file)
                            ext = os.path.splitext(file)[1].lower()

                            if ext in [
                                ".doc",
                                ".docx",
                                ".ppt",
                                ".pptx",
                                ".xls",
                                ".xlsx",
                            ]:
                                found_office_file = True
                                # Move to source dir
                                # We might want to rename it to match zip name if needed,
                                # but keeping original name is safer for now unless we want strict mapping.
                                # The script did: zip_basename + "_" + office_filename

                                zip_basename = os.path.splitext(filename)[0]
                                new_filename = f"{zip_basename}_{file}"
                                dest_source_path = os.path.join(
                                    source_dir, new_filename
                                )
                                shutil.copy2(file_path, dest_source_path)

                                # Convert to PDF
                                if convert_to_pdf:
                                    pdf_path = self.converter.convert_to_pdf(
                                        dest_source_path, pdf_dir
                                    )
                                    if pdf_path:
                                        final_pdf_path = pdf_path

                                # Convert to Markdown (Optional)
                                if convert_to_md:
                                    self.converter.convert_to_markdown(
                                        dest_source_path, md_dir
                                    )

                    if not found_office_file:
                        logger.warning(f"No office files found in {filename}")
                        # If no office file, maybe it was just PDFs?
                        # If PDFs found, move them to pdf_dir
                        for root, _, files in os.walk(temp_extract_dir):
                            for file in files:
                                if file.lower().endswith(
                                    ".pdf"
                                ) and not file.startswith("._"):
                                    # If it's a PDF, we treat it as source AND pdf?
                                    # Or just put in PDF dir?
                                    # If convert_to_pdf is False, maybe we still want it in source?
                                    # But usually PDF is the target.
                                    # Let's put it in PDF dir if convert_to_pdf is True, or if it's the only thing.
                                    # Actually, if it's a PDF, it IS the source format too.
                                    # Let's copy to source AND pdf (if enabled).

                                    # Copy to source as well?
                                    # The script might have just put it in PDF dir.
                                    # Let's put it in PDF dir.
                                    extracted_pdf_path = os.path.join(root, file)
                                    if convert_to_pdf:
                                        if not os.path.exists(pdf_dir):
                                            os.makedirs(pdf_dir)
                                        shutil.copy2(
                                            extracted_pdf_path,
                                            os.path.join(pdf_dir, file),
                                        )
                                        if not final_pdf_path:
                                            final_pdf_path = os.path.join(pdf_dir, file)

                                    # Also convert to MD if requested
                                    if convert_to_md:
                                        self.converter.convert_to_markdown(
                                            extracted_pdf_path, md_dir
                                        )

                else:
                    logger.error(f"Failed to extract {filename}")
                    # Move to archive anyway? Or leave it?
                    # Leave it for retry or manual inspection
                    pass

        elif filename.lower().endswith(
            (".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx")
        ):
            # Direct office file
            # Move to source
            dest_source_path = os.path.join(source_dir, filename)
            shutil.move(local_path, dest_source_path)

            # Convert
            if convert_to_pdf:
                pdf_path = self.converter.convert_to_pdf(dest_source_path, pdf_dir)
                if pdf_path:
                    final_pdf_path = pdf_path

            if convert_to_md:
                self.converter.convert_to_markdown(dest_source_path, md_dir)

        elif filename.lower().endswith(".pdf"):
            # Direct PDF
            # If convert_to_pdf is False, do we still save it?
            # Yes, it's the file we downloaded.
            # But where? source or pdf?
            # If it's a PDF, it belongs in pdf dir usually.
            # But if user said --no-pdf, maybe they just want source?
            # But PDF IS the source here.
            # So we save it to pdf dir (or source dir?).
            # Let's save to PDF dir as it is a PDF.
            if convert_to_pdf:
                if not os.path.exists(pdf_dir):
                    os.makedirs(pdf_dir)
                dest_pdf_path = os.path.join(pdf_dir, filename)
                shutil.move(local_path, dest_pdf_path)
                final_pdf_path = dest_pdf_path
            else:
                # If no PDF conversion wanted, but file IS PDF, maybe put in source?
                dest_source_path = os.path.join(source_dir, filename)
                shutil.move(local_path, dest_source_path)
                final_pdf_path = dest_source_path  # Return this as the result

            if convert_to_md:
                # We need the path to the file.
                input_path = final_pdf_path
                self.converter.convert_to_markdown(input_path, md_dir)

        else:
            # Other files
            # Move to source or a 'others' dir?
            # Let's put in source for now
            shutil.move(local_path, os.path.join(source_dir, filename))

        # Return the path to the PDF if generated, else the source file
        return (
            final_pdf_path
            if final_pdf_path
            else os.path.join(target_base_dir, filename)
        )

    def get_total_results(self, query: str, **kwargs) -> int:
        # For 3GPP, we can just fetch and count
        results = self.search(query, max_results=None)
        return len(results)
