import streamlit as st
import pandas as pd
import io
import zipfile
from datetime import datetime

from modules.data_handler  import load_payroll_data, validate_columns, compute_summaries
from modules.merger        import merge_files, export_excel, export_csv, export_report_pdf
from modules.pdf_generator import generate_payslip_pdf
from modules.settings      import init_settings, render_settings_page, get_settings
from modules.styles        import inject_css

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Payroll Payslip Generator",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
init_settings()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        settings = get_settings()
        logo_b64 = settings.get("logo_b64")
        if logo_b64:
            st.markdown(
                f'<div style="text-align:center;margin-bottom:10px;">'
                f'<img src="data:image/png;base64,{logo_b64}" style="max-width:130px;border-radius:8px;"></div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="sidebar-company">{settings["company_name"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        menu = st.radio(
            "Navigation",
            [
                "📊 Dashboard",
                "🔀 Multi-File Merge",
                "🔍 Employee Search",
                "📄 Generate Single Payslip",
                "📦 Generate Bulk Payslips",
                "📑 Master Payroll Report",
                "🔎 Audit Log",
                "💾 Download ZIP Archive",
                "⚙️ Settings",
            ],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown('<div class="sidebar-footer">© 2025 Smart Payroll</div>', unsafe_allow_html=True)
    return menu


# ═══════════════════════════════════════════════════════════════════════════════
# WORKFLOW STATUS BAR
# ═══════════════════════════════════════════════════════════════════════════════
def render_workflow_status():
    ss = st.session_state
    steps = [
        ("✓ Files Uploaded",     ss.get("files_uploaded_count", 0) > 0),
        ("✓ Records Processed",  ss.get("records_processed", 0) > 0),
        ("✓ Employees Merged",   ss.get("employees_merged", 0) > 0),
        ("✓ Payslips Generated", ss.get("payslips_generated", False)),
    ]
    cols = st.columns(4)
    for col, (label, done) in zip(cols, steps):
        color  = "#E8610A" if done else "#CCCCCC"
        text_c = "#FFFFFF" if done else "#888888"
        col.markdown(
            f'<div style="background:{color};color:{text_c};padding:8px 12px;'
            f'border-radius:8px;font-size:13px;font-weight:600;text-align:center;">'
            f'{label}</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _get_df():
    """Return merged DataFrame from session state, or None."""
    return st.session_state.get("merged_df")


def _metric_card(label, value):
    return (
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div></div>'
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: MULTI-FILE MERGE
# ═══════════════════════════════════════════════════════════════════════════════
def page_merge():
    st.markdown("## 🔀 Multi-File Payroll Merge")
    st.markdown(
        "Upload **two or more** Excel payroll files. "
        "The system will match employees by name and consolidate all components into a single record."
    )

    # ── Upload area ────────────────────────────────────────────────────────
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload Payroll Excel Files (.xlsx) — select multiple",
        type=["xlsx"],
        accept_multiple_files=True,
        help="You can select multiple files at once. All files must contain a STAFF NAME column.",
        key="merge_uploader",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if not uploaded_files:
        st.info("📂 Upload two or more Excel files to begin.")
        return

    # ── Show uploaded file list with remove option ─────────────────────────
    st.markdown("### 📁 Uploaded Files")
    if "removed_files" not in st.session_state:
        st.session_state["removed_files"] = set()

    active_files = [f for f in uploaded_files if f.name not in st.session_state["removed_files"]]

    for uf in active_files:
        c1, c2 = st.columns([6, 1])
        with c1:
            st.markdown(
                f'<div class="file-chip">📄 <b>{uf.name}</b> '
                f'<span style="color:#888;font-size:12px;">({uf.size/1024:.1f} KB)</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            if st.button("✕", key=f"rm_{uf.name}", help="Remove this file"):
                st.session_state["removed_files"].add(uf.name)
                st.rerun()

    active_files = [f for f in uploaded_files if f.name not in st.session_state["removed_files"]]
    if len(active_files) < 1:
        st.warning("No active files. Please upload again.")
        return

    st.markdown("---")

    # ── Merge settings ─────────────────────────────────────────────────────
    st.markdown("### ⚙️ Merge Settings")
    dup_col1, dup_col2 = st.columns([2, 3])
    with dup_col1:
        dup_strategy = st.selectbox(
            "Duplicate Column Treatment",
            options=["sum", "first", "last"],
            format_func=lambda x: {
                "sum":   "➕ Sum Values (Default)",
                "first": "1️⃣ Use First File Value",
                "last":  "🔚 Use Last File Value",
            }[x],
            help="When the same column (e.g. BASIC) appears in multiple files, choose how to handle it.",
        )
    with dup_col2:
        st.markdown(
            '<div style="background:#FFF3EC;border-left:4px solid #E8610A;'
            'padding:10px 14px;border-radius:6px;font-size:13px;margin-top:22px;">'
            '<b>Example:</b> File A: BASIC=100,000 | File B: BASIC=20,000<br>'
            '→ Sum = <b>120,000</b> | First = <b>100,000</b> | Last = <b>20,000</b>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Merge button ───────────────────────────────────────────────────────
    if st.button("🚀 Merge & Consolidate Payroll", type="primary"):
        progress_bar  = st.progress(0, text="Initialising…")
        status_holder = st.empty()

        def _progress(pct, msg):
            progress_bar.progress(pct, text=msg)
            status_holder.markdown(
                f'<div style="color:#E8610A;font-size:13px;font-weight:600;">{msg}</div>',
                unsafe_allow_html=True,
            )

        # Rewind file objects (Streamlit may have partially read them)
        file_list = []
        for uf in active_files:
            uf.seek(0)
            file_list.append((uf, uf.name))

        result = merge_files(file_list, dup_strategy=dup_strategy, progress_cb=_progress)

        progress_bar.empty()
        status_holder.empty()

        # Store in session state
        st.session_state["merged_df"]          = result["merged_df"]
        st.session_state["audit_df"]           = result["audit_df"]
        st.session_state["validation_issues"]  = result["validation_issues"]
        st.session_state["file_summaries"]     = result["file_summaries"]
        st.session_state["earning_cols"]       = result["earning_cols"]
        st.session_state["deduction_cols"]     = result["deduction_cols"]
        st.session_state["files_uploaded_count"] = len(active_files)
        st.session_state["records_processed"]    = sum(s["Employees"] for s in result["file_summaries"])
        st.session_state["employees_merged"]     = len(result["merged_df"])
        st.session_state["zip_ready"]            = False

        mdf = result["merged_df"]

        if mdf.empty:
            st.error("❌ Merge produced no data. Check validation issues below.")
        else:
            st.success(
                f"✅ Merged **{len(active_files)} file(s)** → "
                f"**{len(mdf)} unique employees** consolidated."
            )

    # ── Post-merge display ─────────────────────────────────────────────────
    mdf = st.session_state.get("merged_df")

    # Validation issues
    issues = st.session_state.get("validation_issues", [])
    if issues:
        with st.expander(f"⚠️ Validation Report ({len(issues)} item(s))", expanded=False):
            for iss in issues:
                st.markdown(
                    f'<div class="validation-warn">⚠️ {iss}</div>',
                    unsafe_allow_html=True,
                )

    # File summaries
    summaries = st.session_state.get("file_summaries", [])
    if summaries:
        with st.expander("📁 File Import Summary", expanded=False):
            for s in summaries:
                st.markdown(
                    f'<div class="file-chip">📄 <b>{s["File"]}</b> — '
                    f'{s["Employees"]} employees | Columns: '
                    f'{", ".join(s["Columns"][:8])}{"…" if len(s["Columns"])>8 else ""}</div>',
                    unsafe_allow_html=True,
                )

    # Consolidated preview
    if mdf is not None and not mdf.empty:
        st.markdown("### 👁️ Consolidated Payroll Preview")
        summary = compute_summaries(mdf)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(_metric_card("👥 Employees", summary["total_employees"]), unsafe_allow_html=True)
        with c2:
            st.markdown(_metric_card("💰 Total Gross", f"₦{summary['total_gross']:,.2f}"), unsafe_allow_html=True)
        with c3:
            st.markdown(_metric_card("📉 Total Deductions", f"₦{summary['total_deductions']:,.2f}"), unsafe_allow_html=True)
        with c4:
            st.markdown(_metric_card("✅ Net Salary", f"₦{summary['total_net']:,.2f}"), unsafe_allow_html=True)

        preview_cols = ["STAFF NAME"] + [
            c for c in ["GROSS SALARY","TOTAL DED.","NET SALARY"] if c in mdf.columns
        ]
        st.dataframe(mdf[preview_cols].reset_index(drop=True), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    settings = get_settings()
    logo_b64 = settings.get("logo_b64")

    st.markdown('<div class="page-header">', unsafe_allow_html=True)
    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        if logo_b64:
            st.markdown(
                f'<img src="data:image/png;base64,{logo_b64}" style="max-width:90px;border-radius:8px;margin-top:4px;">',
                unsafe_allow_html=True,
            )
    with col_title:
        st.markdown(f"## {settings['company_name']}")
        st.markdown(f"**Payroll Period:** {settings['payroll_month']} {settings['payroll_year']}")
    st.markdown("</div>", unsafe_allow_html=True)

    df = _get_df()
    if df is None:
        st.info("📂 Upload files via **🔀 Multi-File Merge** (or single file below) to view the dashboard.")

        # Allow single-file quick load
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        single = st.file_uploader("Quick-load single Excel file", type=["xlsx"], key="dash_upload")
        st.markdown("</div>", unsafe_allow_html=True)
        if single:
            try:
                df = load_payroll_data(single)
                st.session_state["merged_df"] = df
                st.session_state["files_uploaded_count"] = 1
                st.session_state["records_processed"]    = len(df)
                st.session_state["employees_merged"]     = len(df)
                st.rerun()
            except Exception as exc:
                st.error(f"❌ {exc}")
        return

    summary = compute_summaries(df)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_metric_card("👥 Total Employees", summary["total_employees"]), unsafe_allow_html=True)
    with c2:
        st.markdown(_metric_card("💰 Total Payroll", f"₦{summary['total_gross']:,.2f}"), unsafe_allow_html=True)
    with c3:
        st.markdown(_metric_card("📉 Total Deductions", f"₦{summary['total_deductions']:,.2f}"), unsafe_allow_html=True)
    with c4:
        st.markdown(_metric_card("✅ Total Net Salary", f"₦{summary['total_net']:,.2f}"), unsafe_allow_html=True)

    st.markdown("### 📋 Payroll Summary Table")
    priority = ["STAFF NAME","BASIC","HOUSING","TRANSPORT","GROSS SALARY","TOTAL DED.","NET SALARY"]
    show = [c for c in priority if c in df.columns]
    extras = [c for c in df.columns if c not in show and not c.startswith("_")]
    st.dataframe(df[show + extras].reset_index(drop=True), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: EMPLOYEE SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
def page_employee_search():
    st.markdown("## 🔍 Employee Search")
    df = _get_df()
    if df is None:
        st.info("📂 Please merge or upload payroll data first.")
        return
    query = st.text_input("Search by employee name", placeholder="Type a name…")
    if query:
        mask = df["STAFF NAME"].str.contains(query, case=False, na=False)
        results = df[mask]
        if results.empty:
            st.warning("No employees matched your search.")
        else:
            st.success(f"Found {len(results)} employee(s)")
            st.dataframe(results.reset_index(drop=True), use_container_width=True)
    else:
        st.dataframe(df.reset_index(drop=True), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SINGLE PAYSLIP
# ═══════════════════════════════════════════════════════════════════════════════
def page_single_payslip():
    st.markdown("## 📄 Generate Single Payslip")
    df = _get_df()
    if df is None:
        st.info("📂 Please merge or upload payroll data first.")
        return

    settings = get_settings()
    names    = df["STAFF NAME"].dropna().tolist()
    selected = st.selectbox("Select Employee", options=names)

    if not selected:
        return

    emp = df[df["STAFF NAME"] == selected].iloc[0]

    # Dynamic earnings / deductions from merged data
    earn_cols = st.session_state.get("earning_cols", ["BASIC","HOUSING","TRANSPORT"])
    ded_cols  = st.session_state.get("deduction_cols", ["TAX","PENSION","LOAN","SAL. ADV.","PENALTY"])
    earn_cols = [c for c in earn_cols if c in emp.index]
    ded_cols  = [c for c in ded_cols  if c in emp.index]

    gross     = sum(float(emp.get(c, 0) or 0) for c in earn_cols)
    total_ded = sum(float(emp.get(c, 0) or 0) for c in ded_cols)
    net       = float(emp.get("NET SALARY", gross - total_ded) or (gross - total_ded))

    st.markdown("### 👤 Employee Preview")
    col_earn, col_ded = st.columns(2)

    with col_earn:
        st.markdown("**Earnings**")
        rows = {c.title(): f"₦{float(emp.get(c,0)):,.2f}" for c in earn_cols}
        rows["**Gross Salary**"] = f"**₦{gross:,.2f}**"
        st.table(pd.DataFrame(list(rows.items()), columns=["Item","Amount"]))

    with col_ded:
        st.markdown("**Deductions**")
        drows = {c.title(): f"₦{float(emp.get(c,0)):,.2f}" for c in ded_cols}
        drows["**Total Deductions**"] = f"**₦{total_ded:,.2f}**"
        st.table(pd.DataFrame(list(drows.items()), columns=["Item","Amount"]))

    st.markdown(
        f'<div class="net-salary-box">💵 NET SALARY: ₦{net:,.2f}</div>',
        unsafe_allow_html=True,
    )

    if st.button("🖨️ Generate & Download PDF Payslip", type="primary"):
        with st.spinner("Generating PDF…"):
            pdf_bytes = generate_payslip_pdf(emp, settings,
                                             earn_cols=earn_cols, ded_cols=ded_cols)
        fname = f"payslip_{selected.replace(' ','_')}_{settings['payroll_month']}_{settings['payroll_year']}.pdf"
        st.download_button("⬇️ Download Payslip PDF", data=pdf_bytes,
                           file_name=fname, mime="application/pdf")
        st.success("✅ Payslip generated successfully!")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: BULK PAYSLIPS
# ═══════════════════════════════════════════════════════════════════════════════
def page_bulk_payslips():
    st.markdown("## 📦 Generate Bulk Payslips")
    df = _get_df()
    if df is None:
        st.info("📂 Please merge or upload payroll data first.")
        return

    settings  = get_settings()
    earn_cols = st.session_state.get("earning_cols", ["BASIC","HOUSING","TRANSPORT"])
    ded_cols  = st.session_state.get("deduction_cols", ["TAX","PENSION","LOAN","SAL. ADV.","PENALTY"])

    st.info(f"Ready to generate payslips for **{len(df)}** employee(s).")

    if st.button("🚀 Generate All Payslips", type="primary"):
        progress  = st.progress(0, text="Generating payslips…")
        zip_buf   = io.BytesIO()
        total     = len(df)

        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, (_, row) in enumerate(df.iterrows(), 1):
                pdf_bytes = generate_payslip_pdf(row, settings,
                                                 earn_cols=earn_cols, ded_cols=ded_cols)
                safe_name = str(row["STAFF NAME"]).replace(" ", "_")
                fname = f"payslip_{safe_name}_{settings['payroll_month']}_{settings['payroll_year']}.pdf"
                zf.writestr(fname, pdf_bytes)
                progress.progress(i / total, text=f"Processing {row['STAFF NAME']}…")

        zip_buf.seek(0)
        st.session_state["zip_data"]          = zip_buf.getvalue()
        st.session_state["zip_ready"]         = True
        st.session_state["payslips_generated"] = True
        progress.empty()
        st.success(f"✅ {total} payslips generated!")

    if st.session_state.get("zip_ready"):
        st.download_button(
            label="⬇️ Download All Payslips (ZIP)",
            data=st.session_state["zip_data"],
            file_name=f"payslips_{settings['payroll_month']}_{settings['payroll_year']}.zip",
            mime="application/zip",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: MASTER PAYROLL REPORT
# ═══════════════════════════════════════════════════════════════════════════════
def page_master_report():
    st.markdown("## 📑 Master Payroll Report")
    df = _get_df()
    if df is None:
        st.info("📂 Please merge or upload payroll data first.")
        return

    settings = get_settings()

    # Show full table
    display_df = df[[c for c in df.columns if not c.startswith("_")]].reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True)

    st.markdown("### ⬇️ Export Consolidated Report")
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("📊 Export as Excel", type="primary"):
            xls = export_excel(display_df)
            st.download_button(
                "⬇️ Download Excel",
                data=xls,
                file_name=f"payroll_report_{settings['payroll_month']}_{settings['payroll_year']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with c2:
        if st.button("📄 Export as CSV", type="primary"):
            csv = export_csv(display_df)
            st.download_button(
                "⬇️ Download CSV",
                data=csv,
                file_name=f"payroll_report_{settings['payroll_month']}_{settings['payroll_year']}.csv",
                mime="text/csv",
            )

    with c3:
        if st.button("🖨️ Export as PDF", type="primary"):
            with st.spinner("Generating PDF report…"):
                pdf = export_report_pdf(display_df, settings)
            st.download_button(
                "⬇️ Download PDF Report",
                data=pdf,
                file_name=f"payroll_report_{settings['payroll_month']}_{settings['payroll_year']}.pdf",
                mime="application/pdf",
            )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: AUDIT LOG
# ═══════════════════════════════════════════════════════════════════════════════
def page_audit_log():
    st.markdown("## 🔎 Payroll Audit Log")
    audit_df = st.session_state.get("audit_df")

    if audit_df is None or audit_df.empty:
        st.info("📂 No audit data available. Merge files first via **🔀 Multi-File Merge**.")
        return

    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">📋 Total Audit Records</div>'
        f'<div class="metric-value">{len(audit_df)}</div></div>',
        unsafe_allow_html=True,
    )

    # Filter controls
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        name_filter = st.text_input("Filter by Employee Name", placeholder="Leave blank for all")
    with col_f2:
        file_opts = ["All Files"] + sorted(audit_df["Source File"].unique().tolist())
        file_filter = st.selectbox("Filter by Source File", options=file_opts)

    filtered = audit_df.copy()
    if name_filter:
        filtered = filtered[filtered["Employee Name"].str.contains(name_filter, case=False, na=False)]
    if file_filter != "All Files":
        filtered = filtered[filtered["Source File"] == file_filter]

    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)

    # Export audit log
    if st.button("⬇️ Export Audit Log as Excel", type="primary"):
        xls = export_excel(filtered)
        settings = get_settings()
        st.download_button(
            "⬇️ Download Audit Log",
            data=xls,
            file_name=f"audit_log_{settings['payroll_month']}_{settings['payroll_year']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DOWNLOAD ZIP
# ═══════════════════════════════════════════════════════════════════════════════
def page_download_zip():
    st.markdown("## 💾 Download ZIP Archive")
    if st.session_state.get("zip_ready"):
        settings = get_settings()
        st.success("✅ ZIP archive is ready for download.")
        st.download_button(
            label="⬇️ Download ZIP Archive",
            data=st.session_state["zip_data"],
            file_name=f"payslips_{settings['payroll_month']}_{settings['payroll_year']}.zip",
            mime="application/zip",
        )
    else:
        st.warning("⚠️ No ZIP archive generated yet. Go to **📦 Generate Bulk Payslips** first.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    # Initialise session state keys
    for key, default in [
        ("zip_ready", False),
        ("payslips_generated", False),
        ("files_uploaded_count", 0),
        ("records_processed", 0),
        ("employees_merged", 0),
        ("removed_files", set()),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    menu = render_sidebar()

    if menu == "⚙️ Settings":
        render_settings_page()
        return

    # Workflow status bar (shown on all data pages)
    render_workflow_status()
    st.markdown("<br>", unsafe_allow_html=True)

    if menu == "📊 Dashboard":
        page_dashboard()
    elif menu == "🔀 Multi-File Merge":
        page_merge()
    elif menu == "🔍 Employee Search":
        page_employee_search()
    elif menu == "📄 Generate Single Payslip":
        page_single_payslip()
    elif menu == "📦 Generate Bulk Payslips":
        page_bulk_payslips()
    elif menu == "📑 Master Payroll Report":
        page_master_report()
    elif menu == "🔎 Audit Log":
        page_audit_log()
    elif menu == "💾 Download ZIP Archive":
        page_download_zip()


if __name__ == "__main__":
    main()
