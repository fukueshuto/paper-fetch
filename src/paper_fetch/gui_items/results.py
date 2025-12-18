import streamlit as st
from paper_fetch.gui_items.fetcher_info import get_fetcher
from paper_fetch.gui_items.operater import download_papers
from paper_fetch.gui_items.style import inject_sticky_header_css
import os
import shutil
from paper_fetch.exporters.notebooklm import upload_to_notebooklm
from paper_fetch.fetchers.utils import generate_filename
from paper_fetch.gui_items.operater import get_default_output_dir


def results_panel():
    # Helper to switch modes
    def switch_to_export():
        st.session_state.in_export_mode = True

    def switch_to_list():
        st.session_state.in_export_mode = False

    if st.session_state.in_export_mode:
        export_view(switch_to_list)
    else:
        results_list_view(switch_to_export)


def export_view(go_back_callback):
    st.markdown(
        '<h1 class="main-header">📤 Export Actions</h1>', unsafe_allow_html=True
    )

    if st.button("⬅️ Back to Results"):
        go_back_callback()
        st.rerun()

    # Determine Target Directory using fallback logic
    # 1. Try last_download_dir from session
    # 2. Try calculated default paths (similar to badge logic)

    candidate_dirs = []
    if st.session_state.last_download_dir:
        candidate_dirs.append(st.session_state.last_download_dir)

    # Calculation logic from results_list_view
    current_query = st.session_state.executed_query
    target_dir_base = st.session_state.executed_save_dir

    if current_query and target_dir_base:  # Ensure we have necessary info
        calc_dir = None
        if target_dir_base == "downloads":
            calc_dir = os.path.join(
                get_default_output_dir(current_query), st.session_state.executed_source
            )
        else:
            calc_dir = os.path.join(target_dir_base, st.session_state.executed_source)

        if calc_dir and calc_dir not in candidate_dirs:
            candidate_dirs.append(calc_dir)

    # Find the first valid directory containing files
    effective_target_dir = None
    for d in candidate_dirs:
        if d and os.path.exists(d):
            # Check for any relevant files (PDFs usually, or just any file)
            if any(os.path.isfile(os.path.join(d, f)) for f in os.listdir(d)):
                effective_target_dir = d
                break

    # Update last_download_dir to the found one if it was missing/wrong
    if (
        effective_target_dir
        and st.session_state.last_download_dir != effective_target_dir
    ):
        st.session_state.last_download_dir = effective_target_dir

    st.info(
        f"Target Directory: **{effective_target_dir or 'Not yet downloaded (Export disabled)'}**"
    )

    # Mode Selection
    export_mode = st.radio(
        "Select Export Destination", ["Cloud Storage", "NotebookLM"], horizontal=True
    )

    # Determine if actions should be allowed
    files_ready = effective_target_dir is not None
    target_dir = effective_target_dir  # Alias for downstream compatibility

    if not files_ready:
        if not effective_target_dir:
            st.warning(
                "⚠️ No papers downloaded yet. Please go back and download papers first."
            )
        else:
            # Should be covered by loop above, but just in case
            st.warning("⚠️ No files found in target directory.")

    # UI based on selection
    if export_mode == "Cloud Storage":
        st.markdown("#### Cloud Copy")
        st.caption("Copy the entire downloaded folder to your Sync Folder.")

        # We allow clicking but show error if settings missing, or verify if files ready
        if st.button(
            "☁️ Copy to Cloud Folder",
            disabled=(
                not files_ready
            ),  # Only disable if no files. If settings missing, we show error on click.
        ):
            if not st.session_state.cloud_sync_dir:
                st.error("Please set Cloud Sync Folder in settings above.")
            elif not os.path.exists(st.session_state.cloud_sync_dir):
                st.error(
                    f"Cloud folder does not exist: {st.session_state.cloud_sync_dir}"
                )
            else:
                src_dir = target_dir
                folder_name = os.path.basename(src_dir)
                dst_dir = os.path.join(st.session_state.cloud_sync_dir, folder_name)
                try:
                    if os.path.exists(dst_dir):
                        st.warning(
                            f"Destination exists. Merging/Overwriting: {dst_dir}"
                        )
                        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                    else:
                        shutil.copytree(src_dir, dst_dir)
                    st.success(f"Successfully copied to {dst_dir}")
                except Exception as e:
                    st.error(f"Copy failed: {e}")

        st.markdown("#### Settings")
        # Cloud Export Settings
        st.text_input(
            "Cloud Sync Folder Path",
            value=st.session_state.cloud_sync_dir,
            key="cloud_sync_dir",
            placeholder="/Users/username/Google Drive/Papers",
            help="If set, downloaded papers can be copied here.",
        )

    elif export_mode == "NotebookLM":
        st.markdown("#### NotebookLM Upload")
        st.caption("Auto-upload all PDFs in folder to Google NotebookLM.")

        # Sub-mode selection
        nb_action = st.radio(
            "Action",
            ["🆕 Create New Notebook", "📂 Add to Existing Notebook"],
            horizontal=True,
        )

        if "Existing" in nb_action:
            # Notebook ID Setting (Only for Existing mode)
            st.text_input(
                "Notebook ID (Optional)",
                key="notebook_id_env",
                help="Specify a Notebook ID to open directly. Leave empty to use Dashboard.",
                placeholder="e.g. f717a90e-a954-4e44-92c0-4dac70406d16",
            )

        # Extension Selection
        # Detect if we have 3GPP source to smart-default
        default_exts = ["pdf"]
        if st.session_state.executed_source == "3gpp":
            default_exts = ["pdf", "docx", "doc"]

        target_extensions = st.multiselect(
            "File Types to Upload",
            ["pdf", "docx", "doc", "txt", "md"],
            default=default_exts,
        )

        info_msg = "ℹ️ This will launch a browser. " + (
            "It will auto-create a new notebook."
            if "New" in nb_action
            else "Please manually open the target notebook in the browser window (or specify ID above)."
        )
        st.info(info_msg)

        if st.button("📓 Upload to NotebookLM", disabled=(not files_ready)):
            from paper_fetch.gui_items.state import save_state

            save_state()  # Save ID setting

            mode_arg = "new" if "New" in nb_action else "existing"
            nb_id_arg = st.session_state.notebook_id_env.strip() or None

            try:
                with st.spinner(
                    f"Running NotebookLM uploader ({mode_arg} mode)... Check opened browser."
                ):
                    upload_to_notebooklm(
                        target_dir,
                        mode=mode_arg,
                        notebook_id=nb_id_arg,
                        extensions=target_extensions,
                    )
                st.success("Automation script finished.")
            except Exception as e:
                st.error(f"NotebookLM Upload failed: {e}")


def results_list_view(go_to_export_callback):
    st.markdown(
        '<h1 class="main-header">📚 Search Results</h1>', unsafe_allow_html=True
    )
    with st.container():
        # 2. Settings Area (Outside Form)
        # Download Settings
        col_save_dir, col_dl_limit, col_dl_unlimited = st.columns(
            3, vertical_alignment="bottom"
        )
        with col_save_dir:
            st.text_input(
                "Save Dir", value=st.session_state.executed_save_dir, key="output_dir"
            )
        with col_dl_limit:
            if st.session_state.unlimited_download:
                st.warning("⚠️ Unlimited Download active.")
            else:
                st.number_input(
                    "Max Download",
                    min_value=1,
                    max_value=50,
                    value=st.session_state.download_limit,
                    key="download_limit",
                )
        with col_dl_unlimited:
            st.checkbox(
                "Unlimited Download",
                value=st.session_state.unlimited_download,
                key="unlimited_download",
            )

        # Options setup
        opts = ["Markdown"]
        if st.session_state.executed_source == "3gpp":
            opts.append("PDF")

        # Determine defaults from current state
        default_selection = []
        if st.session_state.convert_to_md:
            default_selection.append("Markdown")
        if (
            st.session_state.convert_to_pdf
            and st.session_state.executed_source == "3gpp"
        ):
            default_selection.append("PDF")

        selected_formats = st.pills(
            "Output Format",
            opts,
            default=default_selection,
            selection_mode="multi",
            key="pills_conversion",
            label_visibility="visible",
        )

        st.session_state.convert_to_md = "Markdown" in selected_formats
        st.session_state.convert_to_pdf = "PDF" in selected_formats

    # --- Sticky Header Container ---
    inject_sticky_header_css()

    with st.container():
        st.markdown('<div class="sticky-header-marker"></div>', unsafe_allow_html=True)

        # Action Buttons
        col_act_dl_sel, col_act_dl_all, col_act_export = st.columns([2, 2, 1.5])

        has_results = len(st.session_state.results) > 0
        selected_count = len(st.session_state.selected_papers)
        total_results_count = len(st.session_state.results)
        dl_limit = (
            st.session_state.download_limit
            if not st.session_state.unlimited_download
            else float("inf")
        )
        out_dir = st.session_state.output_dir

        dl_button = False
        papers_to_download = []

        with col_act_dl_sel:
            dl_sel_button = st.button(
                f"⬇️ Download Selected ({selected_count})",
                type="primary",
                disabled=selected_count == 0,
                use_container_width=True,
                key="btn_dl_selected",
            )
            if dl_sel_button:
                papers_to_download = [
                    st.session_state.results[i]
                    for i in st.session_state.selected_papers
                ]
                dl_button = True

            fetcher_preview = get_fetcher(st.session_state.executed_source)
            if fetcher_preview:
                d_min, d_max = fetcher_preview.get_download_wait_range()
                st.caption(
                    f"Wait: {selected_count * d_min:.0f}-{selected_count * d_max:.0f}s"
                )

        with col_act_dl_all:
            is_partial_selection = 0 < selected_count < total_results_count
            download_all_disabled = (not has_results) or is_partial_selection
            dl_all_button = st.button(
                "⬇️ Download All",
                disabled=download_all_disabled,
                use_container_width=True,
                key="btn_dl_all",
            )
            if dl_all_button:
                papers_to_download = st.session_state.results
                dl_button = True

            # Shortened wait time caption for layout
            fetcher_preview = get_fetcher(st.session_state.executed_source)
            if fetcher_preview:
                d_min, d_max = fetcher_preview.get_download_wait_range()
                st.caption(
                    f"Wait: {total_results_count * d_min:.0f}-{total_results_count * d_max:.0f}s"
                )

        with col_act_export:
            # Link to Export Mode
            if st.button("🚀 Export Mode", use_container_width=True):
                go_to_export_callback()
                st.rerun()

        if dl_button:
            if papers_to_download:
                if len(papers_to_download) > dl_limit:
                    st.warning(f"Limit exceeded. Truncating to {int(dl_limit)}.")
                    papers_to_download = papers_to_download[: int(dl_limit)]

                final_out_dir = download_papers(
                    papers_to_download, out_dir, st.session_state.executed_source
                )
                if final_out_dir:
                    st.session_state.last_download_dir = final_out_dir
                    # Auto switch to export mode on successful download?
                    # User didn't explicitly ask to auto-switch, but said "button to go there".
                    # Let's show a toast or just let user click.
                    st.success(
                        "Download Complete! Click 'Export Mode' to process further."
                    )
            else:
                st.warning("No papers selected.")

        # Filter Section (Rest of the code remains similar)
        col_f1, col_f2, col_f3, col_show_dl_only = st.columns(
            [2, 1, 1, 1], vertical_alignment="bottom"
        )
        with col_f1:
            st.text_input(
                "Keyword Filter",
                key="filter_keyword",
                placeholder="Title, Author, Abstract",
            )
        with col_f2:
            st.number_input(
                "Min Year",
                min_value=1900,
                max_value=2100,
                value=None,
                step=1,
                key="filter_year_min",
                placeholder="YYYY",
            )
        with col_f3:
            st.number_input(
                "Max Year",
                min_value=1900,
                max_value=2100,
                value=None,
                step=1,
                key="filter_year_max",
                placeholder="YYYY",
            )

        with col_show_dl_only:
            st.checkbox(
                "Show Downloadable Only",
                value=st.session_state.downloadable_only,
                key="downloadable_only",
            )

    # --- Results Area ---
    if st.session_state.results:
        results = st.session_state.results
        display_results = results

        # Determine download availability based on fetcher and method
        fetcher = get_fetcher(st.session_state.executed_source)
        method = st.session_state.executed_download_method

        if st.session_state.downloadable_only:
            display_results = [
                p for p in display_results if fetcher.check_downloadable(p, method)
            ]

        # Determine current effective output directory to check for downloaded files
        # Consolidate logic for where files are expected to be
        current_query = st.session_state.executed_query
        target_dir_base = st.session_state.executed_save_dir

        if target_dir_base == "downloads":
            # If default, it uses the query-based folder
            # However, executed_save_dir might just be 'downloads' string in session state
            # but actual download happened to specific folder.
            # If we rely on get_default_output_dir(current_query), it might mismatch if date changed?
            # Actually, `get_default_output_dir` uses today's date.
            # If I search yesterday and reload today, the date changes.
            # Ideally `executed_save_dir` should store the FULL path if it was auto-generated?
            # But currently it stores what's in the text input.

            # Use last_download_dir if available and it matches the expected structure roughly?
            # Or just check against the generated one for TODAY.
            # LIMITATION: If day changed, "Downloaded" badge might disappear for default "downloads" folder.
            # This is acceptable for simple logic.
            # Better: If st.session_state.last_download_dir exists, check there too?

            check_dirs = []
            if st.session_state.last_download_dir:
                check_dirs.append(st.session_state.last_download_dir)

            # Also check what WOULD be the dir if downloaded now (for immediate feedback before last_download_dir updates or if manual refind)
            calc_dir = os.path.join(
                get_default_output_dir(current_query), st.session_state.executed_source
            )
            if calc_dir not in check_dirs:
                check_dirs.append(calc_dir)

        else:
            # User specified a specific directory
            check_dirs = [
                os.path.join(target_dir_base, st.session_state.executed_source)
            ]

        if st.session_state.filter_keyword:
            kw = st.session_state.filter_keyword.lower()
            display_results = [
                p
                for p in display_results
                if kw in p.title.lower()
                or any(kw in a.lower() for a in p.authors)
                or (p.abstract and kw in p.abstract.lower())
            ]

        if st.session_state.filter_year_min:
            display_results = [
                p
                for p in display_results
                if p.published_date
                and p.published_date.year >= st.session_state.filter_year_min
            ]

        if st.session_state.filter_year_max:
            display_results = [
                p
                for p in display_results
                if p.published_date
                and p.published_date.year <= st.session_state.filter_year_max
            ]

        # List Control Header
        col_ctrl_1, col_ctrl_2, col_ctrl_3 = st.columns(
            [1, 1, 8], vertical_alignment="center"
        )
        with col_ctrl_1:

            def toggle_select_all():
                is_checked = st.session_state.select_all_checkbox
                if is_checked:
                    indices = set(range(len(display_results)))
                    st.session_state.selected_papers = indices
                    for i in range(len(display_results)):
                        st.session_state[f"chk_{i}"] = True
                else:
                    st.session_state.selected_papers = set()
                    for i in range(len(display_results)):
                        st.session_state[f"chk_{i}"] = False

            st.checkbox(
                "Select All", key="select_all_checkbox", on_change=toggle_select_all
            )

        with col_ctrl_2:
            st.caption(f"Showing {len(display_results)} papers")
        with col_ctrl_3:
            st.caption("Results for: " + st.session_state.executed_query)

        # Render List
        for i, paper in enumerate(display_results):
            with st.container():
                col_c1, col_c2 = st.columns([0.5, 10])
                with col_c1:
                    chk_key = f"chk_{i}"
                    if chk_key not in st.session_state:
                        st.session_state[chk_key] = (
                            i in st.session_state.selected_papers
                        )

                    def update_selection(idx=i, key=chk_key):
                        if st.session_state[key]:
                            st.session_state.selected_papers.add(idx)
                        else:
                            st.session_state.selected_papers.discard(idx)

                    st.checkbox(
                        "",
                        key=chk_key,
                        on_change=update_selection,
                        kwargs={"idx": i, "key": chk_key},
                    )

                with col_c2:
                    badges = f'<span class="badge badge-source">{paper.source.upper()}</span>'

                    is_available = fetcher.check_downloadable(paper, method)

                    if is_available:
                        badges += ' <span class="badge badge-open">Open Access</span>'
                    else:

                        badges += ' <span class="badge badge-locked">Restricted</span>'

                    # Check if downloaded
                    is_downloaded = False
                    expected_filename = generate_filename(
                        paper.title, paper.authors, paper.published_date, paper.source
                    )

                    for d in check_dirs:
                        if os.path.exists(os.path.join(d, expected_filename)):
                            is_downloaded = True
                            break

                    if is_downloaded:
                        badges += ' <span class="badge badge-source" style="background-color: #28a745;">✅ Downloaded</span>'

                    st.markdown(
                        f"""
                    <div class="paper-card-compact">
                        <div class="paper-title"><a href="{paper.url}" target="_blank">{paper.title}</a> {badges}</div>
                        <div class="paper-meta">
                            👤 {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''} |
                            📅 {paper.published_date.year if paper.published_date else 'Unknown'}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    with st.expander("📄 Abstract"):
                        st.write(paper.abstract)
                        st.caption(f"PDF URL: {paper.pdf_url}")

    else:
        st.info("No results found.")
