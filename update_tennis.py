#!/usr/bin/env python3
"""Daily ATP/WTA snapshot using AcesAPI, with a 300-credit monthly safety cap."""
import copy
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

KEY = os.environ.get("ACES_API_KEY", "").strip()
if not KEY:
    print("ACES_API_KEY is missing; tennis refresh not performed.", file=sys.stderr)
    sys.exit(1)

PATH = Path("data/tennis.json")
now = datetime.now(timezone.utc)
today = now.date()
month = now.strftime("%Y-%m")
previous = json.loads(PATH.read_text()) if PATH.exists() else {}
usage = previous.get("usage", {})
spent = max(0, int(usage.get("credits", 0))) if usage.get("month") == month else 0
limit = 300

if previous.get("last_refresh_day") == today.isoformat():
    print("Tennis already refreshed today; skipping to protect the free credit budget.")
    sys.exit(0)

def is_final(match):
    status = str(match.get("status") or "").lower()
    return bool(match.get("score")) and (
        status in {"final", "finished", "completed"} or match.get("winner_id") is not None
    )

def start_time(match):
    value = match.get("starts_at")
    if value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
        except ValueError:
            pass
    day = match.get("match_date")
    if day:
        try:
            return datetime.combine(date.fromisoformat(str(day)), datetime.min.time(), timezone.utc)
        except ValueError:
            pass
    return None

def call(endpoint, payload):
    global spent
    if spent + 2 > limit:
        raise RuntimeError("Tennis credit safety cap reached during refresh")
    spent += 2  # Count attempted requests conservatively, including failures.
    request = urllib.request.Request(
        "https://mcp.acesapi.com/v1/" + endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-api-key": KEY, "User-Agent": "BetVaultHQ/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.load(response)
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError("Unexpected response from " + endpoint)
    return body["data"]

yesterday = today - timedelta(days=1)
dates_by_tour = {}
for label in ("atp", "wta"):
    prior_day = previous.get(label, {}).get("last_result_date")
    try:
        earliest = date.fromisoformat(prior_day) + timedelta(days=1) if prior_day else yesterday - timedelta(days=1)
    except (ValueError, TypeError):
        earliest = yesterday - timedelta(days=1)
    # Backfill at most two dates to recover missed scheduled runs without draining credits.
    earliest = max(earliest, yesterday - timedelta(days=1))
    dates_by_tour[label] = [
        day.isoformat() for day in (yesterday - timedelta(days=1), yesterday)
        if earliest <= day <= yesterday
    ]

rankings_due = today.weekday() == 0 or any(
    not previous.get(tour, {}).get("rankings") for tour in ("atp", "wta")
)
planned_calls = 2 + sum(len(days) for days in dates_by_tour.values()) + (2 if rankings_due else 0)
if spent + planned_calls * 2 > limit:
    print("Monthly tennis safety cap reached; previous data retained. "
          f"Tracked credits: {spent}/{limit}.")
    sys.exit(0)

data = copy.deepcopy(previous)
data["source"] = "AcesAPI"
data["coverage"] = "ATP and WTA singles; daily cached updates, not live scores"

try:
    for league, label in (("tennis", "atp"), ("wta", "wta")):
        schedule = call("get_schedule", {"league": league, "days": 7})
        if not isinstance(schedule.get("matches"), list):
            raise ValueError("Missing schedule matches for " + label)
        bucket = data.setdefault(label, {})
        confirmed = {
            str(match["match_id"]): match
            for match in bucket.get("results", [])
            if isinstance(match, dict) and match.get("match_id") and is_final(match)
        }
        upcoming = []
        for match in schedule["matches"]:
            if not isinstance(match, dict):
                continue
            when = start_time(match)
            if is_final(match) and match.get("match_id"):
                confirmed[str(match["match_id"])] = match
            elif (str(match.get("status") or "").lower() in {"scheduled", "upcoming"}
                  and when and when >= now):
                upcoming.append(match)

        for day in dates_by_tour[label]:
            results = call("get_matches", {"league": league, "date": day, "limit": 100})
            if not isinstance(results.get("matches"), list):
                raise ValueError("Missing match data for " + label + " on " + day)
            for match in results["matches"]:
                if isinstance(match, dict) and match.get("match_id") and is_final(match):
                    confirmed[str(match["match_id"])] = match

        # Never publish old scheduled matches as results, or past fixtures as upcoming.
        cutoff = now - timedelta(days=21)
        bucket["results"] = sorted(
            (match for match in confirmed.values()
             if (when := start_time(match)) and cutoff <= when <= now),
            key=lambda match: start_time(match),
            reverse=True,
        )[:80]
        bucket["upcoming"] = sorted(
            upcoming, key=lambda match: start_time(match)
        )[:80]

        if rankings_due:
            rankings = call("get_rankings", {"league": league, "limit": 20})
            if not isinstance(rankings.get("rankings"), list):
                raise ValueError("Missing rankings for " + label)
            if rankings["rankings"]:
                bucket["rankings"] = rankings["rankings"][:20]
                bucket["rankings_updated_utc"] = now.isoformat()

        bucket["last_result_date"] = yesterday.isoformat()
        bucket["updated_utc"] = now.isoformat()

    data["updated_utc"] = now.isoformat()
    data["last_refresh_day"] = today.isoformat()
    data["usage"] = {"month": month, "credits": spent}
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Tennis refreshed; tracked credits this month:", spent)
except Exception as error:
    # A failed update must never replace the last fully valid snapshot.
    previous["usage"] = {"month": month, "credits": spent}
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n")
    print("Tennis update failed:", error, file=sys.stderr)
    sys.exit(1)
