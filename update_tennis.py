#!/usr/bin/env python3
"""Weekly ATP/WTA cache. Maximum 300 tracked credits per UTC month."""
import copy, json, os, sys, urllib.request
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
weekly = now.weekday() == 4 or any(not previous.get(t, {}).get("rankings") for t in ("atp", "wta"))
planned = 2 * 2 * (1 + 7 + int(weekly))
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

data = copy.deepcopy(previous)
data["source"] = "AcesAPI"
data["coverage"] = "ATP and WTA singles; weekly Friday updates, not live scores"
data["usage"] = {"month": month, "credits": spent}
try:
    for league, label in (("tennis", "atp"), ("wta", "wta")):
        schedule = call("get_schedule", {"league": league, "days": 7})
        data["usage"]["credits"] = spent
        if not isinstance(schedule.get("matches"), list):
            raise ValueError("Missing schedule matches")
        data.setdefault(label, {})["upcoming"] = schedule["matches"][:80]
        # Seven completed UTC dates, including the previous Friday.
        old = data[label].get("results", [])
        combined = {str(m["match_id"]): m for m in old if m.get("match_id")}
        final_states = {"finished", "completed", "final"}
        for offset in range(7, 0, -1):
            date = (now - timedelta(days=offset)).strftime("%Y-%m-%d")
            matches = call("get_matches", {"league": league, "date": date, "limit": 100})
            data["usage"]["credits"] = spent
            if not isinstance(matches.get("matches"), list):
                raise ValueError("Missing results for " + date)
            for m in matches["matches"]:
                if m.get("match_id"):
                    key = str(m["match_id"])
                    old_match = combined.get(key, {})
                    if str(old_match.get("status", "")).lower() in final_states and str(m.get("status", "")).lower() not in final_states:
                        continue
                    combined[key] = m
        data[label]["results"] = sorted(combined.values(), key=lambda m: m.get("starts_at") or m.get("match_date") or "", reverse=True)[:80]
        if weekly:
            ranks = call("get_rankings", {"league": league, "limit": 20})
            data["usage"]["credits"] = spent
            if ranks.get("rankings"):
                data[label]["rankings"] = ranks["rankings"][:20]
        data[label]["updated_utc"] = now.isoformat()
    data["updated_utc"] = now.isoformat()
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Tennis refreshed; tracked credits this month:", spent)
except Exception as error:
    # Preserve credit usage on failure so retries cannot silently bypass cap.
    previous["usage"] = {"month": month, "credits": spent}
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n")
    print("Tennis update failed:", error, file=sys.stderr)
    sys.exit(1)
