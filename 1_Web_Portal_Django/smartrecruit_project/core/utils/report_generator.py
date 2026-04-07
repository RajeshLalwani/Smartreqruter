import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from django.utils import timezone
from PIL import Image as PILImage

def generate_proctoring_pdf(candidate_name, job_title, frames_data):
    """
    Generates a PDF report containing flagged proctoring frames.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.hexColor("#00d2ff"),
        alignment=1,
        spaceAfter=20
    )
    
    elements = []
    
    # 1. Header
    elements.append(Paragraph(f"Integrity Audit Report: {candidate_name}", title_style))
    elements.append(Paragraph(f"<b>Job Title:</b> {job_title}", styles['Normal']))
    elements.append(Paragraph(f"<b>Audit Date:</b> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # 2. Flagged Frames
    elements.append(Paragraph("<b>Flagged Evidence Matrix</b>", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    for idx, item in enumerate(frames_data):
        # Decode base64 frame
        try:
            img_b64 = item['frame']
            if ',' in img_b64:
                img_b64 = img_b64.split(',')[1]
            
            img_data = base64.b64decode(img_b64)
            img_io = io.BytesIO(img_data)
            
            # Use PIL to handle potential format issues and get size
            pil_img = PILImage.open(img_io)
            width, height = pil_img.size
            aspect = height / float(width)
            
            # Scale to fit PDF width (500 units)
            disp_width = 400
            disp_height = disp_width * aspect
            
            img_element = Image(img_io, width=disp_width, height=disp_height)
            
            # Metadata Table
            meta_data = [
                [f"Frame #{idx+1}", f"Timestamp: {item['timestamp']}"],
                ["Violations:", ", ".join(item['violations']) if item['violations'] else "Suspicious Activity"]
            ]
            t = Table(meta_data, colWidths=[100, 300])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.hexColor("#0a0b10")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.hexColor("#00d2ff")),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
            ]))
            
            elements.append(img_element)
            elements.append(t)
            elements.append(Spacer(1, 30))
            
            # Page Break every 2 frames
            if (idx + 1) % 2 == 0:
                from reportlab.platypus import PageBreak
                elements.append(PageBreak())
                
        except Exception as e:
            elements.append(Paragraph(f"Error processing frame {idx+1}: {e}", styles['Normal']))

    doc.build(elements)
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content
