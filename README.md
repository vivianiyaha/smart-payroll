# Smart Payroll Payslip Generator

A professional Streamlit application for generating PDF payslips from Excel payroll data.

---

## Features

- **Excel Upload** — Reads payroll data from `.xlsx` files automatically
- **Dashboard** — Real-time metrics: total employees, payroll, deductions, net salary
- **Employee Search** — Search by name with instant results
- **Single Payslip** — Preview + one-click PDF download for any employee
- **Bulk Generation** — Generate all payslips and download as a ZIP archive
- **Settings** — Upload logo, set company name/address and payroll period
- **Professional PDF Design** — Orange-accent A4 layout with earnings table, deductions table, net salary banner, and signature lines

---

## Folder Structure

```
smart_payroll/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md
├── modules/
│   ├── __init__.py
│   ├── data_handler.py       # Excel reading, validation, summaries
│   ├── pdf_generator.py      # ReportLab PDF generation
│   ├── settings.py           # Company settings (session state)
│   └── styles.py             # Custom CSS injection
└── sample_data/
    └── payroll_template.xlsx # Sample Excel file with 5 employees
```

---

## Required Excel Columns

| Column       | Description                |
|-------------|----------------------------|
| STAFF NAME  | Employee full name         |
| BASIC       | Basic salary               |
| HOUSING     | Housing allowance          |
| TRANSPORT   | Transport allowance        |
| TAX         | PAYE tax deduction         |
| PENSION     | Pension deduction          |
| LOAN        | Loan repayment             |
| SAL. ADV.   | Salary advance             |
| PENALTY     | Penalty deduction          |
| TOTAL DED.  | Sum of all deductions      |
| NET SALARY  | Take-home pay              |

> **Note:** `TOTAL DED.` and `NET SALARY` are auto-calculated if missing or zero.

---

## Local Setup

```bash
# 1. Clone or download the project
cd smart_payroll

# 2. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Streamlit Cloud Deployment

1. Push the `smart_payroll/` folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in.
3. Click **New app** → select your repository.
4. Set **Main file path** to `app.py`.
5. Click **Deploy**.

Streamlit Cloud automatically reads `requirements.txt` and installs dependencies.

---

## Usage Guide

### 1. Configure Settings
- Go to **⚙️ Settings** in the sidebar.
- Upload your company logo (PNG/JPG).
- Set company name, address, payroll month, and year.
- Click **Save Settings**.

### 2. Upload Payroll Data
- On any data page, use the file uploader to upload your `.xlsx` file.
- The app validates required columns automatically.

### 3. Generate Payslips
- **Single:** Go to **Generate Single Payslip**, select an employee, preview their details, and click Generate.
- **Bulk:** Go to **Generate Bulk Payslips**, click **Generate All Payslips**, then download the ZIP.

---

## Payslip Calculations

```
Gross Salary     = BASIC + HOUSING + TRANSPORT
Total Deductions = TAX + PENSION + LOAN + SAL. ADV. + PENALTY
Net Salary       = Gross Salary - Total Deductions
```

If `NET SALARY` column already has values in the Excel file, those are used directly.

---

## Tech Stack

| Library      | Purpose                        |
|-------------|-------------------------------|
| Streamlit   | Web UI                        |
| Pandas      | Data processing               |
| OpenPyXL    | Excel file reading            |
| ReportLab   | PDF generation                |
| zipfile     | ZIP archive creation          |
| io.BytesIO  | In-memory file handling       |
