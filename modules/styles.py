"""
Styles Module
Injects custom CSS into the Streamlit app.
"""

import streamlit as st


def inject_css():
    st.markdown(
        """
        <style>
        /* ── Global ─────────────────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .main { background-color: #FFFFFF; }
        [data-testid="stSidebar"] { background-color: #1C1C2E; }
        [data-testid="stSidebar"] * { color: #FFFFFF !important; }

        /* ── Sidebar brand ─────────────────────────────────────────── */
        .sidebar-company {
            font-size: 15px;
            font-weight: 700;
            color: #E8610A !important;
            text-align: center;
            padding: 4px 0 8px;
        }
        .sidebar-footer {
            font-size: 11px;
            color: #888 !important;
            text-align: center;
            margin-top: 20px;
        }

        /* ── Radio buttons ─────────────────────────────────────────── */
        [data-testid="stSidebar"] .stRadio label {
            font-size: 14px;
            padding: 6px 10px;
            border-radius: 6px;
            transition: background 0.2s;
            cursor: pointer;
        }
        [data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(232,97,10,0.25);
        }

        /* ── Page header ───────────────────────────────────────────── */
        .page-header {
            background: linear-gradient(135deg, #1C1C2E 0%, #2e2e45 100%);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            color: #FFFFFF;
        }
        .page-header h2, .page-header p { color: #FFFFFF !important; margin: 0; }

        /* ── Metric cards ──────────────────────────────────────────── */
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E8E8E8;
            border-left: 5px solid #E8610A;
            border-radius: 10px;
            padding: 18px 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            margin-bottom: 16px;
        }
        .metric-label {
            font-size: 13px;
            color: #888888;
            font-weight: 500;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 22px;
            font-weight: 700;
            color: #1C1C2E;
        }

        /* ── Upload box ─────────────────────────────────────────────── */
        .upload-box {
            background: #FFF8F4;
            border: 2px dashed #E8610A;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 20px;
        }

        /* ── Net salary banner ──────────────────────────────────────── */
        .net-salary-box {
            background: linear-gradient(90deg, #E8610A, #FF8C42);
            color: #FFFFFF;
            font-size: 20px;
            font-weight: 700;
            padding: 14px 24px;
            border-radius: 10px;
            text-align: right;
            margin-top: 10px;
            margin-bottom: 10px;
            box-shadow: 0 4px 12px rgba(232,97,10,0.3);
        }

        /* ── Buttons ────────────────────────────────────────────────── */
        .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #E8610A, #FF8C42) !important;
            border: none !important;
            color: #FFFFFF !important;
            font-weight: 600;
            padding: 10px 24px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(232,97,10,0.3);
            transition: transform 0.1s;
        }
        .stButton > button[kind="primary"]:hover { transform: translateY(-1px); }

        /* ── Download buttons ───────────────────────────────────────── */
        [data-testid="stDownloadButton"] button {
            background: #FFFFFF !important;
            border: 2px solid #E8610A !important;
            color: #E8610A !important;
            font-weight: 600;
            border-radius: 8px;
            padding: 8px 20px;
        }
        [data-testid="stDownloadButton"] button:hover {
            background: #FFF3EC !important;
        }

        /* ── DataFrame ──────────────────────────────────────────────── */
        [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

        /* ── Success / warning / error ───────────────────────────────── */
        .stSuccess { border-left: 4px solid #28a745; border-radius: 6px; }
        .stWarning { border-left: 4px solid #E8610A; border-radius: 6px; }
        .stError   { border-left: 4px solid #dc3545; border-radius: 6px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
