import os
import shutil
import subprocess
import zipfile
import platform
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class Converter:
    def __init__(self):
        self.os_type = platform.system()
        self.has_unzip = shutil.which("unzip") is not None
        self.has_pandoc = shutil.which("pandoc") is not None
        self.has_soffice = self._find_soffice()
        self.has_inkscape = shutil.which("inkscape") is not None
        self.has_pdftotext = shutil.which("pdftotext") is not None

    def _find_soffice(self) -> Optional[str]:
        """Find LibreOffice executable."""
        if self.os_type == "Darwin":
            # Common path on macOS
            path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path

        # Check PATH
        return shutil.which("soffice")

    def check_dependencies(self) -> dict:
        """Check availability of external tools."""
        return {
            "unzip": self.has_unzip,
            "pandoc": self.has_pandoc,
            "libreoffice": self.has_soffice is not None,
            "inkscape": self.has_inkscape,
            "pdftotext": self.has_pdftotext
        }

    def extract_zip(self, zip_path: str, output_dir: str) -> bool:
        """
        Extract ZIP file with encoding handling.
        Tries to use system 'unzip' command first for better encoding support (cp932),
        falls back to Python's zipfile.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Try system unzip first if available (especially for macOS/Linux with encoding flags)
        if self.has_unzip:
            try:
                cmd = ["unzip", "-q", "-o"]

                # Add encoding flag for macOS if supported (usually checks if it accepts -O)
                # For simplicity based on the script, we'll try to use it if we are on macOS
                # The script checked `unzip -h 2>&1 | grep -- "-O"`
                # Here we assume if it's macOS we might want cp932 for 3GPP

                use_encoding_flag = False
                if self.os_type == "Darwin":
                    # Quick check if unzip supports -O
                    try:
                        help_out = subprocess.check_output(["unzip", "-h"], stderr=subprocess.STDOUT).decode()
                        if "-O CHAR" in help_out or "-O charset" in help_out:
                            use_encoding_flag = True
                    except:
                        pass

                if use_encoding_flag:
                    cmd.extend(["-O", "cp932"])

                cmd.extend([zip_path, "-d", output_dir])

                subprocess.run(cmd, check=True, capture_output=True)
                return True
            except subprocess.CalledProcessError as e:
                logger.warning(f"System unzip failed: {e}. Falling back to python zipfile.")
            except Exception as e:
                logger.warning(f"Error using system unzip: {e}. Falling back to python zipfile.")

        # Fallback to Python zipfile
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Python's zipfile doesn't support cp932 decoding for filenames easily before extracting
                # But we can try to iterate and decode manually if needed,
                # or just extractall which uses cp437 or utf-8.
                # For now, standard extractall.
                zf.extractall(output_dir)
            return True
        except Exception as e:
            logger.error(f"Failed to extract zip {zip_path}: {e}")
            return False

    def convert_to_pdf(self, input_path: str, output_dir: str) -> Optional[str]:
        """
        Convert document to PDF using LibreOffice.
        Returns the path to the generated PDF or None if failed.
        """
        if not self.has_soffice:
            logger.warning("LibreOffice (soffice) not found. Skipping PDF conversion.")
            return None

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filename = os.path.basename(input_path)
        base_name = os.path.splitext(filename)[0]
        expected_pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

        try:
            # Create a temporary profile directory to avoid conflicts
            # Using subprocess to call soffice
            # --headless --convert-to pdf --outdir ...

            # Note: soffice is sensitive to user profile locking.
            # The script used a temp profile dir.
            import tempfile
            with tempfile.TemporaryDirectory() as temp_profile_dir:
                env = os.environ.copy()
                # env['UserInstallation'] = f"file://{temp_profile_dir}" # This format depends on OS?
                # The script used -env:UserInstallation="file://$temp_profile_dir" as argument

                cmd = [
                    self.has_soffice,
                    f"-env:UserInstallation=file://{temp_profile_dir}",
                    "--headless",
                    "--convert-to", "pdf",
                    input_path,
                    "--outdir", output_dir
                ]

                # Set a timeout (e.g., 60 seconds)
                subprocess.run(cmd, check=True, capture_output=True, timeout=60)

                if os.path.exists(expected_pdf_path):
                    return expected_pdf_path
                else:
                    logger.error(f"PDF conversion ran but output file not found: {expected_pdf_path}")
                    return None

        except subprocess.TimeoutExpired:
            logger.error(f"PDF conversion timed out for {input_path}")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"PDF conversion failed for {input_path}: {e.stderr.decode() if e.stderr else str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during PDF conversion: {e}")
            return None

    def convert_to_markdown(self, input_path: str, output_dir: str) -> Optional[str]:
        """
        Convert document to Markdown.
        Supports:
        - .docx -> Markdown (via Pandoc)
        - .pdf -> Markdown (via pdftotext, basic text extraction)

        Returns the path to the generated Markdown file or None if failed.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filename = os.path.basename(input_path)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{base_name}.md")
        ext = os.path.splitext(filename)[1].lower()

        if ext == '.pdf':
            if not self.has_pdftotext:
                logger.warning("pdftotext not found. Skipping PDF to Markdown conversion.")
                return None

            try:
                # pdftotext -layout input.pdf output.md (technically output is text, but we treat as MD)
                # We use -layout to preserve some structure
                cmd = ["pdftotext", "-layout", input_path, output_path]
                subprocess.run(cmd, check=True, capture_output=True)
                return output_path
            except subprocess.CalledProcessError as e:
                logger.error(f"pdftotext conversion failed for {input_path}: {e.stderr.decode() if e.stderr else str(e)}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error during pdftotext conversion: {e}")
                return None

        elif ext in ['.docx', '.doc', '.odt']:
            if not self.has_pandoc:
                logger.warning("Pandoc not found. Skipping Markdown conversion.")
                return None

            # Temp dir for media extraction
            import tempfile
            with tempfile.TemporaryDirectory() as temp_media_dir:
                try:
                    # Adjust command to extract to a persistent location
                    media_dir = os.path.join(output_dir, "media")
                    cmd = [
                        "pandoc",
                        "-f", "docx", # Assuming docx for now, but pandoc can auto-detect often
                        "-t", "markdown",
                        input_path,
                        f"--extract-media={output_dir}", # This usually creates a 'media' folder in output_dir
                        "-o", output_path
                    ]

                    subprocess.run(cmd, check=True, capture_output=True)

                    # Optional: Convert WMF/EMF to PNG if Inkscape is available
                    if self.has_inkscape:
                        self._convert_wmf_emf_to_png(os.path.join(output_dir, "media"))

                    return output_path

                except subprocess.CalledProcessError as e:
                    logger.error(f"Pandoc conversion failed for {input_path}: {e.stderr.decode() if e.stderr else str(e)}")
                    return None
                except Exception as e:
                    logger.error(f"Unexpected error during Pandoc conversion: {e}")
                    return None

        else:
            logger.warning(f"Unsupported file type for Markdown conversion: {ext}")
            return None

    def _convert_wmf_emf_to_png(self, media_dir: str):
        """Convert WMF/EMF images in the directory to PNG using Inkscape."""
        if not os.path.exists(media_dir):
            return

        for root, _, files in os.walk(media_dir):
            for file in files:
                if file.lower().endswith(('.wmf', '.emf')):
                    file_path = os.path.join(root, file)
                    output_png = os.path.splitext(file_path)[0] + ".png"
                    try:
                        # inkscape "input" --export-type="png" --export-filename="output"
                        cmd = [
                            "inkscape",
                            file_path,
                            "--export-type=png",
                            f"--export-filename={output_png}"
                        ]
                        subprocess.run(cmd, check=True, capture_output=True)
                    except Exception as e:
                        logger.warning(f"Failed to convert image {file}: {e}")
