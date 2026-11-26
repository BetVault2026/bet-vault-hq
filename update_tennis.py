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

# Rankings only: reserve four credits before attempting a weekly refresh.
if previous.get("ranking_attempt_week") == today.strftime("%G-%V"):
    sys.exit(0)
if spent + 4 > 100:
    print("Ranking safety cap reached")
    sys.exit(0)
previous["ranking_attempt_week"] = today.strftime("%G-%V")
previous["usage"] = {"month": month, "credits": spent + 4}
PATH.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n")
try:
    for league, label in (("tennis", "atp"), ("wta", "wta")):
        rankings = call("get_rankings", {"league": league, "limit": 20})
        if isinstance(rankings.get("rankings"), list) and rankings["rankings"]:
            previous[label]["rankings"] = rankings["rankings"][:20]
            previous[label]["rankings_updated_utc"] = now.isoformat()
            PATH.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n")
except Exception as error:
    print("Ranking refresh failed:", error, file=sys.stderr)
    sys.exit(1)
