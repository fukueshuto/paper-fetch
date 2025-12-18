import os
import time
import sys
from patchright.sync_api import sync_playwright
import subprocess


def check_and_install_playwright():
    """
    Installs Playwright/Patchright browsers (chromium) using the CLI.
    """
    print("Installing Patchright browsers (chromium)...")
    try:
        subprocess.run(
            [sys.executable, "-m", "patchright", "install", "chromium"], check=True
        )
        print("Patchright browsers installed successfully.")
    except Exception as e:
        print(f"Failed to install Patchright browsers: {e}")


def upload_to_notebooklm(
    output_dir: str,
    mode: str = "new",
    notebook_id: str = None,
    extensions: list = None,
):
    """
    Uploads files in the specified directory to Google NotebookLM.
    Supports chunked uploads (max 50 files per batch) and multiple extensions.

    Args:
        output_dir: Directory containing files.
        mode: "new" to create a new notebook, "existing" to add to an existing one.
        notebook_id: Optional. If provided, directly opens the specific notebook.
        extensions: List of file extensions to upload (e.g. ['pdf', 'docx']). Defaults to ['pdf'].
    """
    if extensions is None:
        extensions = ["pdf"]

    # Normalize extensions
    extensions = [ext.lower().replace(".", "") for ext in extensions]

    # Gather files
    all_files = []
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            if any(f.lower().endswith(f".{ext}") for ext in extensions):
                all_files.append(os.path.join(output_dir, f))

    if not all_files:
        print(f"No files found with extensions {extensions} in {output_dir}")
        return

    # Sort for consistent order
    all_files.sort()

    print(
        f"Found {len(all_files)} files. Initiating NotebookLM upload (Mode: {mode}, ID: {notebook_id})..."
    )

    # NotebookLM limit is 50 sources at once.
    CHUNK_SIZE = 50
    file_chunks = [
        all_files[i : i + CHUNK_SIZE] for i in range(0, len(all_files), CHUNK_SIZE)
    ]
    print(f"Split into {len(file_chunks)} batches (max {CHUNK_SIZE} files/batch).")

    # Validation: warnings for conflicting arguments
    if mode == "new" and notebook_id:
        print(
            "WARNING: 'notebook_id' was provided but mode is 'new'. The ID will be IGNORED and a new notebook will be created."
        )
        notebook_id = None

    user_data_dir = os.path.expanduser("~/.paper_fetch/browser_data")
    os.makedirs(user_data_dir, exist_ok=True)
    print(f"Using browser profile at: {user_data_dir}")

    def cleanup_locks():
        """Removes Singleton lock files if they exist."""
        print("Cleaning up stale browser lock files...")
        for lock_file in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
            path = os.path.join(user_data_dir, lock_file)
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"Removed stale lock file: {path}")
                except Exception as e:
                    print(f"Failed to remove {path}: {e}")

    def kill_existing_chrome_processes():
        """
        Kills any running Chrome processes that are using the specific user_data_dir.
        """
        print(f"Checking for existing Chrome processes using {user_data_dir}...")
        try:
            cmd = ["pgrep", "-f", user_data_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)
            pids = result.stdout.strip().splitlines()

            if pids:
                print(f"Found {len(pids)} existing Chrome process(es). Terminating...")
                for pid in pids:
                    if pid.strip():
                        try:
                            subprocess.run(["kill", "-9", pid], check=False)
                            print(f"Killed process {pid}")
                        except Exception as e:
                            print(f"Failed to kill process {pid}: {e}")
                time.sleep(2)  # Wait for cleanup
            else:
                print("No conflicting Chrome processes found.")
        except Exception as e:
            print(f"Error checking/killing processes: {e}")

    import random
    import json
    import datetime

    def human_delay(min_ms=500, max_ms=1500):
        """Inserts a random delay to simulate human behavior."""
        time.sleep(random.randint(min_ms, max_ms) / 1000.0)

    def save_session_info(page, current_mode, current_id=None):
        """Saves the current notebook info to a JSON file in output_dir."""
        try:
            current_url = page.url
            nb_id = "unknown"
            if "/notebook/" in current_url:
                nb_id = current_url.split("/notebook/")[-1].split("?")[0].split("/")[0]

            # If we know the ID from args, use it if parsing failed
            if nb_id == "unknown" and current_id:
                nb_id = current_id

            session_data = {
                "notebook_id": nb_id,
                "notebook_url": current_url,
                "updated_at": datetime.datetime.now().isoformat(),
                "mode": current_mode,
            }

            json_path = os.path.join(output_dir, "notebooklm_session.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            print(f"Session info saved to: {json_path}")
            return nb_id

        except Exception as e:
            print(f"Failed to save session info: {e}")
            return None

    def find_visible_target(page, selectors):
        for sel in selectors:
            if page.is_visible(sel):
                return sel
        return None

    def click_upload_trigger(page):
        """
        Navigates the UI to open the file chooser.
        Returns the selector that should be clicked to open file chooser, or None.
        """
        # Potential buttons that trigger the file chooser directly
        final_target_selectors = [
            "button:has-text('ファイルをアップロード')",
            "div[role='button']:has-text('ファイルをアップロード')",
            "text=ファイルをアップロード",
            "span:has-text('PDF')",  # Often used for 'PDF / Text file'
            "div:has-text('PDF')",
            "text=PDF",
            # Fallbacks for other file types if text differs (though usually it's the same upload dialog)
            "span:has-text('Upload')",
            "text=Upload",
        ]

        # Buttons that open the menu/modal where the final target resides (Add Source)
        trigger_selectors = [
            "button:has-text('ソースを追加')",
            "div[role='button']:has-text('ソースを追加')",
            "text=ソースを追加",
            "button:has-text('Add source')",
            "text=Add source",
            "button[aria-label='Add source']",
            "button[aria-label='ソースを追加']",
        ]

        # 1. Check if 'Upload File' (final target) is already visible
        target = find_visible_target(page, final_target_selectors)
        if target:
            return target

        # 2. Check for 'Add Source' menu trigger
        trigger = find_visible_target(page, trigger_selectors)
        if trigger:
            print(f"Clicking 'Add Source' trigger: {trigger}")
            try:
                page.click(trigger)
                human_delay(1000, 2000)
                # Now check for final target again
                target = find_visible_target(page, final_target_selectors)
                if target:
                    return target
            except Exception as e:
                print(f"Error clicking triggers: {e}")

        return None

    def check_for_upload_failures(page):
        """
        Inspects the DOM for error indicators on source items.
        Returns a list of error messages or empty list.
        """
        errors = []
        try:
            # Common error indicators in NotebookLM sources:
            # Red text, '!', specific error classes.
            # We look for generic failure text in the source list area.

            # This selector is a guess based on Material Design error patterns or simple text search
            # Ideally we would scope this to the source list container.
            failure_texts = [
                "text=失敗",
                "text=Failed",
                "text=Error",
                "text=エラー",
                "text=Unsupported",
                "text=非対応",
                "mat-icon:has-text('error')",  # Common in Angular/Material apps
                "mat-icon[data-mat-icon-name='warn']",
            ]

            # Simple check: visible text specific to upload errors
            for sel in failure_texts:
                if page.is_visible(sel):
                    # Try to get more context
                    try:
                        el = page.locator(sel).first
                        txt = el.text_content().strip()
                        # parent text might have filename
                        parent_txt = el.locator("..").text_content().strip()
                        errors.append(f"Found error indicator: {txt} in '{parent_txt}'")
                    except Exception:
                        errors.append(f"Found error indicator: {sel}")

            # Also check for "Upload limit reached" or similar specific toasts
            if page.is_visible("text=50"):  # Rough check for "50 limit"
                errors.append("Possible 50 file limit warning detected.")

        except Exception as e:
            print(f"Error checking failures: {e}")

        return errors

    with sync_playwright() as p:
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-background-timer-throttling",
            "--disable-popup-blocking",
            "--disable-renderer-backgrounding",
        ]
        ignore_default_args = ["--enable-automation"]

        browser_context = None
        # attempt launch
        for attempt in range(3):
            try:
                try:
                    kill_existing_chrome_processes()
                except Exception:
                    pass

                print(f"Launching Chrome (Attempt {attempt+1})...")
                browser_context = p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False,
                    args=args,
                    ignore_default_args=ignore_default_args,
                    no_viewport=True,
                    channel="chrome",
                )
                break
            except Exception as e:
                print(f"Launch failed: {e}")
                if "Singleton" in str(e):
                    cleanup_locks()
                    time.sleep(1)
                    continue
                if attempt == 0:
                    check_and_install_playwright()
                elif attempt == 2:
                    raise e

        if not browser_context:
            return

        try:
            human_delay(1000, 2000)
            pages = browser_context.pages
            page = pages[0] if pages else browser_context.new_page()

            # --- NAVIGATION ---
            if notebook_id:
                # Try direct nav
                print(f"Navigating to Notebook ID: {notebook_id}...")
                try:
                    page.goto(f"https://notebooklm.google.com/notebook/{notebook_id}")
                    human_delay(3000, 5000)
                except Exception:
                    pass
            else:
                # Dashboard
                page.goto("https://notebooklm.google.com/")
                human_delay(2000, 3000)

                if mode == "new":
                    # Click New Notebook
                    print("Creating new notebook...")
                    selector = "text=/New Notebook|新しいノートブック|新規作成|作成/"
                    try:
                        page.wait_for_selector(selector, timeout=10000)
                        page.click(selector)
                        human_delay(3000, 5000)
                    except Exception:
                        print(
                            "Could not find New Notebook button (maybe need login? or already in notebook?)"
                        )

            # Wait for notebook load (Project Title or Add Source)
            print("Waiting for Notebook to be ready...")
            try:
                page.wait_for_selector("editable-project-title", timeout=15000)
            except Exception:
                print(
                    "Warning: Project title not found. Assuming we are in a state to try upload."
                )

            # Save session info early if possible
            save_session_info(page, mode, notebook_id)

            # --- BATCH UPLOAD LOOP ---
            total_batches = len(file_chunks)
            for idx, chunk in enumerate(file_chunks):
                batch_num = idx + 1
                print(
                    f"--- Processing Batch {batch_num}/{total_batches} ({len(chunk)} files) ---"
                )

                # 1. Find and Open File Chooser
                upload_target = click_upload_trigger(page)
                if not upload_target:
                    # Fallback: blind click 'PDF' text if nothing found
                    upload_target = "text=PDF"

                print(f"Opening file chooser via: {upload_target}")
                try:
                    with page.expect_file_chooser(timeout=20000) as fc_info:
                        # Ensure we click properly
                        if page.is_visible(upload_target):
                            page.click(upload_target)
                        else:
                            # Try JS click if suspicious
                            page.evaluate(
                                f"document.querySelector('{upload_target}')?.click()"
                            )
                            # If that fails, might time out and user has to do it

                    file_chooser = fc_info.value
                    print(f"Uploading batch {batch_num}...")
                    file_chooser.set_files(chunk)

                    # 2. Wait for upload to process
                    # It takes time for the UI to register files.
                    print("Files submitted. Waiting for processing...")
                    time.sleep(5)

                    # Wait for a bit longer for large batches
                    wait_time = len(chunk) * 1.5  # 1.5s per file estimation
                    print(f"Waiting {wait_time}s for uploads to stabilize...")
                    time.sleep(wait_time)

                    # 3. Check for errors
                    errors = check_for_upload_failures(page)
                    if errors:
                        print(f"⚠️ Potential errors detected in batch {batch_num}:")
                        for err in errors:
                            print(f"  - {err}")
                    else:
                        print(f"Batch {batch_num} appears successful.")

                except Exception as e:
                    print(f"Error in batch {batch_num}: {e}")
                    print("Please check browser and manually upload if needed.")

                # Small pause between batches
                if batch_num < total_batches:
                    print("Preparing next batch...")
                    human_delay(2000, 3000)

            print("All batches processed.")
            print("Browser will remain open. Close it manually to finish.")

            # Keep alive loop
            while True:
                if page.is_closed() or not browser_context.pages:
                    break
                time.sleep(1)

        except Exception as e:
            print(f"Global Error: {e}")
            import traceback

            traceback.print_exc()
            time.sleep(30)  # Wait for user to read
        finally:
            if browser_context:
                try:
                    browser_context.close()
                except Exception:
                    pass
