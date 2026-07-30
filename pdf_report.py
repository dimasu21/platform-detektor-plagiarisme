"""
PDF Report Generator Module

Generates professional Turnitin-style plagiarism detection reports
using ReportLab. Supports:
  - Single Compare reports
  - Batch detail (pair) reports
  - Batch summary reports

Each report includes:
  - Header with branding
  - Examiner info, date, method
  - Color-coded similarity score with visual bar
  - Side-by-side text comparison with highlighted matches
  - List of matching K-Gram phrases
  - Embedded highlighted images (if applicable)
  - Footer with page numbers
"""

import io
import os
import re
import logging
from datetime import datetime, timedelta, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.utils import ImageReader

logger = logging.getLogger(__name__)

# ==================== COLOR PALETTE ====================

COLOR_PRIMARY = colors.HexColor('#1a1a2e')
COLOR_ACCENT = colors.HexColor('#b9ff66')
COLOR_ACCENT_DARK = colors.HexColor('#7fbf3f')
COLOR_HIGH = colors.HexColor('#dc3545')
COLOR_MEDIUM = colors.HexColor('#fd7e14')
COLOR_LOW = colors.HexColor('#ffc107')
COLOR_SAFE = colors.HexColor('#28a745')
COLOR_LIGHT_GRAY = colors.HexColor('#f8f9fa')
COLOR_BORDER = colors.HexColor('#dee2e6')
COLOR_TEXT = colors.HexColor('#212529')
COLOR_TEXT_GRAY = colors.HexColor('#6c757d')
COLOR_WHITE = colors.white
COLOR_HIGHLIGHT_BG = colors.HexColor('#fff3cd')
COLOR_MATCH_RED = colors.HexColor('#dc3545')


# ==================== CUSTOM STYLES ====================

def _get_styles():
    """Create and return custom paragraph styles for the PDF."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontSize=22,
        fontName='Helvetica-Bold',
        textColor=COLOR_PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
        spaceBefore=0,
    ))

    styles.add(ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica',
        textColor=COLOR_TEXT_GRAY,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
    ))

    styles.add(ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=COLOR_PRIMARY,
        spaceBefore=8 * mm,
        spaceAfter=4 * mm,
        borderWidth=0,
        borderPadding=0,
    ))

    styles.add(ParagraphStyle(
        'InfoLabel',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=COLOR_TEXT_GRAY,
    ))

    styles.add(ParagraphStyle(
        'InfoValue',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=COLOR_TEXT,
    ))

    styles.add(ParagraphStyle(
        'BodyText14',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=COLOR_TEXT,
        leading=14,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        'ScoreLarge',
        parent=styles['Normal'],
        fontSize=36,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=2 * mm,
    ))

    styles.add(ParagraphStyle(
        'StatusBadge',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    ))

    styles.add(ParagraphStyle(
        'MatchItem',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=COLOR_TEXT,
        leftIndent=10 * mm,
        spaceBefore=1 * mm,
        spaceAfter=1 * mm,
    ))

    styles.add(ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        textColor=COLOR_TEXT_GRAY,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        'TextColumnHeader',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=COLOR_WHITE,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        'TextColumnBody',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
        textColor=COLOR_TEXT,
        leading=12,
        alignment=TA_LEFT,
    ))

    return styles


# ==================== HELPER FUNCTIONS ====================

def _get_score_color(score):
    """Return the appropriate color for a similarity score."""
    if score >= 90:
        return COLOR_HIGH
    elif score >= 60:
        return COLOR_MEDIUM
    elif score >= 30:
        return COLOR_LOW
    else:
        return COLOR_SAFE


def _get_status_text(score):
    """Return status text based on score."""
    if score >= 90:
        return 'PLAGIAT'
    elif score >= 60:
        return 'WARNING'
    else:
        return 'AMAN'


def _get_status_color(score):
    """Return status color based on score."""
    if score >= 90:
        return COLOR_HIGH
    elif score >= 60:
        return COLOR_MEDIUM
    else:
        return COLOR_SAFE


def _format_datetime_wib():
    """Get current datetime formatted in WIB (UTC+7)."""
    now_utc = datetime.now(timezone.utc)
    wib = now_utc + timedelta(hours=7)
    return wib.strftime('%d %B %Y, %H:%M WIB')


def _truncate_text(text, max_chars=3000):
    """Truncate text if too long for PDF rendering."""
    if not text:
        return ""
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n... [Teks dipotong, terlalu panjang untuk ditampilkan di PDF]"
    return text


def _highlight_matches_in_text(text, matches):
    """
    Return text with matched words wrapped in bold+red font tags for ReportLab.

    Args:
        text: Original text
        matches: List of matched phrases from K-gram detection

    Returns:
        str: Text with ReportLab XML markup for highlighting
    """
    if not text or not matches:
        return _escape_xml(text or "")

    # Extract unique words from matches
    matched_words = set()
    for match in matches:
        words = match.lower().split()
        matched_words.update(words)

    if not matched_words:
        return _escape_xml(text)

    # Build regex to find matched words
    pattern_words = '|'.join(re.escape(w) for w in matched_words)
    pattern = rf'\b({pattern_words})\b'

    # Split and rebuild with highlights
    parts = []
    last_end = 0
    for m in re.finditer(pattern, text, re.IGNORECASE):
        start, end = m.start(), m.end()
        if start > last_end:
            parts.append(_escape_xml(text[last_end:start]))
        parts.append(
            f'<font color="#dc3545"><b>{_escape_xml(text[start:end])}</b></font>'
        )
        last_end = end

    if last_end < len(text):
        parts.append(_escape_xml(text[last_end:]))

    return ''.join(parts)


def _escape_xml(text):
    """Escape special XML characters for ReportLab Paragraph."""
    if not text:
        return ""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    # Replace newlines with <br/> for ReportLab
    text = text.replace('\n', '<br/>')
    return text


def _add_page_number(canvas, doc):
    """Add page number and footer to each page."""
    canvas.saveState()
    page_num = canvas.getPageNumber()

    # Footer line
    canvas.setStrokeColor(COLOR_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 15 * mm, A4[0] - 20 * mm, 15 * mm)

    # Footer text
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(COLOR_TEXT_GRAY)
    canvas.drawString(20 * mm, 10 * mm, f"Dibuat oleh PlagiarismDetector — {_format_datetime_wib()}")
    canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Halaman {page_num}")

    canvas.restoreState()


# ==================== REPORT SECTIONS ====================

def _build_header(styles):
    """Build the report header section."""
    elements = []

    # Title
    elements.append(Paragraph("PLAGIARISM DETECTOR", styles['ReportTitle']))
    elements.append(Paragraph(
        "Laporan Hasil Deteksi Plagiarisme",
        styles['ReportSubtitle']
    ))

    # Decorative line
    elements.append(HRFlowable(
        width="100%", thickness=2, color=COLOR_ACCENT_DARK,
        spaceAfter=6 * mm, spaceBefore=0
    ))

    return elements


def _build_info_table(styles, examiner_name, method,
                      suspect_name=None, source_name=None,
                      doc1_name=None, doc2_name=None):
    """Build the metadata information table."""
    elements = []

    # Build rows
    info_data = [
        ['Pemeriksa', f': {examiner_name}'],
        ['Tanggal', f': {_format_datetime_wib()}'],
        ['Metode', f': {method}'],
    ]

    if suspect_name and source_name:
        info_data.append(['File Suspect', f': {suspect_name}'])
        info_data.append(['File Source', f': {source_name}'])
    elif doc1_name and doc2_name:
        info_data.append(['Dokumen 1', f': {doc1_name}'])
        info_data.append(['Dokumen 2', f': {doc2_name}'])

    # Create styled table
    styled_data = []
    for label, value in info_data:
        styled_data.append([
            Paragraph(f'<b>{label}</b>', styles['InfoLabel']),
            Paragraph(value, styles['InfoValue']),
        ])

    table = Table(styled_data, colWidths=[35 * mm, 130 * mm])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 6 * mm))

    return elements


def _build_score_section(styles, score):
    """Build the similarity score display section."""
    elements = []

    score_color = _get_score_color(score)
    status_text = _get_status_text(score)
    status_color = _get_status_color(score)

    # Score card as a table with colored background
    score_content = [
        [Paragraph("SKOR KEMIRIPAN", ParagraphStyle(
            'ScoreLabel', parent=styles['Normal'],
            fontSize=10, fontName='Helvetica-Bold',
            textColor=COLOR_TEXT_GRAY, alignment=TA_CENTER,
        ))],
        [Spacer(1, 2 * mm)],
        [Paragraph(f'{score}%', ParagraphStyle(
            'ScoreNum', parent=styles['Normal'],
            fontSize=40, fontName='Helvetica-Bold',
            textColor=score_color, alignment=TA_CENTER,
            leading=48, spaceAfter=10
        ))],
        [Spacer(1, 2 * mm)],
    ]

    # Visual progress bar
    bar_width = 120 * mm
    filled_width = bar_width * (score / 100)

    # Status badge
    score_content.append([
        Paragraph(
            f'<font color="#{status_color.hexval()[2:]}">'
            f'Status: <b>{status_text}</b></font>',
            ParagraphStyle(
                'StatusText', parent=styles['Normal'],
                fontSize=12, fontName='Helvetica-Bold',
                alignment=TA_CENTER,
            )
        )
    ])

    score_table = Table(score_content, colWidths=[140 * mm])
    score_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_GRAY),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))

    # Center the score table
    wrapper = Table([[score_table]], colWidths=[170 * mm])
    wrapper.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
    ]))

    elements.append(wrapper)
    elements.append(Spacer(1, 6 * mm))

    return elements


def _build_interpretation_table(styles):
    """Build the score interpretation guide table."""
    elements = []

    elements.append(Paragraph("Panduan Interpretasi Skor", styles['SectionTitle']))

    interp_data = [
        ['Rentang Skor', 'Kategori', 'Keterangan'],
        ['90 - 100%', 'Plagiat', 'Terindikasi kuat plagiarisme — Perlu ditinjau segera'],
        ['60 - 89%', 'Warning', 'Mencurigakan — Perlu investigasi lebih lanjut'],
        ['30 - 59%', 'Risiko Rendah', 'Beberapa frasa umum terdeteksi'],
        ['0 - 29%', 'Aman', 'Minimal atau tidak ada plagiarisme'],
    ]

    # Style rows
    styled_data = []
    for i, row in enumerate(interp_data):
        styled_row = []
        for j, cell in enumerate(row):
            if i == 0:
                styled_row.append(Paragraph(
                    f'<b>{cell}</b>',
                    ParagraphStyle('InterpHeader', parent=styles['Normal'],
                                   fontSize=9, fontName='Helvetica-Bold',
                                   textColor=COLOR_WHITE, alignment=TA_CENTER)
                ))
            else:
                styled_row.append(Paragraph(
                    cell,
                    ParagraphStyle('InterpCell', parent=styles['Normal'],
                                   fontSize=9, fontName='Helvetica',
                                   textColor=COLOR_TEXT, alignment=TA_CENTER if j < 2 else TA_LEFT)
                ))
        styled_data.append(styled_row)

    table = Table(styled_data, colWidths=[30 * mm, 30 * mm, 105 * mm])

    # Row colors for categories
    row_colors = [
        COLOR_PRIMARY,  # header
        colors.HexColor('#f8d7da'),  # high
        colors.HexColor('#fff3cd'),  # medium
        colors.HexColor('#d4edda'),  # low-medium
        colors.HexColor('#d1ecf1'),  # safe
    ]

    style_commands = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROUNDEDCORNERS', [3, 3, 3, 3]),
    ]

    for i, bg_color in enumerate(row_colors):
        style_commands.append(('BACKGROUND', (0, i), (-1, i), bg_color))

    table.setStyle(TableStyle(style_commands))
    elements.append(table)
    elements.append(Spacer(1, 6 * mm))

    return elements


def _build_text_comparison(styles, text1, text2, matches,
                           label1="Jawaban Mahasiswa", label2="Kunci Jawaban"):
    """Build side-by-side text comparison with highlighted matches."""
    elements = []

    elements.append(Paragraph("Perbandingan Teks", styles['SectionTitle']))
    elements.append(Paragraph(
        '<i>Teks berwarna <font color="#dc3545"><b>merah tebal</b></font> '
        '= frasa yang cocok terdeteksi</i>',
        ParagraphStyle('Legend', parent=styles['Normal'],
                       fontSize=9, textColor=COLOR_TEXT_GRAY, spaceAfter=4 * mm)
    ))

    # Truncate texts for PDF
    t1 = _truncate_text(text1, 3000)
    t2 = _truncate_text(text2, 3000)

    # Highlight matches
    t1_highlighted = _highlight_matches_in_text(t1, matches)
    t2_highlighted = _highlight_matches_in_text(t2, matches)

    col_width = 82 * mm

    # Header row
    header_style = ParagraphStyle(
        'ColHeader', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold',
        textColor=COLOR_WHITE, alignment=TA_CENTER
    )
    body_style = ParagraphStyle(
        'ColBody', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica',
        textColor=COLOR_TEXT, leading=12, alignment=TA_LEFT
    )

    data = [
        [
            Paragraph(f'<b>{label1}</b>', header_style),
            Paragraph(f'<b>{label2}</b>', header_style),
        ],
        [
            Paragraph(t1_highlighted, body_style),
            Paragraph(t2_highlighted, body_style),
        ],
    ]

    table = Table(data, colWidths=[col_width, col_width])
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        # Body
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#fff8f8')),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#f8fff8')),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 6 * mm))

    return elements


def _build_matches_list(styles, matches):
    """Build the list of matched K-Gram phrases."""
    elements = []

    elements.append(Paragraph(
        "Frasa Cocok Terdeteksi (K-Gram)", styles['SectionTitle']
    ))

    if not matches:
        elements.append(Paragraph(
            '<i>Tidak ada frasa yang cocok secara signifikan ditemukan.</i>',
            styles['BodyText14']
        ))
    else:
        # Show matches in a numbered list (max 50 to avoid huge PDFs)
        display_matches = matches[:50]
        for i, match in enumerate(display_matches, 1):
            elements.append(Paragraph(
                f'{i}. "{_escape_xml(match)}"',
                styles['MatchItem']
            ))

        if len(matches) > 50:
            elements.append(Paragraph(
                f'<i>... dan {len(matches) - 50} frasa lainnya</i>',
                styles['MatchItem']
            ))

    elements.append(Spacer(1, 6 * mm))
    return elements


def _build_images_section(styles, images1=None, images2=None,
                          label1="Dokumen 1", label2="Dokumen 2"):
    """Embed highlighted document images in the PDF."""
    elements = []

    has_images = (images1 and len(images1) > 0) or (images2 and len(images2) > 0)
    if not has_images:
        return elements

    elements.append(Paragraph(
        "Dokumen Visual dengan Sorotan Plagiarisme", styles['SectionTitle']
    ))
    elements.append(Paragraph(
        '<i>Kotak merah pada gambar menandai area yang terdeteksi plagiarisme</i>',
        ParagraphStyle('ImgLegend', parent=styles['Normal'],
                       fontSize=9, textColor=COLOR_TEXT_GRAY, spaceAfter=4 * mm)
    ))

    max_img_width = 160 * mm
    max_img_height = 200 * mm

    def add_images(image_paths, label):
        sub_elements = []
        sub_elements.append(Paragraph(f'<b>{_escape_xml(label)}</b>', ParagraphStyle(
            'ImgLabel', parent=styles['Normal'],
            fontSize=11, fontName='Helvetica-Bold',
            textColor=COLOR_PRIMARY, spaceBefore=4 * mm, spaceAfter=3 * mm
        )))

        for idx, img_path in enumerate(image_paths):
            # Resolve absolute path
            if not os.path.isabs(img_path):
                abs_path = os.path.join('static', img_path)
            else:
                abs_path = img_path

            if not os.path.exists(abs_path):
                logger.warning(f"Image not found: {abs_path}")
                continue

            try:
                img = Image(abs_path)
                # Scale to fit
                iw, ih = img.drawWidth, img.drawHeight
                if iw > 0 and ih > 0:
                    ratio = min(max_img_width / iw, max_img_height / ih, 1.0)
                    img.drawWidth = iw * ratio
                    img.drawHeight = ih * ratio
                sub_elements.append(img)
                sub_elements.append(Paragraph(
                    f'Halaman {idx + 1}',
                    ParagraphStyle('PageNum', parent=styles['Normal'],
                                   fontSize=8, textColor=COLOR_TEXT_GRAY,
                                   alignment=TA_CENTER, spaceAfter=3 * mm)
                ))
            except Exception as e:
                logger.error(f"Error embedding image {abs_path}: {e}")

        return sub_elements

    if images1:
        elements.extend(add_images(images1, label1))
    if images2:
        elements.extend(add_images(images2, label2))

    elements.append(Spacer(1, 6 * mm))
    return elements


# ==================== PUBLIC REPORT GENERATORS ====================

def generate_single_report(examiner_name, suspect_filename, source_filename,
                           similarity_score, matches,
                           suspect_text, source_text,
                           suspect_images=None, source_images=None):
    """
    Generate a PDF report for a single comparison.

    Args:
        examiner_name: Name of the examiner/user
        suspect_filename: Name of the suspect file
        source_filename: Name of the source file
        similarity_score: Similarity percentage (0-100)
        matches: List of matched K-gram phrases
        suspect_text: Original suspect text
        source_text: Original source text
        suspect_images: List of highlighted suspect image paths (optional)
        source_images: List of highlighted source image paths (optional)

    Returns:
        BytesIO: PDF file buffer ready for download
    """
    buffer = io.BytesIO()
    styles = _get_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        title="Laporan Deteksi Plagiarisme - Single Compare",
        author="PlagiarismDetector",
    )

    elements = []

    # Header
    elements.extend(_build_header(styles))

    # Info table
    elements.extend(_build_info_table(
        styles, examiner_name, "Rabin-Karp K-Gram (K=3) — Single Compare",
        suspect_name=suspect_filename, source_name=source_filename
    ))

    # Score
    elements.extend(_build_score_section(styles, similarity_score))

    # Interpretation
    elements.extend(_build_interpretation_table(styles))

    # Text comparison
    if suspect_text and source_text:
        elements.extend(_build_text_comparison(
            styles, suspect_text, source_text, matches,
            label1="Jawaban Mahasiswa", label2="Kunci Jawaban"
        ))

    # Matched phrases
    elements.extend(_build_matches_list(styles, matches))

    # Images
    if suspect_images or source_images:
        elements.append(PageBreak())
        elements.extend(_build_images_section(
            styles, suspect_images, source_images,
            label1="Jawaban Mahasiswa", label2="Kunci Jawaban"
        ))

    # Build PDF
    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)

    buffer.seek(0)
    return buffer


def generate_batch_detail_report(examiner_name, doc1_name, doc2_name,
                                 similarity_score, matches,
                                 doc1_text, doc2_text,
                                 doc1_images=None, doc2_images=None):
    """
    Generate a PDF report for a batch comparison pair detail.

    Args:
        examiner_name: Name of the examiner/user
        doc1_name: Name of document 1
        doc2_name: Name of document 2
        similarity_score: Similarity percentage (0-100)
        matches: List of matched K-gram phrases
        doc1_text: Original text of document 1
        doc2_text: Original text of document 2
        doc1_images: List of doc1 image paths (optional)
        doc2_images: List of doc2 image paths (optional)

    Returns:
        BytesIO: PDF file buffer ready for download
    """
    buffer = io.BytesIO()
    styles = _get_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        title="Laporan Deteksi Plagiarisme - Multi Compare Detail",
        author="PlagiarismDetector",
    )

    elements = []

    # Header
    elements.extend(_build_header(styles))

    # Info table
    elements.extend(_build_info_table(
        styles, examiner_name, "Rabin-Karp K-Gram (K=3) — Multi Compare",
        doc1_name=doc1_name, doc2_name=doc2_name
    ))

    # Score
    elements.extend(_build_score_section(styles, similarity_score))

    # Interpretation
    elements.extend(_build_interpretation_table(styles))

    # Text comparison
    if doc1_text and doc2_text:
        elements.extend(_build_text_comparison(
            styles, doc1_text, doc2_text, matches,
            label1=doc1_name, label2=doc2_name
        ))

    # Matched phrases
    elements.extend(_build_matches_list(styles, matches))

    # Images
    if doc1_images or doc2_images:
        elements.append(PageBreak())
        elements.extend(_build_images_section(
            styles, doc1_images, doc2_images,
            label1=doc1_name, label2=doc2_name
        ))

    # Build PDF
    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)

    buffer.seek(0)
    return buffer


def generate_batch_summary_report(examiner_name, pairs, stats, doc_names=None):
    """
    Generate a PDF summary report for the entire batch comparison.

    Args:
        examiner_name: Name of the examiner/user
        pairs: List of pair comparison results
        stats: Dictionary of batch comparison statistics
        doc_names: List of document names (optional)

    Returns:
        BytesIO: PDF file buffer ready for download
    """
    buffer = io.BytesIO()
    styles = _get_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        title="Laporan Ringkasan Deteksi Plagiarisme - Batch",
        author="PlagiarismDetector",
    )

    elements = []

    # Header
    elements.extend(_build_header(styles))

    # Info
    elements.extend(_build_info_table(
        styles, examiner_name, "Rabin-Karp K-Gram (K=3) — Multi Compare (Batch)"
    ))

    # Summary statistics
    elements.append(Paragraph("Statistik Ringkasan", styles['SectionTitle']))

    stat_data = [
        ['Total Dokumen', str(len(doc_names)) if doc_names else '-'],
        ['Total Perbandingan', str(stats.get('total_comparisons', 0))],
        ['Rata-rata Kemiripan', f"{stats.get('avg_similarity', 0)}%"],
        ['Kemiripan Tertinggi', f"{stats.get('max_similarity', 0)}%"],
        ['Kemiripan Terendah', f"{stats.get('min_similarity', 0)}%"],
    ]

    styled_stat = []
    for label, value in stat_data:
        styled_stat.append([
            Paragraph(f'<b>{label}</b>', styles['InfoLabel']),
            Paragraph(value, styles['InfoValue']),
        ])

    stat_table = Table(styled_stat, colWidths=[45 * mm, 40 * mm])
    stat_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('BACKGROUND', (0, 0), (0, -1), COLOR_LIGHT_GRAY),
    ]))

    elements.append(stat_table)
    elements.append(Spacer(1, 8 * mm))

    # Interpretation guide
    elements.extend(_build_interpretation_table(styles))

    # All pairs table
    elements.append(Paragraph("Detail Semua Perbandingan", styles['SectionTitle']))

    # Table header
    pair_header = [
        Paragraph('<b>No</b>', ParagraphStyle('TH', parent=styles['Normal'],
                  fontSize=9, fontName='Helvetica-Bold', textColor=COLOR_WHITE,
                  alignment=TA_CENTER)),
        Paragraph('<b>Dokumen 1</b>', ParagraphStyle('TH', parent=styles['Normal'],
                  fontSize=9, fontName='Helvetica-Bold', textColor=COLOR_WHITE,
                  alignment=TA_CENTER)),
        Paragraph('<b>Dokumen 2</b>', ParagraphStyle('TH', parent=styles['Normal'],
                  fontSize=9, fontName='Helvetica-Bold', textColor=COLOR_WHITE,
                  alignment=TA_CENTER)),
        Paragraph('<b>Kemiripan</b>', ParagraphStyle('TH', parent=styles['Normal'],
                  fontSize=9, fontName='Helvetica-Bold', textColor=COLOR_WHITE,
                  alignment=TA_CENTER)),
        Paragraph('<b>Status</b>', ParagraphStyle('TH', parent=styles['Normal'],
                  fontSize=9, fontName='Helvetica-Bold', textColor=COLOR_WHITE,
                  alignment=TA_CENTER)),
    ]

    pair_data = [pair_header]

    cell_style = ParagraphStyle('TC', parent=styles['Normal'],
                                fontSize=8, fontName='Helvetica',
                                textColor=COLOR_TEXT, alignment=TA_CENTER)
    cell_style_left = ParagraphStyle('TCL', parent=styles['Normal'],
                                     fontSize=8, fontName='Helvetica',
                                     textColor=COLOR_TEXT, alignment=TA_LEFT)

    for i, pair in enumerate(pairs, 1):
        sim = pair.get('similarity', 0)
        status = _get_status_text(sim)
        status_color_hex = _get_status_color(sim).hexval()[2:]

        pair_data.append([
            Paragraph(str(i), cell_style),
            Paragraph(_escape_xml(pair.get('doc1_name', '')), cell_style_left),
            Paragraph(_escape_xml(pair.get('doc2_name', '')), cell_style_left),
            Paragraph(f'<b>{sim}%</b>', cell_style),
            Paragraph(f'<font color="#{status_color_hex}"><b>{status}</b></font>',
                      cell_style),
        ])

    pair_table = Table(pair_data, colWidths=[10 * mm, 50 * mm, 50 * mm, 25 * mm, 25 * mm])

    pair_style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ]

    # Alternate row colors
    for i in range(1, len(pair_data)):
        bg = COLOR_LIGHT_GRAY if i % 2 == 0 else COLOR_WHITE
        pair_style_commands.append(('BACKGROUND', (0, i), (-1, i), bg))

        # Color-code similarity cells
        sim = pairs[i - 1].get('similarity', 0)
        if sim >= 90:
            pair_style_commands.append(
                ('BACKGROUND', (3, i), (4, i), colors.HexColor('#f8d7da')))
        elif sim >= 60:
            pair_style_commands.append(
                ('BACKGROUND', (3, i), (4, i), colors.HexColor('#fff3cd')))

    pair_table.setStyle(TableStyle(pair_style_commands))
    elements.append(pair_table)
    elements.append(Spacer(1, 8 * mm))

    # Document list
    if doc_names:
        elements.append(Paragraph("Daftar Dokumen", styles['SectionTitle']))
        for i, name in enumerate(doc_names, 1):
            elements.append(Paragraph(
                f'{i}. {_escape_xml(name)}',
                styles['MatchItem']
            ))

    # Build PDF
    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)

    buffer.seek(0)
    return buffer
