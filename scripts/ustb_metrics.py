"""Join dated USTB labels to the pinned Ethereum rounds and compute audit metrics."""
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

DAY = timedelta(days=1)
ET = ZoneInfo("America/New_York")
# NYSE full closures in the observed period. Veterans Day is a U.S. federal
# holiday and an NYSE session, so it is tagged separately in the daily rows.
NYSE_CLOSED = frozenset(map(date.fromisoformat, """
2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26
2025-06-19 2025-07-04 2025-09-01 2025-11-27 2025-12-25
2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19
2026-07-03 2026-09-07 2026-11-26
""".split()))
VETERANS_DAY = {date(year, 11, 11) for year in (2024, 2025, 2026)}
FEDERAL_ONLY = VETERANS_DAY | {date(2024, 10, 14), date(2025, 10, 13), date(2026, 10, 12)}
EXCHANGE_ONLY = {date(2025, 1, 9), date(2025, 4, 18), date(2026, 4, 3)}
FEDERAL_HOLIDAYS = (NYSE_CLOSED - EXCHANGE_ONLY) | FEDERAL_ONLY


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc)


def midnight(day):
    return datetime.combine(day, time.min, timezone.utc)


def days(start, end):
    return (start + i * DAY for i in range((end - start).days + 1))


def nyse_session(day):
    return day.weekday() < 5 and day not in NYSE_CLOSED


def next_nyse_session(day):
    return next(d for d in days(day + DAY, day + 8*DAY) if nyse_session(d))


def basis_points(feed, issuer):
    return (Decimal(feed) - issuer) * 10_000 / issuer


def describe(numbers):
    values = sorted(numbers)
    if not values:
        return {"n": 0}

    def quantile(fraction):
        index = Decimal(len(values)-1) * Decimal(fraction)
        low = int(index)
        return values[low] + (values[min(low+1, len(values)-1)] - values[low]) * (index - low)

    return dict(n=len(values), min=values[0], p50=quantile("0.5"), p90=quantile("0.9"), max=values[-1])


def analyze(rounds, labels, first, last, heartbeat, *, observed_through):
    # Record every start of a run of equal values. A later reappearance is a
    # separate candidate, so a repeated value cannot silently imply one date.
    occurrences = defaultdict(list)
    prior_day, prior = None, None
    for day, value in sorted(labels.items()):
        if value != prior or prior_day != day - DAY:
            occurrences[value].append(day)
        prior_day, prior = day, value

    starts = sorted(day for spell in occurrences.values() for day in spell)
    next_changes = {day: successor for day, successor in zip(starts, starts[1:])
                    if all(d in labels for d in days(day, successor))}
    joined = []
    previous = None
    for row in rounds:
        recorded = utc(row["updated_at"])
        updated = utc(row.get("visible_at", row["updated_at"]))
        if updated.timestamp() > observed_through:
            break
        day = updated.date()
        et_day = updated.astimezone(ET).date()
        value = row["answer"]
        candidate_days = [label for label in occurrences[value] if label <= min(day, last)]
        # Ambiguous repeat spell: retain candidates and exclude from timing.
        label = candidate_days[0] if len(candidate_days) == 1 else None
        previous_value = labels.get(day - DAY) if day <= last else None
        next_session = next_nyse_session(label) if label else None
        next_change = next_changes.get(label)
        changed = previous is not None and previous["answer"] != value
        gap = (row["updated_at"] - previous["updated_at"]
               if previous and row["id"] >> 64 == previous["id"] >> 64 else None)
        joined.append(dict(
            **row, updated_utc=recorded.isoformat(), visible_utc=updated.isoformat(),
            visible_et=updated.astimezone(ET).isoformat(),
            window_day=day, posting_date_et=et_day, candidate_label_starts=candidate_days,
            label=label, changed=changed,
            matched_value=any(d <= last for d in occurrences[value]), gap_seconds=gap,
            label_hours=Decimal(int((updated-midnight(label)).total_seconds())) / 3600 if label else None,
            nyse_sessions=sum(map(nyse_session, days(label + DAY, et_day))) if label else None,
            next_nyse_session_date=next_session,
            posted_on_next_nyse_session_date=et_day == next_session if next_session else None,
            next_issuer_value_change_date=next_change,
            posted_on_next_issuer_value_change_date=et_day == next_change if next_change else None,
            days_from_next_issuer_value_change=(et_day - next_change).days if next_change else None,
            weekday_steps=sum(d.weekday() < 5 for d in days(label + DAY, et_day)) if label else None,
            previous_utc_label=day-DAY, previous_utc_label_answer=previous_value,
            previous_utc_label_gap_bp=basis_points(value, previous_value) if previous_value else None,
        ))
        previous = row

    timeline = [row.get("visible_at", row["updated_at"]) for row in joined]
    daily = []
    for day in days(first, last):
        index = bisect_right(timeline, int(midnight(day + DAY).timestamp()) - 1) - 1
        if index < 0 or day not in labels:
            continue
        row = joined[index]
        daily.append(dict(day=day, round_id=row["id"], feed_updated_utc=row["updated_utc"],
                          feed_visible_utc=row["visible_utc"],
                          feed_label=row["label"], feed=row["answer"], issuer=labels[day],
                          kind=("weekend" if day.weekday() >= 5 else
                                "NYSE closure" if day in NYSE_CLOSED else
                                "Veterans Day" if day in VETERANS_DAY else "NYSE session"),
                          federal_holiday=day in FEDERAL_HOLIDAYS,
                          gap_bp=basis_points(row["answer"], labels[day])))
    cohort = [r for r in joined if first <= r["window_day"]]
    new = [r for r in cohort if r["changed"] and r["label"] is not None]
    first_post = {}
    for row in joined:
        if row["label"] is not None:
            first_post.setdefault(row["label"], row)
    covered = {row["answer"] for row in joined}
    through_et = utc(observed_through).astimezone(ET).date()
    delivery = []
    for day in starts:
        if not first <= day <= last:
            continue
        row = first_post.get(day)
        successor = next_changes.get(day)
        if row and row["changed"] and successor:
            offset = row["days_from_next_issuer_value_change"]
            status = "next_change" if offset == 0 else "after" if offset > 0 else "before"
        elif row is None and successor and successor < through_et and labels[day] not in covered:
            status = "unseen"
        else:
            status = "unknown"
        delivery.append(dict(label=day, answer=labels[day], next_issuer_value_change_date=successor,
                             first_post_et=row["visible_et"] if row else None, status=status))
    trading_month_ends = [
        d for d in days(first, last) if nyse_session(d)
        and d.month != next_nyse_session(d).month
    ]
    month_ends = [dict(label=d, label_answer=labels.get(d), first_post=first_post.get(d))
                  for d in trading_month_ends if d in labels]
    retained_labels = {value for day, value in labels.items() if first <= day <= last}
    missing = retained_labels - covered
    # A gap belongs to the cohort only if both endpoint updates are in it.
    intervals = [r for r in cohort[1:] if r["gap_seconds"] is not None]
    largest_interval = max(intervals, key=lambda r: r["gap_seconds"], default=None)
    previous_day_gaps = [abs(r["previous_utc_label_gap_bp"]) for r in cohort
                         if r["previous_utc_label_gap_bp"] is not None]
    groups = {kind: [r for r in daily if r["kind"] == kind] for kind in
              ("weekend", "NYSE closure", "Veterans Day", "NYSE session")}
    summary = dict(
        first=first, last=last, observed_through_utc=utc(observed_through).isoformat(),
        daily_dates=len(daily),
        rounds=len(cohort), matched_rounds=sum(r["matched_value"] for r in cohort),
        unmatched_ids=[r["id"] for r in cohort if not r["matched_value"]],
        ambiguous_rounds=sum(len(r["candidate_label_starts"]) > 1 for r in cohort),
        exact_rounds_without_prior_label=sum(r["matched_value"] and not r["candidate_label_starts"] for r in cohort),
        labels=sum(first <= day <= last for day in labels), distinct_label_values=len(retained_labels),
        covered_ever=len(retained_labels & covered), uncovered_values=sorted(missing),
        uncovered_labels=[dict(label=d, answer=labels[d]) for d in days(first, last)
                          if d in labels and labels[d] in missing],
        distinct_feed_values=len({r["answer"] for r in cohort}),
        changed_rounds=sum(r["changed"] for r in cohort), changed_matched=len(new),
        changed_weekend_et=sum(r["posting_date_et"].weekday() >= 5
                               for r in cohort if r["changed"]),
        changed_posted_on_nyse_closure_et=sum(r["posting_date_et"] in NYSE_CLOSED
                                            for r in cohort if r["changed"]),
        friday_changes=sum(r["label"].weekday() == 4 for r in new),
        friday_to_monday=sum(r["label"].weekday() == 4 and
                             r["posting_date_et"] == r["label"] + 3*DAY for r in new),
        unchanged_rounds=sum(not r["changed"] and r["gap_seconds"] is not None for r in cohort),
        weekend_rounds_et=sum(r["posting_date_et"].weekday() >= 5 for r in cohort),
        weekend_interval_seconds=describe(r["gap_seconds"] for r in intervals
            if r["posting_date_et"].weekday() >= 5),
        weekday_steps=dict(sorted(Counter(r["weekday_steps"] for r in new).items())),
        nyse_sessions=dict(sorted(Counter(r["nyse_sessions"] for r in new).items())),
        posted_on_next_nyse_session_date=sum(r["posted_on_next_nyse_session_date"] for r in new),
        posted_on_next_issuer_value_change_date=sum(
            r["posted_on_next_issuer_value_change_date"] is True for r in new),
        next_issuer_value_change_unknown=sum(r["next_issuer_value_change_date"] is None for r in new),
        delivery_statuses=dict(sorted(Counter(r["status"] for r in delivery).items())),
        changed_label_hours=describe(r["label_hours"] for r in new),
        all_joined_label_hours=describe(r["label_hours"] for r in cohort if r["label_hours"] is not None),
        changed_et_minutes_after_midnight=describe(
            r.hour * 60 + r.minute + Decimal(r.second)/60 for r in
            (datetime.fromisoformat(row["visible_et"]) for row in new)),
        interval_seconds=describe(r["gap_seconds"] for r in intervals),
        max_interval=largest_interval,
        max_interval_ending_utc=[r["updated_utc"] for r in intervals
                                 if r["gap_seconds"] == largest_interval["gap_seconds"]],
        interval_over_heartbeat=sum(r["gap_seconds"] > heartbeat for r in intervals),
        unchanged_interval_seconds=describe(r["gap_seconds"] for r in intervals if not r["changed"]),
        abs_previous_utc_label_gap_bp=describe(previous_day_gaps),
        daily_close_by_kind={kind: dict(n=len(group),
            max_abs=max(group, key=lambda r: abs(r["gap_bp"]), default=None),
            max_behind=min(group, key=lambda r: r["gap_bp"], default=None),
            abs_gap_bp=describe(abs(r["gap_bp"]) for r in group),
        ) for kind, group in groups.items()},
        max_abs_federal_holiday_close=max((r for r in daily if r["federal_holiday"]),
                                          key=lambda r: abs(r["gap_bp"]), default=None),
        max_abs_daily_close=max(daily, key=lambda r: abs(r["gap_bp"]), default=None),
        max_behind_daily_close=min(daily, key=lambda r: r["gap_bp"], default=None),
        month_end_sessions=len(month_ends),
        month_end_exact_new_label_posts=sum(r["first_post"] is not None for r in month_ends),
        month_end_one_session_elapsed=sum(r["first_post"] is not None
                                          and r["first_post"]["nyse_sessions"] == 1 for r in month_ends),
        month_end_next_session_date=sum(r["first_post"] is not None
                                        and r["first_post"]["posted_on_next_nyse_session_date"]
                                        for r in month_ends),
    )
    return dict(summary=summary, rounds=cohort, daily=daily, month_ends=month_ends, delivery=delivery)
