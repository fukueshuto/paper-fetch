import streamlit as st
from paper_fetch.gui_items.fetcher_info import get_fetcher
from paper_fetch.gui_items.operater import download_papers
from paper_fetch.gui_items.style import inject_sticky_header_css


def results_panel():
    st.markdown(
        '<h1 class="main-header">📚 Search Results</h1>', unsafe_allow_html=True
    )
    with st.container():
        # 2. Settings Area (Outside Form)
        # with st.expander("⚙️ Settings", expanded=False):
        # Download Settings
        # st.markdown("**Download & Conversion Settings**")
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

        # --- Conversion Options ---
        # st.markdown("**Conversion Options**")

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

        # Plan 1: st.pills (Modern & Compact)
        selected_formats = st.pills(
            "Output Format",
            opts,
            default=default_selection,
            selection_mode="multi",
            key="pills_conversion",
            label_visibility="visible",
        )

        # Sync flags for downstream logic
        st.session_state.convert_to_md = "Markdown" in selected_formats
        st.session_state.convert_to_pdf = "PDF" in selected_formats

    # --- Sticky Header Container ---
    inject_sticky_header_css()

    with st.container():
        st.markdown('<div class="sticky-header-marker"></div>', unsafe_allow_html=True)

        # Action Buttons (Download Only)
        col_act_dl_sel, col_act_dl_all = st.columns(2)

        has_results = len(st.session_state.results) > 0
        selected_count = len(st.session_state.selected_papers)
        total_results_count = len(st.session_state.results)
        dl_limit = (
            st.session_state.download_limit
            if not st.session_state.unlimited_download
            else float("inf")
        )
        out_dir = st.session_state.output_dir

        # Initialize dl_button and papers_to_download to avoid UnboundLocalError
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

            # Show estimated wait time
            fetcher_preview = get_fetcher(st.session_state.executed_source)
            if fetcher_preview:
                d_min, d_max = fetcher_preview.get_download_wait_range()
                st.caption(
                    f"⏱️ Estimated wait time: {selected_count * d_min:.1f}s - {selected_count * d_max:.1f}s (per file: {d_min:.1f}s - {d_max:.1f}s)"
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

            # Show estimated wait time
            fetcher_preview = get_fetcher(st.session_state.executed_source)
            if fetcher_preview:
                d_min, d_max = fetcher_preview.get_download_wait_range()
                st.caption(
                    f"⏱️ Estimated wait time: {total_results_count * d_min:.1f}s - {total_results_count * d_max:.1f}s (per file: {d_min:.1f}s - {d_max:.1f}s)"
                )

        if dl_button:
            if papers_to_download:
                if len(papers_to_download) > dl_limit:
                    st.warning(
                        f"Selected ({len(papers_to_download)}) exceeds limit ({dl_limit}). Truncating."
                    )
                    papers_to_download = papers_to_download[: int(dl_limit)]
                download_papers(
                    papers_to_download, out_dir, st.session_state.executed_source
                )
            else:
                st.warning("No papers selected.")

        # Warnings
        if st.session_state.unlimited_download:
            st.warning("⚠️ Unlimited Download: Potential large download and ban risk.")
        elif len(st.session_state.selected_papers) > st.session_state.download_limit:
            st.warning(
                f"⚠️ Selection ({len(st.session_state.selected_papers)}) exceeds download limit ({st.session_state.download_limit}). Only first {st.session_state.download_limit} will be downloaded."
            )

        # Filter Section
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

        # Apply Filters (Moved input to sticky header)
        display_results = results

        if st.session_state.downloadable_only:
            display_results = [p for p in display_results if p.is_downloadable]

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
                    if paper.is_downloadable:
                        badges += ' <span class="badge badge-open">Open Access</span>'
                    else:
                        badges += ' <span class="badge badge-locked">Restricted</span>'

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
