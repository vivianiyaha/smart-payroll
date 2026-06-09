"""
Smart Payroll Payslip Generator
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import io
import zipfile
import base64
from datetime import datetime

from modules.data_handler import load_payroll_data, validate_columns, compute_summaries
from modules.pdf_generator import generate_payslip_pdf
from modules.settings import init_settings, render_settings_page, get_settings
from modules.styles import inject_css

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Payroll Payslip Generator",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
init_settings()

# ── Sidebar ───────────────────────────────────────────────────────────────────
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
                "🔍 Employee Search",
                "📄 Generate Single Payslip",
                "📦 Generate Bulk Payslips",
                "💾 Download ZIP Archive",
                "⚙️ Settings",
            ],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown(
            '<div class="sidebar-footer">© 2025 Smart Payroll</div>',
            unsafe_allow_html=True,
        )
    return menu


# ── File upload widget (shared across pages) ──────────────────────────────────
def upload_section():
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload Payroll Excel File (.xlsx)",
        type=["xlsx"],
        help="Upload your payroll spreadsheet. Required columns: STAFF NAME, BASIC, HOUSING, TRANSPORT, TAX, PENSION, LOAN, SAL. ADV., PENALTY, TOTAL DED., NET SALARY",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return uploaded


# ── Dashboard page ────────────────────────────────────────────────────────────
def page_dashboard(df):
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

    if df is None:
        st.info("📂 Please upload a payroll Excel file to view the dashboard.")
        return

    summary = compute_summaries(df)

    c1, c2, c3, c4 = st.columns(4)
    metric_style = "metric-card"
    with c1:
        st.markdown(
            f'<div class="{metric_style}"><div class="metric-label">👥 Total Employees</div>'
            f'<div class="metric-value">{summary["total_employees"]}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="{metric_style}"><div class="metric-label">💰 Total Payroll</div>'
            f'<div class="metric-value">₦{summary["total_gross"]:,.2f}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="{metric_style}"><div class="metric-label">📉 Total Deductions</div>'
            f'<div class="metric-value">₦{summary["total_deductions"]:,.2f}</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="{metric_style}"><div class="metric-label">✅ Total Net Salary</div>'
            f'<div class="metric-value">₦{summary["total_net"]:,.2f}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 📋 Payroll Summary Table")
    display_cols = ["STAFF NAME", "BASIC", "HOUSING", "TRANSPORT", "TOTAL DED.", "NET SALARY"]
    available = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available].reset_index(drop=True), use_container_width=True)


# ── Employee search page ──────────────────────────────────────────────────────
def page_employee_search(df):
    st.markdown("## 🔍 Employee Search")
    if df is None:
        st.info("📂 Please upload a payroll Excel file first.")
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


# ── Single payslip page ───────────────────────────────────────────────────────
def page_single_payslip(df):
    st.markdown("## 📄 Generate Single Payslip")
    if df is None:
        st.info("📂 Please upload a payroll Excel file first.")
        return

    settings = get_settings()
    names = df["STAFF NAME"].dropna().tolist()
    selected = st.selectbox("Select Employee", options=names)

    if selected:
        emp = df[df["STAFF NAME"] == selected].iloc[0]

        st.markdown("### 👤 Employee Preview")
        col_earn, col_ded = st.columns(2)

        with col_earn:
            st.markdown("**Earnings**")
            basic = float(emp.get("BASIC", 0) or 0)
            housing = float(emp.get("HOUSING", 0) or 0)
            transport = float(emp.get("TRANSPORT", 0) or 0)
            gross = basic + housing + transport
            earn_data = {
                "Item": ["Basic Salary", "Housing Allowance", "Transport Allowance", "**Gross Salary**"],
                "Amount (₦)": [f"{basic:,.2f}", f"{housing:,.2f}", f"{transport:,.2f}", f"**{gross:,.2f}**"],
            }
            st.table(pd.DataFrame(earn_data))

        with col_ded:
            st.markdown("**Deductions**")
            tax = float(emp.get("TAX", 0) or 0)
            pension = float(emp.get("PENSION", 0) or 0)
            loan = float(emp.get("LOAN", 0) or 0)
            sal_adv = float(emp.get("SAL. ADV.", 0) or 0)
            penalty = float(emp.get("PENALTY", 0) or 0)
            total_ded = tax + pension + loan + sal_adv + penalty
            net = float(emp.get("NET SALARY", gross - total_ded) or (gross - total_ded))

            ded_data = {
                "Item": ["Tax", "Pension", "Loan", "Salary Advance", "Penalty", "**Total Deductions**"],
                "Amount (₦)": [
                    f"{tax:,.2f}", f"{pension:,.2f}", f"{loan:,.2f}",
                    f"{sal_adv:,.2f}", f"{penalty:,.2f}", f"**{total_ded:,.2f}**",
                ],
            }
            st.table(pd.DataFrame(ded_data))

        st.markdown(
            f'<div class="net-salary-box">💵 NET SALARY: ₦{net:,.2f}</div>',
            unsafe_allow_html=True,
        )

        if st.button("🖨️ Generate & Download PDF Payslip", type="primary"):
            with st.spinner("Generating PDF…"):
                pdf_bytes = generate_payslip_pdf(emp, settings)
            fname = f"payslip_{selected.replace(' ', '_')}_{settings['payroll_month']}_{settings['payroll_year']}.pdf"
            st.download_button(
                label="⬇️ Download Payslip PDF",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
            )
            st.success("✅ Payslip generated successfully!")


# ── Bulk payslip page ─────────────────────────────────────────────────────────
def page_bulk_payslips(df):
    st.markdown("## 📦 Generate Bulk Payslips")
    if df is None:
        st.info("📂 Please upload a payroll Excel file first.")
        return

    settings = get_settings()
    st.info(f"Ready to generate payslips for **{len(df)}** employee(s).")

    if st.button("🚀 Generate All Payslips", type="primary"):
        progress = st.progress(0, text="Generating payslips…")
        zip_buf = io.BytesIO()

        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, (_, row) in enumerate(df.iterrows(), 1):
                pdf_bytes = generate_payslip_pdf(row, settings)
                fname = f"payslip_{str(row['STAFF NAME']).replace(' ', '_')}_{settings['payroll_month']}_{settings['payroll_year']}.pdf"
                zf.writestr(fname, pdf_bytes)
                progress.progress(i / len(df), text=f"Processing {row['STAFF NAME']}…")

        zip_buf.seek(0)
        st.session_state["zip_data"] = zip_buf.getvalue()
        st.session_state["zip_ready"] = True
        progress.empty()
        st.success(f"✅ {len(df)} payslips generated!")

    if st.session_state.get("zip_ready"):
        st.download_button(
            label="⬇️ Download All Payslips (ZIP)",
            data=st.session_state["zip_data"],
            file_name=f"payslips_{settings['payroll_month']}_{settings['payroll_year']}.zip",
            mime="application/zip",
        )


# ── Download ZIP page ─────────────────────────────────────────────────────────
def page_download_zip(df):
    st.markdown("## 💾 Download ZIP Archive")
    if df is None:
        st.info("📂 Please upload a payroll Excel file first.")
        return

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
        st.warning("⚠️ No ZIP archive generated yet. Go to **Generate Bulk Payslips** first.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if "zip_ready" not in st.session_state:
        st.session_state["zip_ready"] = False

    menu = render_sidebar()

    if menu == "⚙️ Settings":
        render_settings_page()
        return

    # File upload (shown on all data pages)
    uploaded = upload_section()
    df = None

    if uploaded:
        try:
            df = load_payroll_data(uploaded)
            errors = validate_columns(df)
            if errors:
                st.error(f"❌ Missing required columns: {', '.join(errors)}")
                df = None
            else:
                st.success(f"✅ Loaded {len(df)} employee records.")
        except Exception as exc:
            st.error(f"❌ Could not read file: {exc}")

    if menu == "📊 Dashboard":
        page_dashboard(df)
    elif menu == "🔍 Employee Search":
        page_employee_search(df)
    elif menu == "📄 Generate Single Payslip":
        page_single_payslip(df)
    elif menu == "📦 Generate Bulk Payslips":
        page_bulk_payslips(df)
    elif menu == "💾 Download ZIP Archive":
        page_download_zip(df)


if __name__ == "__main__":
    main()
