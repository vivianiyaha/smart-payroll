"""
Settings Module
Manages company settings stored in Streamlit session state.
"""

import streamlit as st
import base64
import os
from datetime import datetime


def _load_default_logo() -> str:
    """Load the Cardstel logo bundled in assets/ and return base64 string."""
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "assets", "cardstel_logo.png"
    )
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None


DEFAULTS = {
    "company_name": "Cardstel Solutions Limited",
    "company_address": "Lagos, Nigeria  |  Tel: +234 800 000 0000  |  info@cardstel.com",
    "payroll_month": datetime.now().strftime("%B"),
    "payroll_year": str(datetime.now().year),
    "logo_b64": _load_default_logo(),
}


def init_settings():
    """Initialise settings in session state if not already set."""
    if "settings" not in st.session_state:
        st.session_state["settings"] = dict(DEFAULTS)


def get_settings() -> dict:
    return st.session_state.get("settings", dict(DEFAULTS))


def render_settings_page():
    st.markdown("## ⚙️ Settings")
    s = get_settings()

    with st.form("settings_form"):
        company_name = st.text_input("Company Name", value=s["company_name"])
        company_address = st.text_area("Company Address", value=s["company_address"], height=80)

        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        current_month_idx = months.index(s["payroll_month"]) if s["payroll_month"] in months else 0
        payroll_month = st.selectbox("Payroll Month", options=months, index=current_month_idx)
        payroll_year = st.text_input("Payroll Year", value=s["payroll_year"])

        logo_file = st.file_uploader(
            "Replace Company Logo (PNG/JPG) — leave blank to keep Cardstel logo",
            type=["png", "jpg", "jpeg"],
        )

        submitted = st.form_submit_button("💾 Save Settings", type="primary")

        if submitted:
            logo_b64 = s.get("logo_b64")  # preserve existing logo unless a new one is uploaded
            if logo_file:
                logo_b64 = base64.b64encode(logo_file.read()).decode("utf-8")

            st.session_state["settings"] = {
                "company_name": company_name.strip(),
                "company_address": company_address.strip(),
                "payroll_month": payroll_month,
                "payroll_year": payroll_year.strip(),
                "logo_b64": logo_b64,
            }
            st.success("✅ Settings saved successfully!")

    # Show current logo preview
    if s.get("logo_b64"):
        st.markdown("**Current Logo:**")
        st.markdown(
            f'<img src="data:image/png;base64,{s["logo_b64"]}" '
            f'style="max-width:220px;background:#1C1C1C;padding:12px;border-radius:8px;">',
            unsafe_allow_html=True,
        )
