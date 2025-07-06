from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from io import BytesIO
from datetime import datetime
from typing import Dict, Any
from config import STORE_NAME, OWNER_USERNAME, CHANNEL_LINK, CURRENCY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class PDFInvoiceGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Setup custom styles for better Arabic text rendering"""
        # Custom header style
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        # Custom title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Normal'],
            fontSize=16,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Custom normal style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        # Custom footer style
        self.footer_style = ParagraphStyle(
            'CustomFooter',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            alignment=TA_CENTER,
            textColor=colors.grey,
            fontName='Helvetica-Bold'
        )

    def create_invoice(self, sale_data: Dict[str, Any], user_data: Dict[str, Any]) -> BytesIO:
        """Create professional PDF invoice"""
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
            title="Yasiin store"
        )
        
        # Build story
        story = []
        
        # Header
        header_text = "Thank you for purchasing from Yassin Store"
        story.append(Paragraph(header_text, self.header_style))
        story.append(Spacer(1, 20))
        
        # Invoice title
        story.append(Paragraph("PURCHASE INVOICE", self.title_style))
        story.append(Spacer(1, 15))
        
        # Invoice details table
        invoice_data = [
            ['Invoice ID:', sale_data.get('invoice_id', 'N/A')],
            ['Customer ID:', user_data.get('user_id', 'N/A')],
            ['Customer Name:', user_data.get('name', 'Customer')],
            ['Purchase Date:', sale_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
            ['Product:', sale_data.get('product_name', 'N/A')],
            ['Price:', f"{sale_data.get('price', 0):,} {CURRENCY}"],
        ]
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
        invoice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(invoice_table)
        story.append(Spacer(1, 30))
        
        # Product code section
        if sale_data.get('code'):
            story.append(Paragraph("PRODUCT DETAILS:", self.title_style))
            story.append(Spacer(1, 10))
            
            code_data = [
                ['Product Code:', sale_data['code']],
                ['Instructions:', 'Please keep this code safe and follow product instructions']
            ]
            
            code_table = Table(code_data, colWidths=[2*inch, 3*inch])
            code_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(code_table)
            story.append(Spacer(1, 30))
        
        # Contact information
        contact_info = f"""
        Store Information:
        Owner: {OWNER_USERNAME}
        Channel: {CHANNEL_LINK}
        
        Thank you for your purchase!
        For support, contact us through the above channels.
        """
        
        story.append(Paragraph(contact_info, self.normal_style))
        story.append(Spacer(1, 30))
        
        # Footer
        footer_text = "By: Yasiin"
        story.append(Paragraph(footer_text, self.footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def create_simple_invoice(self, sale_data: Dict[str, Any], user_data: Dict[str, Any]) -> BytesIO:
        """Create simple fallback invoice"""
        buffer = BytesIO()
        
        # Create simple text-based invoice
        invoice_text = f"""
=================================
   Thank you for purchasing from Yassin Store
=================================

Invoice ID: {sale_data.get('invoice_id', 'N/A')}
Customer: {user_data.get('name', 'Customer')}
Date: {sale_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}

Product: {sale_data.get('product_name', 'N/A')}
Price: {sale_data.get('price', 0):,} {CURRENCY}

Product Code: {sale_data.get('code', 'N/A')}

Contact:
Owner: {OWNER_USERNAME}
Channel: {CHANNEL_LINK}

=================================
By: Yasiin
=================================
        """
        
        buffer.write(invoice_text.encode('utf-8'))
        buffer.seek(0)
        return buffer

    def create_sales_report(self, sales_data: Dict[str, Any], date_range: str = None) -> BytesIO:
        """Create sales report PDF"""
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
            title="Sales Report"
        )
        
        story = []
        
        # Header
        story.append(Paragraph("SALES REPORT", self.header_style))
        story.append(Spacer(1, 20))
        
        if date_range:
            story.append(Paragraph(f"Period: {date_range}", self.normal_style))
            story.append(Spacer(1, 15))
        
        # Sales summary
        total_sales = len(sales_data)
        total_revenue = sum(sale.get('price', 0) for sale in sales_data.values())
        
        summary_data = [
            ['Total Sales:', str(total_sales)],
            ['Total Revenue:', f"{total_revenue:,} {CURRENCY}"],
            ['Report Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Paragraph("By: Yasiin", self.footer_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
