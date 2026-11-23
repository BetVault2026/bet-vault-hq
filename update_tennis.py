#!/usr/bin/env python3
"""Daily ATP/WTA cache. Maximum 300 tracked credits per UTC month."""
import json, os, sys, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

KEY = os.environ.get("ACES_API_KEY", "").strip()
if not KEY:
    print("ACES_API_KEY not configured; no credits used.")
    sys.exit(0)

path = Path("data/tennis.json")
now = datetime.now(timezone.utc)
month = now.strftime("%Y-%m")
previous = json.loads(path.read_text()) if path.exists() else {}
usage = previous.get("usage", {})
spent = int(usage.get("credits", 0)) if usage.get("month") == month else 0
weekly = now.weekday() == 0
planned = 8 + (4 if weekly else 0)
if spent + planned > 300:
    print("Monthly tennis safety cap reached; no requests made.")
    sys.exit(0)

def call(endpoint, payload):
    global spent
    req = urllib.request.Request(
        "https://mcp.acesapi.com/v1/" + endpoint,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-api-key": KEY,
                 "User-Agent": "BetVaultHQ/1.0"},
        method="POST",
    )
    # Count a request before attempting it: conservative safety accounting.
    spent += 2
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)
    if not isinstance(result, dict) or not isinstance(result.get("data"), dict):
        raise ValueError("Unexpected response from " + endpoint)
    return result["data"]

data = dict(previous)
data["source"] = "AcesAPI"
data["coverage"] = "ATP and WTA singles; daily updates, not live scores"
data["usage"] = {"month": month, "credits": spent}
try:
    for league, label in (("tennis", "atp"), ("wta", "wta")):
        schedule = call("get_schedule", {"league": league, "days": 7})
        data["usage"]["credits"] = spent
        data.setdefault(label, {})["upcoming"] = schedule.get("matches", [])[:80]
        # Request today's and recent results as one day-scoped call per tour.
        matches = call("get_matches", {"league": league, "date": (now - timedelta(days=1)).strftime("%Y-%m-%d"), "limit": 100})
        data["usage"]["credits"] = spent
        data[label]["results"] = matches.get("matches", [])[:80]
        if weekly:
            ranks = call("get_rankings", {"league": league, "limit": 20})
            data["usage"]["credits"] = spent
            data[label]["rankings"] = ranks.get("rankings", [])[:20]
        data[label]["updated_utc"] = now.isoformat()
    data["updated_utc"] = now.isoformat()
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Tennis refreshed; tracked credits this month:", spent)
except Exception as error:
    # Preserve credit usage on failure so retries cannot silently bypass cap.
    data["usage"]["credits"] = spent
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Tennis update failed:", error, file=sys.stderr)
    sys.exit(1)
