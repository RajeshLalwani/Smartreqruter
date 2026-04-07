import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.core.files.base import ContentFile

def generate_offer_letter_pdf(candidate_name, role, salary, joining_date):
    """
    Phase 2 Flow C: Enterprise-grade PDF generation via ReportLab.
    Injects professional branding, a dynamic CTC table, and specific terms.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=inch, leftMargin=inch,
        topMargin=inch, bottomMargin=inch
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#0a0b10'),
        alignment=1, # Center
        spaceAfter=20,
    )
    
    h2_style = ParagraphStyle(
        name='Heading2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#00acc1'), # Closer to cyan for text readability
        spaceBefore=15,
        spaceAfter=10,
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.spaceAfter = 10
    normal_style.leading = 14
    
    elements = []
    
    # 1. Branding Header
    elements.append(Paragraph("RAJ'S TECH EMPIRE", title_style))
    elements.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor('#00E5FF'), spaceAfter=20))
    
    # 2. Date & Salutation
    current_date = datetime.now().strftime("%B %d, %Y")
    elements.append(Paragraph(f"Date: <b>{current_date}</b>", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Dear <b>{candidate_name}</b>,", normal_style))
    
    # 3. Intro Body
    intro_text = (
        f"We are thrilled to formally offer you the position of <b>{role}</b> at Raj's Tech Empire. "
        "Your technical expertise and impressive performance during our grueling AI-driven interview process were exceptional. "
        f"Your anticipated start date is <b>{joining_date}</b>."
    )
    elements.append(Paragraph(intro_text, normal_style))
    elements.append(Spacer(1, 10))
    
    # 4. CTC Table Breakdown
    elements.append(Paragraph("<b>Compensation Structure & Breakdown</b>", h2_style))
    
    # Safely extract digits for CTC calculation
    try:
        base_salary = float(''.join(c for c in str(salary) if c.isdigit() or c == '.')) or 1000000
    except Exception:
        base_salary = 1200000 # default fallback
        
    hra = base_salary * 0.40
    pf = base_salary * 0.12
    bonus = base_salary * 0.10
    total_ctc = base_salary + hra + pf + bonus
    
    data = [
        ['Component', 'Annual Amount (INR)'],
        ['Basic Salary', f"Rs. {base_salary:,.2f}"],
        ['House Rent Allowance (HRA)', f"Rs. {hra:,.2f}"],
        ['Provident Fund (PF)', f"Rs. {pf:,.2f}"],
        ['Performance Bonus (Variable)', f"Rs. {bonus:,.2f}"],
        ['Total Target Compensation (CTC)', f"Rs. {total_ctc:,.2f}"]
    ]
    
    t = Table(data, colWidths=[3.5 * inch, 2.5 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a0b10')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f2f2f2')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), # Highlight total row
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#0a0b10'))
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # 5. Terms & Conditions
    elements.append(Paragraph("<b>Standard Terms and Conditions</b>", h2_style))
    terms = [
        "1. <b>Probation:</b> Your employment is subject to a standard 90-day probationary period.",
        "2. <b>Exclusivity:</b> You agree to devote your full-time professional efforts exclusively to Raj's Tech Empire.",
        "3. <b>Confidentiality:</b> You are required to sign a strict Non-Disclosure Agreement (NDA) prior to onboarding.",
        "4. <b>Validity:</b> This offer is valid for exactly 3 days from the date of issuance. Failure to accept will result in automated rejection."
    ]
    for term in terms:
        elements.append(Paragraph(term, normal_style))
        
    elements.append(Spacer(1, 40))
    
    # 6. Signatures
    elements.append(Paragraph("Sincerely,", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Raj</b>", normal_style))
    elements.append(Paragraph("Principal Systems Architect & CTO", normal_style))
    elements.append(Paragraph("Raj's Tech Empire", normal_style))
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return ContentFile(pdf_bytes)
