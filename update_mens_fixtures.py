"""Refresh men's ATP and Challenger fixtures using free endpoints only."""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def normalize(row, tour, now):
    if row.get("tour") != tour or row.get("gender") != "men" or row.get("draw") != "singles" or row.get("status") != "upcoming":
        return None
    if row.get("event_status") in ("Cancelled", "Postponed", "Walk Over"):
        return None
    players = row.get("players") or {}
    p1, p2 = players.get("p1") or {}, players.get("p2") or {}
    if not all(isinstance(p.get("name"), str) and p["name"].strip() and p["name"].strip().lower() not in ("tbc", "tbd", "unknown", "bye") for p in (p1, p2)):
        return None
    if not row.get("id") or not row.get("tournament") or not row.get("scheduled_time"):
        return None
    try:
        when = datetime.fromisoformat(row["scheduled_time"].replace("Z", "+00:00"))
        if when.tzinfo is None or not now <= when <= now + timedelta(days=7):
            return None
    except (ValueError, TypeError):
        return None
    return {"match_id": "lt-" + str(row["id"]), "tournament": row["tournament"],
            "round": ("ATP Challenger" if tour == "challenger" else "ATP") + (" · " + row["round_code"] if row.get("round_code") else ""),
            "player1": p1["name"], "player2": p2["name"],
            "player1_country": p1.get("country"), "player2_country": p2.get("country"),
            "starts_at": when.isoformat(), "match_date": when.date().isoformat(),
            "status": "upcoming", "source": "Live Tennis API"}

def main():
    path = Path("data/tennis.json")
    data = json.loads(path.read_text())
    now = datetime.now(timezone.utc)
    key = os.environ.get("LIVE_TENNIS_API_KEY", "").strip()
    if not key:
        raise SystemExit("LIVE_TENNIS_API_KEY missing")
    existing = data["atp"]
    if existing.get("live_fixture_day") == now.date().isoformat():
        print("Men's fixtures already refreshed today")
        return
    fixtures = {}
    for tour in ("atp", "challenger"):
        for offset in (0, 200):
            query = urlencode({"status": "upcoming", "tour": tour, "gender": "men", "draw": "singles",
                               "from": now.date().isoformat(), "to": (now + timedelta(days=7)).date().isoformat(),
                               "limit": 200, "offset": offset})
            request = Request("https://api.livetennisapi.com/api/public/v1/matches?" + query,
                              headers={"X-API-Key": key, "Accept": "application/json"})
            with urlopen(request, timeout=30) as response:
                rows = json.load(response)["data"]
            if not isinstance(rows, list):
                raise ValueError("Invalid fixture response")
            for row in rows:
                match = normalize(row, tour, now)
                if match:
                    fixtures[match["match_id"]] = match
            if len(rows) < 200:
                break
    existing["live_upcoming"] = sorted(fixtures.values(), key=lambda m: m["starts_at"])[:200]
    existing["live_fixture_day"] = now.date().isoformat()
    existing["live_fixture_updated_utc"] = now.isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Men's fixtures:", len(fixtures))

if __name__ == "__main__":
    main()
