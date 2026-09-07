"""Public ATS JSON adapters. One board failure must not stop the others."""

from __future__ import annotations

import logging
from typing import Any

from agent.errors import SkillUpstreamError
from agent.jobs import JobPosting, parse_datetime, strip_html, within_max_age
from agent.profile import JobProfile, WorkdayBoard
from tools.http import HttpTransport, HttpxHttp

logger = logging.getLogger("jobbot.ingest")


def ingest_all(
    profile: JobProfile,
    *,
    http: HttpTransport | None = None,
    timeout_s: float = 20.0,
) -> tuple[list[JobPosting], list[str]]:
    """Fetch Greenhouse, Lever, and Workday boards listed in the profile.

    Returns:
        (postings, source_errors) — errors are logged strings; parsing continues.
    """
    client = http or HttpxHttp()
    jobs: list[JobPosting] = []
    errors: list[str] = []
    max_age = profile.search.max_age_hours

    for token in profile.sources.greenhouse:
        try:
            jobs.extend(fetch_greenhouse(token, http=client, max_age_hours=max_age, timeout_s=timeout_s))
        except SkillUpstreamError as exc:
            msg = f"greenhouse:{token}: {exc}"
            logger.error(msg)
            errors.append(msg)
        except Exception as exc:
            msg = f"greenhouse:{token}: {exc}"
            logger.error(msg)
            errors.append(msg)

    for company in profile.sources.lever:
        try:
            jobs.extend(fetch_lever(company, http=client, max_age_hours=max_age, timeout_s=timeout_s))
        except SkillUpstreamError as exc:
            msg = f"lever:{company}: {exc}"
            logger.error(msg)
            errors.append(msg)
        except Exception as exc:
            msg = f"lever:{company}: {exc}"
            logger.error(msg)
            errors.append(msg)

    for board in profile.sources.workday:
        try:
            jobs.extend(fetch_workday(board, http=client, max_age_hours=max_age, timeout_s=timeout_s))
        except SkillUpstreamError as exc:
            msg = f"workday:{board.company}: {exc}"
            logger.error(msg)
            errors.append(msg)
        except Exception as exc:
            msg = f"workday:{board.company}: {exc}"
            logger.error(msg)
            errors.append(msg)

    # Fetch generic web sources if any
    if profile.sources.generic_web:
        try:
            jobs.extend(fetch_generic_web(profile.sources.generic_web, http=client, max_age_hours=max_age, timeout_s=timeout_s))
        except Exception as exc:
            msg = f"generic_web: {exc}"
            logger.error(msg)
            errors.append(msg)

    return jobs, errors


def fetch_greenhouse(
    board_token: str,
    *,
    http: HttpTransport,
    max_age_hours: int,
    timeout_s: float,
) -> list[JobPosting]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    payload = http.get_json(url, timeout_s=timeout_s)
    jobs_raw = _as_list(payload, "jobs")
    out: list[JobPosting] = []
    for item in jobs_raw:
        if not isinstance(item, dict):
            continue
        posted = parse_datetime(item.get("first_published") or item.get("updated_at"))
        if posted is None or not within_max_age(posted, max_age_hours=max_age_hours):
            continue
        location = ""
        loc = item.get("location")
        if isinstance(loc, dict):
            location = str(loc.get("name") or "")
        company = str(item.get("company_name") or board_token)
        out.append(
            JobPosting(
                source="greenhouse",
                company=company,
                title=str(item.get("title") or ""),
                location=location,
                url=str(item.get("absolute_url") or ""),
                posted_at=posted,
                description=strip_html(str(item.get("content") or "")),
            )
        )
    return out


def fetch_lever(
    company: str,
    *,
    http: HttpTransport,
    max_age_hours: int,
    timeout_s: float,
) -> list[JobPosting]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    payload = http.get_json(url, timeout_s=timeout_s)
    if not isinstance(payload, list):
        raise SkillUpstreamError(f"Lever payload for {company} was not a list")
    out: list[JobPosting] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        posted = parse_datetime(item.get("createdAt") or item.get("created_at"))
        if posted is None or not within_max_age(posted, max_age_hours=max_age_hours):
            continue
        cats = item.get("categories") if isinstance(item.get("categories"), dict) else {}
        location = str(cats.get("location") or item.get("location") or "")
        desc = item.get("descriptionPlain") or item.get("description") or ""
        out.append(
            JobPosting(
                source="lever",
                company=str(item.get("company") or company),
                title=str(item.get("text") or item.get("title") or ""),
                location=location,
                url=str(item.get("hostedUrl") or item.get("applyUrl") or ""),
                posted_at=posted,
                description=strip_html(str(desc)),
            )
        )
    return out


def fetch_workday(
    board: WorkdayBoard,
    *,
    http: HttpTransport,
    max_age_hours: int,
    timeout_s: float,
) -> list[JobPosting]:
    url = f"https://{board.host}/wday/cxs/{board.tenant}/{board.site}/jobs"
    payload = http.post_json(
        url,
        body={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""},
        timeout_s=timeout_s,
    )
    postings = _as_list(payload, "jobPostings")
    out: list[JobPosting] = []
    for item in postings:
        if not isinstance(item, dict):
            continue
        posted = parse_datetime(item.get("postedOn") or item.get("firstPosted"))
        if posted is None or not within_max_age(posted, max_age_hours=max_age_hours):
            continue
        external = str(item.get("externalPath") or "")
        apply_url = f"https://{board.host}{external}" if external.startswith("/") else str(item.get("externalUrl") or "")
        out.append(
            JobPosting(
                source="workday",
                company=board.company,
                title=str(item.get("title") or ""),
                location=str(item.get("locationsText") or ""),
                url=apply_url,
                posted_at=posted,
                description=strip_html(str(item.get("bulletFields") or item.get("title") or "")),
            )
        )
    return out


def fetch_generic_web(urls: list[str], *, http: HttpTransport, max_age_hours: int, timeout_s: float) -> list[JobPosting]:
    """Fetch job postings from generic web URLs.

    This is a placeholder implementation that performs a simple GET request
    and expects a JSON list of job dicts with keys matching JobPosting fields.
    Errors are logged and ignored to keep the ingestion pipeline robust.
    """
    out: list[JobPosting] = []
    for url in urls:
        try:
            payload = http.get_json(url, timeout_s=timeout_s)
            # Assume payload is a list of job dicts; adapt as needed.
            if isinstance(payload, list):
                for item in payload:
                    try:
                        posted = parse_datetime(item.get("posted_at") or item.get("date"))
                        if posted is None or not within_max_age(posted, max_age_hours):
                            continue
                        out.append(
                            JobPosting(
                                source="generic_web",
                                company=str(item.get("company") or ""),
                                title=str(item.get("title") or ""),
                                location=str(item.get("location") or ""),
                                url=str(item.get("url") or ""),
                                posted_at=posted,
                                description=strip_html(str(item.get("description") or "")),
                            )
                        )
                    except Exception:
                        continue
        except Exception as exc:
            logger.error(f"generic_web fetch error for {url}: {exc}")
    return out


def _as_list(payload: Any, key: str) -> list[Any]:
    if not isinstance(payload, dict):
        raise SkillUpstreamError(f"Expected object with {key!r}")
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise SkillUpstreamError(f"Expected list at {key!r}")
    return value
