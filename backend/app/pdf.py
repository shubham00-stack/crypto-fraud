"""PDF investigation report export."""
from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import CaseRecord


def build_report_pdf(case: CaseRecord) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title=f"Investigation report {case.id}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
    body = styles["BodyText"]
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8, textColor=colors.grey)

    story = [
        Paragraph("Crypto Fraud Attribution — Investigation Report", title_style),
        Paragraph(f"Case {case.id} &nbsp;&middot;&nbsp; {case.input.title}", body),
        Paragraph(
            "DEMO ANALYSIS — generated from the local demo blockchain provider using synthetic, "
            "deterministic data. This report is an investigative aid; it is not proof of criminal activity.",
            small,
        ),
        Spacer(1, 10),
    ]

    story.append(Paragraph("Case summary", h2))
    summary_rows = [
        ["Victim reference", case.input.victim_reference],
        ["Blockchain", case.input.blockchain],
        ["Reported wallet", case.input.wallet_address],
        ["Token", case.input.token],
        ["Reported amount", f"{case.input.reported_amount:,.2f} {case.input.token}"],
        ["Trace depth", f"{case.max_hop_depth} hops"],
        ["Total value traced", f"{case.traced_amount:,.2f} {case.input.token}"],
        ["Transactions collected", str(len(case.transactions))],
    ]
    summary_table = Table(summary_rows, colWidths=[55 * mm, 110 * mm])
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4a5a68")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe4e8")),
            ]
        )
    )
    story.append(summary_table)

    story.append(Paragraph("Risk assessment", h2))
    story.append(
        Paragraph(
            f"Score: <b>{case.risk.score}/100</b> &nbsp;&middot;&nbsp; "
            f"Priority: <b>{case.risk.level.upper()}</b> (risk indicators, not a legal conclusion)",
            body,
        )
    )
    if case.risk.factors:
        factor_rows = [["Indicator", "Points", "Evidence"]]
        for factor in case.risk.factors:
            factor_rows.append([factor.name, f"+{factor.points}", factor.evidence])
        factor_table = Table(factor_rows, colWidths=[45 * mm, 18 * mm, 102 * mm])
        factor_table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f5")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe4e8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(factor_table)
    else:
        story.append(Paragraph("No risk indicators were triggered for this trace.", body))

    story.append(Paragraph("Entity evidence", h2))
    if case.entities:
        for entity in case.entities:
            story.append(
                Paragraph(
                    f"<b>{entity.entity_name}</b> ({entity.entity_type}) — {entity.address}<br/>"
                    f"Confidence: {entity.confidence}% &nbsp;&middot;&nbsp; Source: {entity.source}",
                    body,
                )
            )
    else:
        story.append(Paragraph("No known entity association was established in this trace.", body))

    story.append(Paragraph("Transaction timeline", h2))
    tx_rows = [["Time (UTC)", "From", "To", "Amount"]]
    for tx in case.transactions:
        tx_rows.append(
            [
                datetime.fromisoformat(tx.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                f"{tx.from_address[:10]}...",
                f"{tx.to_address[:10]}...",
                f"{tx.amount:,.2f} {tx.asset}",
            ]
        )
    tx_table = Table(tx_rows, colWidths=[38 * mm, 45 * mm, 45 * mm, 37 * mm], repeatRows=1)
    tx_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f5")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe4e8")),
            ]
        )
    )
    story.append(tx_table)

    if case.alerts:
        story.append(Paragraph("Monitoring alerts", h2))
        for alert in case.alerts:
            story.append(
                Paragraph(
                    f"<b>{alert.severity}-RISK</b> — {alert.amount:,.2f} {alert.asset}: {alert.reason}",
                    body,
                )
            )

    doc.build(story)
    return buffer.getvalue()
