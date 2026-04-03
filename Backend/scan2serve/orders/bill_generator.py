"""
Bill PDF generator for Scan2Serve.
Adapted to your Order / OrderItem / Table model structure.

OrderItem.price is stored as line total (unit_price × qty) — per your serializer.
Order.total_amount is the pre-computed grand total stored on the model.
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, KeepTogether
)


def generate_bill_pdf(order) -> bytes:
    """
    Generate a PDF bill for the given Order instance.
    Returns raw PDF bytes ready for HttpResponse or email attachment.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()

    # ── Custom styles ──────────────────────────────────────────────────────────
    def style(name, **kwargs):
        return ParagraphStyle(name, parent=styles["Normal"], **kwargs)

    title_s    = style("T", fontSize=20, spaceAfter=4, alignment=TA_CENTER,
                       fontName="Helvetica-Bold", textColor=colors.HexColor("#1a1a2e"))
    sub_s      = style("S", fontSize=10, alignment=TA_CENTER,
                       textColor=colors.HexColor("#555555"), spaceAfter=2)
    sec_s      = style("H", fontSize=9,  textColor=colors.HexColor("#888888"), spaceAfter=2)
    left_s     = style("L", fontSize=10, alignment=TA_LEFT)
    right_s    = style("R", fontSize=10, alignment=TA_RIGHT)
    total_s    = style("Tot", fontSize=13, fontName="Helvetica-Bold",
                       alignment=TA_RIGHT, textColor=colors.HexColor("#1a1a2e"))
    footer_s   = style("F", fontSize=8, alignment=TA_CENTER,
                       textColor=colors.HexColor("#aaaaaa"))

    story = []

    # ── Resolve restaurant info via table FK ───────────────────────────────────
    tbl        = order.table
    restaurant = getattr(tbl, "restaurant", None)
    rest_name  = getattr(restaurant, "name",    "Scan2Serve Restaurant") if restaurant else "Scan2Serve Restaurant"
    rest_addr  = getattr(restaurant, "address", "") if restaurant else ""
    rest_phone = getattr(restaurant, "phone",   "") if restaurant else ""
    # Support table.number or table.table_number field names
    tbl_number = getattr(tbl, "number", getattr(tbl, "table_number", tbl.pk))

    # ── Header ─────────────────────────────────────────────────────────────────
    story.append(Paragraph(rest_name, title_s))
    if rest_addr:
        story.append(Paragraph(rest_addr, sub_s))
    if rest_phone:
        story.append(Paragraph(f"Tel: {rest_phone}", sub_s))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd")))
    story.append(Spacer(1, 3 * mm))

    # ── Bill meta ──────────────────────────────────────────────────────────────
    meta_rows = [
        [Paragraph(f"<b>Bill #:</b> {order.id}", left_s),
         Paragraph(f"<b>Table:</b> {tbl_number}", right_s)],
        [Paragraph(f"<b>Date:</b> {order.created_at.strftime('%d %b %Y, %I:%M %p')}", left_s),
         Paragraph(f"<b>Status:</b> {order.get_status_display()}", right_s)],
    ]
    # if order.special_notes:
    #     meta_rows.append([
    #         Paragraph(f"<b>Notes:</b> {order.special_notes}", left_s),
    #         Paragraph("", right_s),
    #     ])

    meta_tbl = Table(meta_rows, colWidths=["50%", "50%"])
    meta_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(meta_tbl)
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#eeeeee")))
    story.append(Spacer(1, 3 * mm))

    # ── Items table ────────────────────────────────────────────────────────────
    story.append(Paragraph("ORDER DETAILS", sec_s))
    story.append(Spacer(1, 2 * mm))

    rows = [[
        Paragraph("<b>Item</b>", left_s),
        Paragraph("<b>Qty</b>",  left_s),
        Paragraph("<b>Unit Price</b>", right_s),
        Paragraph("<b>Total</b>",      right_s),
    ]]

    # OrderItem.price = line total (unit * qty) as set by OrderCreateSerializer
    for item in order.items.select_related("menu_item").all():
        line_total = item.price
        unit_price = (line_total / item.quantity) if item.quantity else line_total
        rows.append([
            Paragraph(item.menu_item.name, left_s),
            Paragraph(str(item.quantity),  left_s),
            Paragraph(f"LKR {unit_price:.2f}", right_s),
            Paragraph(f"LKR {line_total:.2f}", right_s),
        ])

    items_tbl = Table(rows, colWidths=["45%", "12%", "22%", "21%"], repeatRows=1)
    items_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ("GRID",          (0, 0), (-1, -1), 0.25, colors.HexColor("#e0e0e0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(items_tbl)
    story.append(Spacer(1, 4 * mm))

    # ── Grand total ────────────────────────────────────────────────────────────
    totals_tbl = Table(
        [[Paragraph("<b>GRAND TOTAL</b>", total_s),
          Paragraph(f"<b>LKR {order.total_amount:.2f}</b>", total_s)]],
        colWidths=["70%", "30%"],
    )
    totals_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEABOVE",     (0, 0), (-1, 0),  1, colors.HexColor("#cccccc")),
    ]))
    story.append(totals_tbl)
    story.append(Spacer(1, 6 * mm))

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#eeeeee")))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Thank you for dining with us!", footer_s))
    story.append(Paragraph("Powered by Scan2Serve", footer_s))

    doc.build(story)
    return buffer.getvalue()


# ── Thermal receipt (80 mm roll) ───────────────────────────────────────────────

# Standard 80 mm paper; change to 58 * mm if your printer uses 58 mm rolls.
_THERMAL_WIDTH  = 80 * mm
_THERMAL_MARGIN = 4 * mm


def _thermal_style(name, **kwargs) -> ParagraphStyle:
    """Base style for thermal receipt — small font, tight leading, no color."""
    defaults = dict(fontName="Helvetica", fontSize=7, leading=9,
                    textColor=colors.black)
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)


def _build_thermal_story(order) -> list:
    """
    Assemble the ReportLab story (flowables) for a thermal receipt.
    Kept separate so the story can be measured before fixing page height.
    """
    # ── Styles ─────────────────────────────────────────────────────────────────
    title_s  = _thermal_style("TH_T",  fontSize=11, fontName="Helvetica-Bold",
                               alignment=TA_CENTER, spaceAfter=1)
    sub_s    = _thermal_style("TH_Su", fontSize=7,  alignment=TA_CENTER, spaceAfter=1)
    meta_l   = _thermal_style("TH_ML", alignment=TA_LEFT)
    meta_r   = _thermal_style("TH_MR", alignment=TA_RIGHT)
    hdr_s    = _thermal_style("TH_H",  fontName="Helvetica-Bold")
    item_l   = _thermal_style("TH_IL", alignment=TA_LEFT)
    item_r   = _thermal_style("TH_IR", alignment=TA_RIGHT)
    total_l  = _thermal_style("TH_TL", fontSize=9, fontName="Helvetica-Bold",
                               alignment=TA_LEFT)
    total_r  = _thermal_style("TH_TR", fontSize=9, fontName="Helvetica-Bold",
                               alignment=TA_RIGHT)
    footer_s = _thermal_style("TH_F",  fontSize=6, alignment=TA_CENTER,
                               textColor=colors.grey)

    # ── Resolve restaurant / table info ────────────────────────────────────────
    tbl        = order.table
    restaurant = getattr(tbl, "restaurant", None)
    rest_name  = getattr(restaurant, "name",    "Scan2Serve") if restaurant else "Scan2Serve"
    rest_addr  = getattr(restaurant, "address", "")           if restaurant else ""
    rest_phone = getattr(restaurant, "phone",   "")           if restaurant else ""
    tbl_number = getattr(tbl, "number", getattr(tbl, "table_number", tbl.pk))

    story = []

    # ── Header ─────────────────────────────────────────────────────────────────
    story.append(Paragraph(rest_name, title_s))
    if rest_addr:
        story.append(Paragraph(rest_addr, sub_s))
    if rest_phone:
        story.append(Paragraph(f"Tel: {rest_phone}", sub_s))
    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))
    story.append(Spacer(1, 1 * mm))

    # ── Bill meta ──────────────────────────────────────────────────────────────
    meta_tbl = Table([
        [Paragraph(f"Bill #: {order.id}", meta_l),
         Paragraph(f"Table: {tbl_number}", meta_r)],
        [Paragraph(order.created_at.strftime("%d %b %Y  %I:%M %p"), meta_l),
         Paragraph(order.get_status_display(), meta_r)],
    ], colWidths=["55%", "45%"])
    meta_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 2 * mm))

    # ── Dashed divider ─────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.black, dash=(2, 2)))
    story.append(Spacer(1, 1 * mm))

    # ── Items ──────────────────────────────────────────────────────────────────
    rows = [[
        Paragraph("<b>Item</b>",  hdr_s),
        Paragraph("<b>Qty</b>",   hdr_s),
        Paragraph("<b>Price</b>", item_r),
        Paragraph("<b>Total</b>", item_r),
    ]]

    for item in order.items.select_related("menu_item").all():
        line_total = item.price
        unit_price = (line_total / item.quantity) if item.quantity else line_total
        rows.append([
            Paragraph(item.menu_item.name,  item_l),
            Paragraph(str(item.quantity),   item_l),
            Paragraph(f"{unit_price:.2f}",  item_r),
            Paragraph(f"{line_total:.2f}",  item_r),
        ])

    items_tbl = Table(rows, colWidths=["44%", "10%", "23%", "23%"], repeatRows=1)
    items_tbl.setStyle(TableStyle([
        ("LINEBELOW",     (0, 0), (-1, 0),  0.5, colors.black),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(items_tbl)
    story.append(Spacer(1, 2 * mm))

    # ── Grand total ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black))
    story.append(Spacer(1, 1 * mm))
    grand_tbl = Table([[
        Paragraph("TOTAL", total_l),
        Paragraph(f"LKR {order.total_amount:.2f}", total_r),
    ]], colWidths=["50%", "50%"])
    grand_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    story.append(grand_tbl)
    story.append(Spacer(1, 2 * mm))

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, dash=(2, 2)))
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph("Thank you for dining with us!", footer_s))
    story.append(Paragraph("Powered by Scan2Serve", footer_s))
    story.append(Spacer(1, 1 * mm))

    return story


def generate_thermal_pdf(order) -> bytes:
    """
    Generate an 80 mm thermal-receipt PDF sized closely to its content.
    Returns raw PDF bytes ready for HttpResponse or direct printer spooling.
    """
    story = _build_thermal_story(order)
    usable_width = _THERMAL_WIDTH - (_THERMAL_MARGIN * 2)

    total_height = 0
    for flowable in story:
        _, h = flowable.wrap(usable_width, 10000 * mm)
        total_height += h

    # Add margins + extra safety space so footer does not jump to page 2
    page_height = total_height + (_THERMAL_MARGIN * 2) + (8 * mm)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=(_THERMAL_WIDTH, page_height),
        rightMargin=_THERMAL_MARGIN,
        leftMargin=_THERMAL_MARGIN,
        topMargin=_THERMAL_MARGIN,
        bottomMargin=_THERMAL_MARGIN,
    )

    doc.build(_build_thermal_story(order))
    return buf.getvalue()