"""Render the USTB daily gap figure from the verified replay."""
import argparse
import html
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from issuer_history import check

INK = "#142E28"
PAPER = "#F4F5EF"
HIGHLIGHT = "#DFFF5E"
WIDTH, HEIGHT = 680, 416
LEFT, RIGHT, TOP, BOTTOM = 58, 643, 120, 304


def render(report):
    rows = report["full"]["daily"]
    days = [date.fromisoformat(r["day"]) for r in rows]
    values = [Decimal(r["gap_bp"]) for r in rows]
    check(len(days) >= 2 and all((b-a).days == 1 for a, b in zip(days, days[1:])),
          "chart requires consecutive daily observations")
    check(all(v.is_finite() and -6 <= v <= 0 for v in values), "chart values outside the checked axis")
    worst_index = min(range(len(values)), key=values.__getitem__)
    worst_day, worst = days[worst_index], values[worst_index]
    check(rows[worst_index] == report["full"]["summary"]["max_behind_daily_close"],
          "chart extreme differs from replay summary")

    def x(day):
        return LEFT + (RIGHT-LEFT) * (day-days[0]).days / (days[-1]-days[0]).days

    def y(value):
        return TOP - (BOTTOM-TOP) * float(value) / 6

    alt = (f"Scatterplot of {len(rows)} daily observations from {days[0]} to {days[-1]}. "
           f"At 23:59:59 UTC, the active Chainlink USTB NAV per share minus the same-date "
           f"Superstate label, divided by that issuer label, reached {worst:.2f} basis points on {worst_day}. "
           "The issuer label has no publication timestamp.")
    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        'role="img" aria-labelledby="title description">',
        '<title id="title">USTB trailed Superstate’s NAV</title>',
        f'<desc id="description">{html.escape(alt)}</desc>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{PAPER}"/>',
        f'<g fill="{INK}" font-family="IBM Plex Sans, DejaVu Sans, sans-serif">',
        '<text x="31" y="57" font-weight="800" font-size="32">USTB trailed Superstate’s NAV</text>',
        '<text x="32" y="91" font-size="22">UTC-close gap (bp)</text>',
    ]
    for value in (0, -2, -4, -6):
        body.append(f'<path d="M {LEFT} {y(value):.2f} H {RIGHT}" stroke="{INK}" '
                    f'opacity="{0.75 if value == 0 else 0.22}"/>')
        body.append(f'<text x="{LEFT-13}" y="{y(value)+6:.2f}" font-size="20" text-anchor="end">'
                    f'{str(value).replace("-", "−")}</text>')
    body.append(f'<g id="daily-gaps" fill="{INK}" fill-opacity="0.64">')
    for day, value in zip(days, values):
        body.append(f'<circle cx="{x(day):.2f}" cy="{y(value):.2f}" r="2"/>')
    body.append('</g>')
    body.append(f'<circle id="deepest-gap" cx="{x(worst_day):.2f}" cy="{y(worst):.2f}" '
                f'r="5" fill="{HIGHLIGHT}" stroke="{INK}" stroke-width="2"/>')
    body.append(f'<text x="{x(worst_day)+15:.2f}" y="{y(worst)+9:.2f}" font-size="21" '
                f'font-weight="700">{str(round(worst, 2)).replace("-", "−")} · {worst_day}</text>')
    ticks = [(days[0], "Jun’24", "start"), (date(2025, 1, 1), "Jan’25", "middle"),
             (date(2026, 1, 1), "Jan’26", "middle"), (days[-1], "Nov’26", "end")]
    for day, label, anchor in ticks:
        body.append(f'<text x="{x(day):.2f}" y="344" font-size="22" text-anchor="{anchor}">{label}</text>')
    body.append('<text x="31" y="380" font-size="22">Chainlink/Superstate</text>')
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
    except (OSError, ValueError, KeyError, InvalidOperation) as exc:
        parser.exit(1, f"chart: {exc}\n")


if __name__ == "__main__":
    main()
