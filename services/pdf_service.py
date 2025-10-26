from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import Dict, List, Any
from datetime import datetime


class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for the PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#6b7280'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#374151'),
            spaceAfter=10,
            spaceBefore=12
        ))
        
        # Activity time style
        self.styles.add(ParagraphStyle(
            name='ActivityTime',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#059669'),
            fontName='Helvetica-Bold'
        ))
        
        # Activity title style
        self.styles.add(ParagraphStyle(
            name='ActivityTitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#111827'),
            fontName='Helvetica-Bold',
            spaceAfter=4
        ))
    
    def generate_itinerary_pdf(self, itinerary_data: Dict[str, Any]) -> BytesIO:
        """Generate a PDF from itinerary data"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Get data
        location = itinerary_data.get('location', 'Unknown')
        origin = itinerary_data.get('origin', '')
        duration = itinerary_data.get('duration', 0)
        days = itinerary_data.get('days', [])
        total_cost = itinerary_data.get('total_estimated_cost', 0)
        summary = itinerary_data.get('summary', '')
        
        # Title
        title = f"Trip to {location}"
        if origin:
            title = f"Trip from {origin} to {location}"
        
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Paragraph(f"{duration} Days • Generated on {datetime.now().strftime('%B %d, %Y')}", 
                              self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Budget Summary
        if total_cost > 0:
            story.append(Paragraph("Budget Summary", self.styles['SectionHeading']))
            budget_table = Table([
                ['Total Estimated Cost', f'${total_cost:.2f}']
            ], colWidths=[3*inch, 2*inch])
            budget_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecfdf5')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#059669')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#10b981'))
            ]))
            story.append(budget_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Summary
        if summary:
            story.append(Paragraph("Trip Summary", self.styles['SectionHeading']))
            story.append(Paragraph(summary, self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
        
        # Daily Itinerary
        for day in days:
            day_num = day.get('day', 0)
            date = day.get('date', '')
            items = day.get('items', [])
            
            # Day header
            day_title = f"Day {day_num}"
            if date:
                day_title += f" - {date}"
            
            story.append(PageBreak() if day_num > 1 else Spacer(1, 0.2*inch))
            story.append(Paragraph(day_title, self.styles['SectionHeading']))
            
            # Activities table
            table_data = [['Time', 'Activity', 'Type', 'Cost']]
            
            for item in items:
                time = item.get('time', '')
                title = item.get('title', '')
                item_type = item.get('type', '').capitalize()
                cost = item.get('cost', 0)
                cost_str = f'${cost:.2f}' if cost > 0 else 'Free'
                
                table_data.append([time, title, item_type, cost_str])
            
            # Create table
            if len(table_data) > 1:
                activities_table = Table(table_data, colWidths=[1*inch, 3*inch, 1*inch, 1*inch])
                activities_table.setStyle(TableStyle([
                    # Header
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, 0), 12),
                    
                    # Alternating row colors
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#374151')),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ]))
                story.append(activities_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

