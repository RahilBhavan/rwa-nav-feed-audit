"""Render the USTB issuer-label delivery chart from the verified replay."""
import argparse
import html
import json
from collections import Counter
from datetime import date
from pathlib import Path

from issuer_history import check

INK = "#142E28"
PAPER = "#F4F5EF"
HIGHLIGHT = "#DFFF5E"
WIDTH, HEIGHT = 680, 386
LEFT, RIGHT = 350, 640
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def render(report):
    rows = report["full"]["delivery"]
    summary = report["full"]["summary"]
    start, end = (date.fromisoformat(summary[key]) for key in ("first", "last"))
    labels = [date.fromisoformat(row["label"]) for row in rows]
    counts = Counter(row["status"] for row in rows)
    check(start < end and labels == sorted(set(labels)) and
          all(start <= label <= end for label in labels), "invalid delivery chart dates")
    check(counts == summary["delivery_statuses"], "chart counts differ from replay summary")
    check(set(counts) <= {"next_change", "after", "unseen", "unknown"}
          and all(row["status"] != "after" or
                  (date.fromisoformat(row["first_post_et"][:10]) -
                   date.fromisoformat(row["next_issuer_value_change_date"])).days == 1 for row in rows)
          and all(row["status"] != "unknown" or row.get("next_issuer_value_change_date") is None
                  for row in rows),
          "delivery status differs from the displayed categories")

    def x(day):
        return LEFT + (RIGHT - LEFT) * (day - start).days / (end - start).days

    claim = f"{counts['next_change']} of {len(rows)}"
    title = f"{claim} USTB NAVs reached Chainlink the next NAV day"
    alt = (f"Ethereum delivery history for {len(rows)} Superstate issuer value changes labelled {start} "
           f"through {end}. The first active post for {counts['next_change']} values fell on the next issuer "
           f"value-change date and {counts['after']} fell one day after. {counts['unseen']} values were "
           f"unseen by the pinned block. Timing for {counts['unknown']} is unknown because the pinned "
           "issuer history ends before the next value change. Issuer value-change dates are a proxy for "
           "valuation dates. Publication times are unknown. Each mark uses the original label date.")
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        'role="img" aria-labelledby="title description">',
        f'<title id="title">{title}</title>',
        f'<desc id="description">{html.escape(alt)}</desc>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{PAPER}"/>',
        f'<g fill="{INK}" font-family="IBM Plex Sans, DejaVu Sans, sans-serif">',
        f'<rect x="26" y="20" width="{12 * len(claim) + 80}" height="42" fill="{HIGHLIGHT}"/>',
        f'<text x="34" y="54" font-family="Archivo, DejaVu Sans, sans-serif" '
        f'font-weight="850" font-size="38">{claim} USTB NAVs reached</text>',
        f'<text x="34" y="98" font-family="Archivo, DejaVu Sans, sans-serif" '
        'font-weight="850" font-size="38">Chainlink the next NAV day</text>',
    ]
    bands = [
        ("next_change", None, 160),
        ("after", "Day after", 217),
        ("unseen", "Unseen", 266),
        ("unknown", "Pending", 315),
    ]
    for status, label_text, y in bands:
        body.append(f'<path d="M {LEFT} {y} H {RIGHT}" stroke="{INK}" opacity="0.22"/>')
        if label_text:
            body.append(f'<text x="79" y="{y + 8}" font-size="30" text-anchor="end" '
                        f'font-weight="600">{counts[status]}</text>')
            body.append(f'<text x="96" y="{y + 8}" font-weight="600" font-size="28">{label_text}</text>')
        body.append(f'<g id="{status}">')
        for row, label in zip(rows, labels):
            if row["status"] != status:
                continue
            pos = x(label)
            if status == "next_change":
                row_y = y + ((label - start).days % 7 - 3) * 2.8
                body.append(f'<circle cx="{pos:.2f}" cy="{row_y:.1f}" r="1.35"/>')
            elif status == "after":
                body.append(f'<circle cx="{pos:.2f}" cy="{y}" r="4.3"/>')
            elif status == "unseen":
                body.append(f'<rect x="{pos-0.8:.2f}" y="{y-5}" width="1.6" height="10"/>')
            else:
                body.append(f'<circle cx="{pos:.2f}" cy="{y}" r="4" fill="{PAPER}" '
                            f'stroke="{INK}" stroke-width="2"/>')
        body.append('</g>')
    for day, anchor in ((start, "start"), (end, "end")):
        label = f"{MONTHS[day.month - 1]}’{day.year % 100:02d}"
        body.append(f'<text x="{x(day):.2f}" y="365" font-size="28" text-anchor="{anchor}">{label}</text>')
    return "\n".join(body + ["</g>", "</svg>", ""])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--check", action="store_true", help="compare with the committed figure")
    args = parser.parse_args()
    try:
        rendered = render(json.loads(args.report.read_bytes())).encode()
        if args.check:
            check(rendered == args.output.read_bytes(), "chart differs from the verified replay")
        else:
            args.output.write_bytes(rendered)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"chart: {exc}\n")


if __name__ == "__main__":
    main()
