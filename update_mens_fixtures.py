"""Refresh men's ATP and Challenger fixtures using free endpoints only."""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def normalize(row, tour, now):
    if row.get("tour") != tour or row.get("gender") != ("women" if tour == "wta" else "men") or row.get("draw") != "singles" or row.get("status") != "upcoming":
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
            "round": ("ATP Challenger" if tour == "challenger" else tour.upper()) + (" · " + row["round_code"] if row.get("round_code") else ""),
            "player1": p1["name"], "player2": p2["name"],
            "player1_country": p1.get("country"), "player2_country": p2.get("country"),
            "starts_at": when.isoformat(), "match_date": when.date().isoformat(),
            "status": "upcoming", "source": "Live Tennis API"}

def main():
    path = Path("data/tennis.json")
    data = json.loads(path.read_text())
    now = datetime.now(timezone.utc)
    day, month = now.date().isoformat(), now.strftime("%Y-%m")
    key = os.environ.get("LIVE_TENNIS_API_KEY", "").strip()
    if not key:
        raise SystemExit("LIVE_TENNIS_API_KEY missing")
    budget = data.setdefault("live_budget", {})
    def save():
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\\n")
    if budget.get("day") == day:
        print("Daily allocation already reserved; no repeat requests")
        return
    budget["day"] = day
    budget["daily_reserved"] = 9
    if budget.get("month") != month:
        budget.update(month=month, history_reserved=0)
    history_due = now.day in (1, 12, 23, 26) and budget["history_reserved"] + 3 <= 9
    if history_due:
        budget["history_reserved"] += 3
    save()
    def fetch(tour, status, offset=0):
        query = urlencode({"status": status, "tour": tour,
                           "gender": "women" if tour == "wta" else "men", "draw": "singles", "limit": 200, "offset": offset,
                           "from": (now - timedelta(days=7) if status == "completed" else now).date().isoformat(),
                           "to": (now + timedelta(days=7) if status == "upcoming" else now).date().isoformat()})
        request = Request("https://api.livetennisapi.com/api/public/v1/matches?" + query,
                          headers={"X-API-Key": key, "Accept": "application/json"})
        with urlopen(request, timeout=30) as response:
            rows = json.load(response)["data"]
        if not isinstance(rows, list):
            raise ValueError("Invalid response")
        return rows
    for label, tours in (("atp", ("atp", "challenger")), ("wta", ("wta",))):
        fixtures = {}
        for tour in tours:
            for offset in (0, 200):
                rows = fetch(tour, "upcoming", offset)
                for row in rows:
                    match = normalize(row, tour, now)
                    if match:
                        fixtures[match["match_id"]] = match
                if len(rows) < 200:
                    break
        bucket = data[label]
        bucket["live_upcoming"] = sorted(fixtures.values(), key=lambda m: m["starts_at"])[:200]
        bucket["live_fixture_updated_utc"] = now.isoformat()
        save()
    if history_due:
        for tour in ("atp", "challenger", "wta"):
            rows = fetch(tour, "completed")
            # Preserve raw confirmed provider results until score schema is validated.
            label = "wta" if tour == "wta" else "atp"
            bucket = data[label]
            bucket.setdefault("history_samples", {})[tour] = [
                {k: row.get(k) for k in ("id", "status", "event_status", "score", "winner", "players", "scheduled_time", "tournament", "round_code", "tour", "gender", "draw")}
                for row in rows if row.get("status") == "completed"
            ][:3]
            save()
    print("Fixture refresh complete; historical sample validation required.")

if __name__ == "__main__":
    main()
