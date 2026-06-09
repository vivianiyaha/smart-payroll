"""
PDF Generator Module
Generates professional A4 payslip PDFs using ReportLab.
"""

import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Brand colours ──────────────────────────────────────────────────────────────
ORANGE = colors.HexColor("#E8610A")
DARK_GRAY = colors.HexColor("#2C2C2C")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MID_GRAY = colors.HexColor("#CCCCCC")
WHITE = colors.white
TABLE_HEADER_BG = colors.HexColor("#E8610A")
TABLE_ALT_ROW = colors.HexColor("#FFF3EC")


def _currency(value) -> str:
    try:
        return f"₦{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₦0.00"


def generate_payslip_pdf(employee_row, settings: dict) -> bytes:
    """Generate a PDF payslip for one employee and return raw bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_company = ParagraphStyle("company", fontSize=16, textColor=DARK_GRAY,
                                   fontName="Helvetica-Bold", alignment=TA_LEFT, leading=20)
    style_address = ParagraphStyle("address", fontSize=9, textColor=DARK_GRAY,
                                   fontName="Helvetica", alignment=TA_LEFT, leading=13)
    style_period = ParagraphStyle("period", fontSize=11, textColor=WHITE,
                                  fontName="Helvetica-Bold", alignment=TA_CENTER, leading=14)
    style_section = ParagraphStyle("section", fontSize=11, textColor=WHITE,
                                   fontName="Helvetica-Bold", alignment=TA_LEFT, leading=14)
    style_emp = ParagraphStyle("emp", fontSize=11, textColor=DARK_GRAY,
                               fontName="Helvetica-Bold", alignment=TA_LEFT, leading=14)
    style_label = ParagraphStyle("label", fontSize=9, textColor=DARK_GRAY,
                                 fontName="Helvetica", alignment=TA_LEFT)
    style_sig_title = ParagraphStyle("sig_title", fontSize=9, textColor=DARK_GRAY,
                                     fontName="Helvetica-Bold", alignment=TA_CENTER)
    style_footer = ParagraphStyle("footer", fontSize=8, textColor=MID_GRAY,
                                  fontName="Helvetica", alignment=TA_CENTER)
    style_net = ParagraphStyle("net", fontSize=13, textColor=WHITE,
                               fontName="Helvetica-Bold", alignment=TA_RIGHT, leading=16)

    story = []

    # ── Header (logo + company info) ────────────────────────────────────────
    logo_b64 = settings.get("logo_b64")
    header_rows = []
    if logo_b64:
        img_data = base64.b64decode(logo_b64)
        img_buf = io.BytesIO(img_data)
        logo_img = Image(img_buf, width=28 * mm, height=28 * mm, kind="proportional")
        company_para = [
            Paragraph(settings.get("company_name", "Company Name"), style_company),
            Spacer(1, 2),
            Paragraph(settings.get("company_address", "Company Address"), style_address),
        ]
        header_rows = [[logo_img, company_para]]
        header_table = Table(header_rows, colWidths=[35 * mm, None])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
    else:
        header_table = Table([[
            Paragraph(settings.get("company_name", "Company Name"), style_company),
        ]])
        header_table.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))

    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # ── Orange divider ──────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=3, color=ORANGE, spaceAfter=4 * mm))

    # ── Payslip period banner ───────────────────────────────────────────────
    period_text = f"PAYSLIP — {settings.get('payroll_month', 'Month').upper()} {settings.get('payroll_year', datetime.now().year)}"
    period_table = Table([[Paragraph(period_text, style_period)]], colWidths=["100%"])
    period_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ORANGE),
        ("ROUNDEDCORNERS", [4]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(period_table)
    story.append(Spacer(1, 5 * mm))

    # ── Employee info ───────────────────────────────────────────────────────
    emp_name = str(employee_row.get("STAFF NAME", "N/A"))
    emp_info = Table([
        [Paragraph("Employee Name:", style_label), Paragraph(emp_name, style_emp)],
    ], colWidths=[40 * mm, None])
    emp_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(emp_info)
    story.append(Spacer(1, 5 * mm))

    # ── Earnings & Deductions side by side ──────────────────────────────────
    basic = float(employee_row.get("BASIC", 0) or 0)
    housing = float(employee_row.get("HOUSING", 0) or 0)
    transport = float(employee_row.get("TRANSPORT", 0) or 0)
    gross = basic + housing + transport

    tax = float(employee_row.get("TAX", 0) or 0)
    pension = float(employee_row.get("PENSION", 0) or 0)
    loan = float(employee_row.get("LOAN", 0) or 0)
    sal_adv = float(employee_row.get("SAL. ADV.", 0) or 0)
    penalty = float(employee_row.get("PENALTY", 0) or 0)
    total_ded = tax + pension + loan + sal_adv + penalty
    net = float(employee_row.get("NET SALARY", gross - total_ded) or (gross - total_ded))

    # Earnings table data
    earn_rows = [
        ["Basic Salary", _currency(basic)],
        ["Housing Allowance", _currency(housing)],
        ["Transport Allowance", _currency(transport)],
        ["GROSS SALARY", _currency(gross)],
    ]
    # Deductions table data
    ded_rows = [
        ["Tax (PAYE)", _currency(tax)],
        ["Pension", _currency(pension)],
        ["Loan", _currency(loan)],
        ["Salary Advance", _currency(sal_adv)],
        ["Penalty", _currency(penalty)],
        ["TOTAL DEDUCTIONS", _currency(total_ded)],
    ]

    # Build side-by-side columns using nested tables
    col_w = (A4[0] - 36 * mm - 8 * mm) / 2

    def _block_table(header_text, rows):
        hdr_style = ParagraphStyle("bh", fontSize=10, textColor=WHITE,
                                   fontName="Helvetica-Bold", alignment=TA_LEFT, leading=13)
        hdr_row = [Paragraph(header_text, hdr_style), ""]
        all_rows = [hdr_row] + rows
        col1_w = col_w - 38 * mm
        t = Table(all_rows, colWidths=[col1_w, 38 * mm])
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), ORANGE),
            ("SPAN", (0, 0), (-1, 0)),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), DARK_GRAY),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (1, 0), (1, -1), 8),
            ("BACKGROUND", (0, -1), (-1, -1), LIGHT_GRAY),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ]
        for i in range(1, len(all_rows) - 1, 2):
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT_ROW))
        t.setStyle(TableStyle(style_cmds))
        return t

    pair = Table(
        [[_block_table("EARNINGS", earn_rows), _block_table("DEDUCTIONS", ded_rows)]],
        colWidths=[col_w, col_w],
    )
    pair.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (1, 0), (1, -1), 6),
        ("RIGHTPADDING", (0, 0), (0, -1), 6),
    ]))
    story.append(pair)
    story.append(Spacer(1, 5 * mm))

    # ── Net Salary banner ───────────────────────────────────────────────────
    net_row = Table(
        [[Paragraph("NET SALARY:", style_period), Paragraph(_currency(net), style_net)]],
        colWidths=["40%", "60%"],
    )
    net_row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ORANGE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
        ("RIGHTPADDING", (1, 0), (1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(net_row)
    story.append(Spacer(1, 8 * mm))

    # ── Signature section ───────────────────────────────────────────────────
    sig_line = HRFlowable(width="80%", thickness=1, color=DARK_GRAY)
    sig_data = [
        [sig_line, sig_line, sig_line],
        [
            Paragraph("HR Officer", style_sig_title),
            Paragraph("Finance Officer", style_sig_title),
            Paragraph("Employee", style_sig_title),
        ],
        [
            Paragraph("Name & Signature", style_footer),
            Paragraph("Name & Signature", style_footer),
            Paragraph("Name & Signature", style_footer),
        ],
    ]
    sig_table = Table(sig_data, colWidths=["33%", "34%", "33%"])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 6 * mm))

    # ── Footer ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY, spaceBefore=2 * mm))
    footer_text = (
        f"This payslip was generated by Smart Payroll Payslip Generator | "
        f"Generated on {datetime.now().strftime('%d %B %Y')} | "
        f"Confidential – For addressee only"
    )
    story.append(Paragraph(footer_text, style_footer))

    doc.build(story)
    buf.seek(0)
    return buf.read()
