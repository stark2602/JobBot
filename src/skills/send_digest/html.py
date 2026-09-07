"""One HTML digest per run, grouped into Top Matches and Good Fits."""

from __future__ import annotations

from html import escape

from agent.jobs import MatchedJob


def split_tiers(jobs: list[MatchedJob]) -> tuple[list[MatchedJob], list[MatchedJob]]:
    """Top: 90-100. Good: 75-89. Scores 70-74 stay out of the email."""
    top = sorted(
        [j for j in jobs if j.match_score >= 20],
        key=lambda j: j.match_score,
        reverse=True,
    )
    good = sorted(
        [j for j in jobs if 0 <= j.match_score <= 19],
        key=lambda j: j.match_score,
        reverse=True,
    )
    return top, good


def render_html(top: list[MatchedJob], good: list[MatchedJob]) -> str:
    return (
        "<html><body style=\"font-family:Segoe UI,Arial,sans-serif\">"
        "<h1>JobBot digest</h1>"
        + _section("Top Matches (90–100%)", top, full=True)
        + _section("Good Fits (75–89%)", good, full=False)
        + "</body></html>"
    )


def _section(title: str, jobs: list[MatchedJob], *, full: bool) -> str:
    if not jobs:
        return f"<h2>{escape(title)}</h2><p>None this run.</p>"
    rows = []
    for job in jobs:
        p = job.posting
        link = f'<a href="{escape(p.url)}">{escape(p.url)}</a>'
        if full:
            rows.append(
                "<tr>"
                f"<td>{escape(p.company)}</td>"
                f"<td>{escape(p.title)}</td>"
                f"<td>{escape(p.location)}</td>"
                f"<td>{job.match_score}</td>"
                f"<td>{escape(job.reason)}</td>"
                f"<td>{link}</td>"
                "</tr>"
            )
        else:
            rows.append(
                "<tr>"
                f"<td>{escape(p.company)}</td>"
                f"<td>{escape(p.title)}</td>"
                f"<td>{job.match_score}</td>"
                f"<td>{link}</td>"
                "</tr>"
            )
    if full:
        head = (
            "<tr><th>Company</th><th>Title</th><th>Location</th>"
            "<th>Score</th><th>Why</th><th>Apply</th></tr>"
        )
    else:
        head = "<tr><th>Company</th><th>Title</th><th>Score</th><th>Apply</th></tr>"
    return (
        f"<h2>{escape(title)}</h2>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        f"{head}{''.join(rows)}</table>"
    )
