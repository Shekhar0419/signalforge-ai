from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.schemas import DatasetProfile


NAVY = colors.HexColor("#0F172A")
BLUE = colors.HexColor("#1D4ED8")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
SLATE = colors.HexColor("#475569")
LIGHT_SLATE = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#CBD5E1")
GREEN = colors.HexColor("#047857")
AMBER = colors.HexColor("#B45309")
RED = colors.HexColor("#B91C1C")


def _safe_text(value: Any) -> str:
    if value is None:
        return "-"

    return str(value).replace("&", "&amp;").replace(
        "<",
        "&lt;",
    ).replace(
        ">",
        "&gt;",
    )


def _format_percentage(value: float) -> str:
    percentage = value * 100 if value <= 1 else value
    return f"{percentage:.1f}%"


def _normalize_score(score: float) -> float:
    normalized = score * 100 if score <= 1 else score
    return max(0.0, min(normalized, 100.0))


def _score_color(score: float):
    normalized = _normalize_score(score)

    if normalized >= 90:
        return GREEN

    if normalized >= 75:
        return AMBER

    return RED


def _failed_business_rules(
    profile: DatasetProfile,
) -> list[dict[str, Any]]:
    failed: list[dict[str, Any]] = []

    for rule in profile.business_rules:
        status = str(
            rule.get("status", "")
        ).lower()

        violations = rule.get(
            "violation_count",
            rule.get(
                "violations",
                rule.get("failed_count", 0),
            ),
        )

        try:
            count = int(violations or 0)
        except (TypeError, ValueError):
            count = 0

        if (
            rule.get("passed") is False
            or status in {"failed", "fail"}
            or count > 0
        ):
            failed.append(
                {
                    **rule,
                    "normalized_violations": count,
                }
            )

    return failed


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=SLATE,
            alignment=TA_CENTER,
            spaceAfter=16,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
            textColor=SLATE,
            alignment=TA_LEFT,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontSize=10,
            leading=15,
            textColor=NAVY,
            alignment=TA_LEFT,
        )
    )

    styles.add(
        ParagraphStyle(
            name="MetricLabel",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=SLATE,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="MetricValue",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=NAVY,
            alignment=TA_CENTER,
        )
    )

    return styles


def _build_metric_table(
    profile: DatasetProfile,
    styles,
) -> Table:
    anomaly_count = len(profile.ml_anomalies)

    metrics = [
        (
            "Reliability",
            f"{_normalize_score(profile.reliability_score):.1f}%",
        ),
        (
            "Rows",
            f"{profile.row_count:,}",
        ),
        (
            "Columns",
            str(profile.column_count),
        ),
        (
            "Duplicates",
            f"{profile.duplicate_rows:,}",
        ),
        (
            "Quality issues",
            str(len(profile.issues)),
        ),
        (
            "ML anomalies",
            str(anomaly_count),
        ),
    ]

    data = [
        [
            Paragraph(
                _safe_text(value),
                styles["MetricValue"],
            )
            for _, value in metrics
        ],
        [
            Paragraph(
                _safe_text(label),
                styles["MetricLabel"],
            )
            for label, _ in metrics
        ],
    ]

    table = Table(
        data,
        colWidths=[1.05 * inch] * len(metrics),
        rowHeights=[0.42 * inch, 0.26 * inch],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BLUE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    BORDER,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    return table


def _build_issue_table(
    profile: DatasetProfile,
    styles,
) -> Table | Paragraph:
    if not profile.issues:
        return Paragraph(
            "No profiler quality issues were detected.",
            styles["Body"],
        )

    rows = [
        [
            Paragraph("<b>Severity</b>", styles["BodySmall"]),
            Paragraph("<b>Code</b>", styles["BodySmall"]),
            Paragraph("<b>Column</b>", styles["BodySmall"]),
            Paragraph("<b>Message</b>", styles["BodySmall"]),
        ]
    ]

    for issue in profile.issues[:25]:
        rows.append(
            [
                Paragraph(
                    _safe_text(issue.severity),
                    styles["BodySmall"],
                ),
                Paragraph(
                    _safe_text(issue.code),
                    styles["BodySmall"],
                ),
                Paragraph(
                    _safe_text(issue.column),
                    styles["BodySmall"],
                ),
                Paragraph(
                    _safe_text(issue.message),
                    styles["BodySmall"],
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            0.65 * inch,
            1.15 * inch,
            1.2 * inch,
            3.45 * inch,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    BLUE,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        LIGHT_SLATE,
                    ],
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


def _build_rules_table(
    profile: DatasetProfile,
    styles,
) -> Table | Paragraph:
    failed_rules = _failed_business_rules(
        profile
    )

    if not failed_rules:
        return Paragraph(
            "All configured business-rule checks passed.",
            styles["Body"],
        )

    rows = [
        [
            Paragraph("<b>Column</b>", styles["BodySmall"]),
            Paragraph("<b>Rule</b>", styles["BodySmall"]),
            Paragraph("<b>Violations</b>", styles["BodySmall"]),
        ]
    ]

    for rule in failed_rules[:25]:
        rule_name = (
            rule.get("rule")
            or rule.get("rule_name")
            or rule.get("description")
            or "Validation rule"
        )

        rows.append(
            [
                Paragraph(
                    _safe_text(rule.get("column")),
                    styles["BodySmall"],
                ),
                Paragraph(
                    _safe_text(rule_name),
                    styles["BodySmall"],
                ),
                Paragraph(
                    _safe_text(
                        rule.get(
                            "normalized_violations",
                            0,
                        )
                    ),
                    styles["BodySmall"],
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            1.7 * inch,
            3.9 * inch,
            0.9 * inch,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    BLUE,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        LIGHT_SLATE,
                    ],
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


def _build_recommendations(
    profile: DatasetProfile,
    styles,
) -> list:
    if not profile.recommendations:
        return [
            Paragraph(
                "No recommendations were generated.",
                styles["Body"],
            )
        ]

    blocks = []

    for index, recommendation in enumerate(
        profile.recommendations[:12],
        start=1,
    ):
        blocks.append(
            Paragraph(
                f"<b>{index}.</b> {_safe_text(recommendation)}",
                styles["Body"],
            )
        )
        blocks.append(Spacer(1, 0.08 * inch))

    return blocks


def _build_column_table(
    profile: DatasetProfile,
    styles,
) -> Table | Paragraph:
    if not profile.columns:
        return Paragraph(
            "No column profiles are available.",
            styles["Body"],
        )

    rows = [
        [
            Paragraph("<b>Column</b>", styles["BodySmall"]),
            Paragraph("<b>Type</b>", styles["BodySmall"]),
            Paragraph("<b>Missing</b>", styles["BodySmall"]),
            Paragraph("<b>Unique</b>", styles["BodySmall"]),
            Paragraph("<b>Outliers</b>", styles["BodySmall"]),
        ]
    ]

    for column in profile.columns[:40]:
        rows.append(
            [
                Paragraph(
                    _safe_text(column.name),
                    styles["BodySmall"],
                ),
                Paragraph(
                    _safe_text(column.inferred_type),
                    styles["BodySmall"],
                ),
                Paragraph(
                    (
                        f"{column.missing_count:,} "
                        f"({_format_percentage(column.missing_ratio)})"
                    ),
                    styles["BodySmall"],
                ),
                Paragraph(
                    (
                        f"{column.unique_count:,} "
                        f"({_format_percentage(column.unique_ratio)})"
                    ),
                    styles["BodySmall"],
                ),
                Paragraph(
                    (
                        f"{column.outlier_count:,} "
                        f"({_format_percentage(column.outlier_ratio)})"
                    ),
                    styles["BodySmall"],
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            1.8 * inch,
            1.05 * inch,
            1.3 * inch,
            1.3 * inch,
            1.2 * inch,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    BLUE,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        LIGHT_SLATE,
                    ],
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


def build_dataset_pdf_report(
    profile: DatasetProfile,
    dataset_id: str,
    created_at: datetime,
) -> bytes:
    """
    Generate a branded executive PDF report for a saved dataset profile.
    """
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.55 * inch,
        title=f"SignalForge AI Report - {profile.filename}",
        author="SignalForge AI",
    )

    styles = _build_styles()
    story = []

    story.append(
        Paragraph(
            "SignalForge AI",
            styles["ReportTitle"],
        )
    )

    story.append(
        Paragraph(
            "Executive Data Reliability Report",
            styles["ReportSubtitle"],
        )
    )

    metadata = (
        f"<b>Dataset:</b> {_safe_text(profile.filename)}"
        f"<br/><b>Dataset ID:</b> {_safe_text(dataset_id)}"
        f"<br/><b>Analyzed:</b> "
        f"{created_at.strftime('%B %d, %Y at %I:%M %p')}"
    )

    story.append(
        Paragraph(
            metadata,
            styles["Body"],
        )
    )

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        _build_metric_table(
            profile,
            styles,
        )
    )

    story.append(Spacer(1, 0.2 * inch))

    score = _normalize_score(
        profile.reliability_score
    )

    score_summary = (
        f"<b>Reliability assessment:</b> "
        f"<font color='{_score_color(score).hexval()}'>"
        f"{score:.1f}%</font>. "
        "Review the detailed findings below before using this "
        "dataset for production analytics or machine learning."
    )

    story.append(
        Paragraph(
            score_summary,
            styles["Body"],
        )
    )

    story.append(
        Paragraph(
            "Executive Summary",
            styles["SectionHeading"],
        )
    )

    story.append(
        Paragraph(
            (
                f"The dataset contains {profile.row_count:,} rows "
                f"and {profile.column_count} columns. "
                f"The profiler identified {len(profile.issues)} "
                f"quality issue(s), {profile.duplicate_rows:,} "
                f"duplicate row(s), and {len(profile.ml_anomalies)} "
                "potential anomalous record(s)."
            ),
            styles["Body"],
        )
    )

    story.append(
        Paragraph(
            "Quality Issues",
            styles["SectionHeading"],
        )
    )

    story.append(
        _build_issue_table(
            profile,
            styles,
        )
    )

    story.append(
        Paragraph(
            "Failed Business Rules",
            styles["SectionHeading"],
        )
    )

    story.append(
        _build_rules_table(
            profile,
            styles,
        )
    )

    story.append(
        Paragraph(
            "Priority Recommendations",
            styles["SectionHeading"],
        )
    )

    story.extend(
        _build_recommendations(
            profile,
            styles,
        )
    )

    story.append(PageBreak())

    story.append(
        Paragraph(
            "Column Profile Overview",
            styles["SectionHeading"],
        )
    )

    story.append(
        _build_column_table(
            profile,
            styles,
        )
    )

    document.build(story)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes