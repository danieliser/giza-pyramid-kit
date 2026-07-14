#!/usr/bin/env python3
"""Fetch and archive DataForSEO research for the Giza article."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


API_ROOT = "https://api.dataforseo.com/v3"
DEFAULT_SEEDS = [
    "great pyramid construction theory",
    "pyramid construction theory",
    "pyramid ramp theory",
    "how were the pyramids built",
    "giza pyramid stl",
    "pyramid stl",
    "3d printable pyramid model",
    "great pyramid 3d model",
    "giza construction model",
    "huni choi pyramid",
]
SUGGESTION_SEEDS = [
    "pyramid construction",
    "great pyramid construction",
    "pyramid ramp",
    "pyramid 3d print",
]
EXACT_KEYWORDS = [
    "great pyramid construction theory",
    "great pyramid building theory",
    "great pyramid construction",
    "great pyramid construction methods",
    "great pyramid ramp theory",
    "great pyramid internal ramp theory",
    "pyramid construction theory",
    "pyramid building theory",
    "pyramid construction methods",
    "pyramid ramp theory",
    "pyramid internal ramp theory",
    "egyptian pyramid construction theory",
    "giza pyramid construction theory",
    "giza pyramid construction",
    "how were the pyramids built",
    "how was the great pyramid built",
    "how did they build the pyramids",
    "how were egyptian pyramids built",
    "how were the giza pyramids built",
    "how did ancient egyptians build pyramids",
    "giza pyramid stl",
    "great pyramid stl",
    "pyramid stl",
    "pyramid stl file",
    "pyramid 3d print",
    "3d printable pyramid",
    "3d printable pyramid model",
    "great pyramid 3d model",
    "giza pyramid 3d model",
    "great pyramid model",
    "giza pyramid model",
    "pyramid construction model",
    "giza construction model",
    "pyramid ramp model",
    "pyramid construction animation",
    "great pyramid construction animation",
    "pyramid internal chambers model",
    "great pyramid internal chambers",
    "great pyramid chambers model",
    "huni choi pyramid",
    "huni choi pyramid theory",
    "top down pyramid construction",
    "top down pyramid construction theory",
    "pyramid switchback ramp",
    "pyramid switchback ramp theory",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/seo/dataforseo") / datetime.now().date().isoformat(),
    )
    parser.add_argument("--location-code", type=int, default=2840)
    parser.add_argument("--language-code", default="en")
    return parser.parse_args()


def credentials() -> tuple[str, str]:
    config_path = Path.home() / ".codex" / "config.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    server = config.get("mcp_servers", {}).get("dataforseo", {})
    env = server.get("env", {})
    username = env.get("DATAFORSEO_USERNAME")
    password = env.get("DATAFORSEO_PASSWORD")
    if not username or not password:
        raise RuntimeError("DataForSEO credentials are not configured in Codex")
    return username, password


def request_json(
    path: str,
    username: str,
    password: str,
    payload: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        API_ROOT + path,
        data=body,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "User-Agent": "giza-pyramid-kit-seo-research/1.0",
        },
        method="GET" if payload is None else "POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"DataForSEO HTTP {error.code}: {detail}") from error


def task_error(response: dict[str, Any]) -> str | None:
    if response.get("status_code") != 20000:
        return f"{response.get('status_code')}: {response.get('status_message')}"
    for task in response.get("tasks") or []:
        if task.get("status_code") != 20000:
            return f"{task.get('status_code')}: {task.get('status_message')}"
    return None


def combine_responses(responses: list[dict[str, Any]]) -> dict[str, Any]:
    tasks = [task for response in responses for task in response.get("tasks") or []]
    top_level_errors = [
        response for response in responses if response.get("status_code") != 20000
    ]
    errors = len(top_level_errors) + sum(
        1 for task in tasks if task.get("status_code") != 20000
    )
    return {
        "version": responses[0].get("version") if responses else None,
        "status_code": top_level_errors[0].get("status_code") if top_level_errors else 20000,
        "status_message": (
            top_level_errors[0].get("status_message") if top_level_errors else "Ok."
        ),
        "tasks_count": len(tasks),
        "tasks_error": errors,
        "tasks": tasks,
    }


def labs_rows(response: dict[str, Any], source: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in response.get("tasks") or []:
        for result in task.get("result") or []:
            for item in result.get("items") or []:
                data = item.get("keyword_data") or item
                info = data.get("keyword_info") or {}
                props = data.get("keyword_properties") or {}
                intent = data.get("search_intent_info") or {}
                rows.append(
                    {
                        "keyword": data.get("keyword") or item.get("keyword"),
                        "search_volume": info.get("search_volume"),
                        "competition": info.get("competition"),
                        "competition_level": info.get("competition_level"),
                        "competition_index": info.get("competition_index"),
                        "cpc": info.get("cpc"),
                        "keyword_difficulty": props.get("keyword_difficulty"),
                        "main_intent": intent.get("main_intent"),
                        "source": source,
                    }
                )
    return rows


def volume_rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in response.get("tasks") or []:
        for result in task.get("result") or []:
            rows.append(
                {
                    "keyword": result.get("keyword"),
                    "search_volume": result.get("search_volume"),
                    "competition": result.get("competition"),
                    "competition_level": result.get("competition_level"),
                    "competition_index": result.get("competition_index"),
                    "cpc": result.get("cpc"),
                    "keyword_difficulty": None,
                    "main_intent": None,
                    "source": "google_ads_search_volume",
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "keyword",
        "search_volume",
        "keyword_difficulty",
        "main_intent",
        "competition_level",
        "competition_index",
        "competition",
        "cpc",
        "source",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def consolidate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    consolidated: dict[str, dict[str, Any]] = {}
    for row in rows:
        keyword = (row.get("keyword") or "").strip().lower()
        if not keyword:
            continue
        current = consolidated.setdefault(
            keyword,
            {
                "keyword": keyword,
                "search_volume": None,
                "competition": None,
                "competition_level": None,
                "competition_index": None,
                "cpc": None,
                "keyword_difficulty": None,
                "main_intent": None,
                "source": "",
            },
        )
        for field in (
            "search_volume",
            "competition",
            "competition_level",
            "competition_index",
            "cpc",
            "keyword_difficulty",
            "main_intent",
        ):
            if current[field] is None and row.get(field) is not None:
                current[field] = row[field]
        sources = set(filter(None, current["source"].split(";")))
        sources.add(row["source"])
        current["source"] = ";".join(sorted(sources))
    return sorted(consolidated.values(), key=lambda row: row["keyword"])


def write_summary(
    path: Path,
    fetched_at: str,
    location_code: int,
    language_code: str,
    rows: list[dict[str, Any]],
    cost: float,
) -> None:
    def numeric(value: Any) -> float:
        return float(value) if value not in (None, "") else 0

    relevant_terms = ("pyramid", "giza", "huni choi")
    ranked = sorted(
        (
            row
            for row in rows
            if row.get("search_volume") is not None
            and any(term in row["keyword"] for term in relevant_terms)
        ),
        key=lambda row: (
            numeric(row["search_volume"]),
            -numeric(row.get("keyword_difficulty")),
        ),
        reverse=True,
    )
    lines = [
        "# DataForSEO Keyword Snapshot",
        "",
        f"- Fetched: `{fetched_at}`",
        f"- Location code: `{location_code}` (United States)",
        f"- Language: `{language_code}`",
        f"- API cost reported for the final successful fetch: `${cost:.4f}`",
        f"- Normalized rows: `{len(rows)}`",
        "",
        "Raw API responses are retained beside this file. They contain no credentials.",
        "The normalized tables preserve off-topic category matches from the ideas endpoint;",
        "the display below is limited to terms containing pyramid, Giza, or Huni Choi.",
        "",
        "## Highest-volume Results",
        "",
        "| Keyword | Volume | KD | Intent | Source |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in ranked[:40]:
        lines.append(
            "| {keyword} | {volume} | {kd} | {intent} | {source} |".format(
                keyword=str(row.get("keyword") or "").replace("|", "\\|"),
                volume=row.get("search_volume") or 0,
                kd=row.get("keyword_difficulty") if row.get("keyword_difficulty") is not None else "",
                intent=row.get("main_intent") or "",
                source=row.get("source") or "",
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    username, password = credentials()
    args.output.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).isoformat()

    ideas_payload = [
        {
            "keywords": DEFAULT_SEEDS,
            "location_code": args.location_code,
            "language_code": args.language_code,
            "include_seed_keyword": True,
            "limit": 200,
        }
    ]
    volume_payload = [
        {
            "keywords": EXACT_KEYWORDS,
            "location_code": args.location_code,
            "language_code": args.language_code,
        }
    ]

    ideas = request_json(
        "/dataforseo_labs/google/keyword_ideas/live",
        username,
        password,
        ideas_payload,
    )
    volumes = request_json(
        "/keywords_data/google_ads/search_volume/live",
        username,
        password,
        volume_payload,
    )
    overview = request_json(
        "/dataforseo_labs/google/keyword_overview/live",
        username,
        password,
        [
            {
                "keywords": EXACT_KEYWORDS,
                "location_code": args.location_code,
                "language_code": args.language_code,
            }
        ],
    )
    suggestions = combine_responses(
        [
            request_json(
                "/dataforseo_labs/google/keyword_suggestions/live",
                username,
                password,
                [
                    {
                        "keyword": keyword,
                        "location_code": args.location_code,
                        "language_code": args.language_code,
                        "include_seed_keyword": True,
                        "limit": 100,
                    }
                ],
            )
            for keyword in SUGGESTION_SEEDS
        ]
    )
    responses = (
        ("keyword ideas", ideas),
        ("search volume", volumes),
        ("keyword overview", overview),
        ("keyword suggestions", suggestions),
    )
    for name, response in responses:
        if error := task_error(response):
            print(f"{name} failed: {error}", file=sys.stderr)
            return 1

    (args.output / "keyword_ideas.raw.json").write_text(
        json.dumps(ideas, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output / "search_volume.raw.json").write_text(
        json.dumps(volumes, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output / "keyword_overview.raw.json").write_text(
        json.dumps(overview, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output / "keyword_suggestions.raw.json").write_text(
        json.dumps(suggestions, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "fetched_at": fetched_at,
        "location_code": args.location_code,
        "language_code": args.language_code,
        "seed_keywords": DEFAULT_SEEDS,
        "suggestion_seed_keywords": SUGGESTION_SEEDS,
        "exact_keywords": EXACT_KEYWORDS,
        "endpoints": [
            "/dataforseo_labs/google/keyword_ideas/live",
            "/keywords_data/google_ads/search_volume/live",
            "/dataforseo_labs/google/keyword_overview/live",
            "/dataforseo_labs/google/keyword_suggestions/live",
        ],
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = (
        labs_rows(ideas, "labs_keyword_ideas")
        + volume_rows(volumes)
        + labs_rows(overview, "labs_keyword_overview")
        + labs_rows(suggestions, "labs_keyword_suggestions")
    )
    rows.sort(key=lambda row: (row.get("keyword") or "", row.get("source") or ""))
    write_csv(args.output / "keywords.csv", rows)
    consolidated = consolidate_rows(rows)
    write_csv(args.output / "keywords_consolidated.csv", consolidated)
    cost = sum(
        float(task.get("cost") or 0)
        for _, response in responses
        for task in response.get("tasks") or []
    )
    write_summary(
        args.output / "README.md",
        fetched_at,
        args.location_code,
        args.language_code,
        consolidated,
        cost,
    )
    print(
        f"Saved {len(rows)} source rows and {len(consolidated)} consolidated rows "
        f"to {args.output}"
    )
    print(f"DataForSEO reported cost: ${cost:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
