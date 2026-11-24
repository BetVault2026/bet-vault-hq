
import json
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

BASE = "https://openboxing.org/api"

def fetch(path):
    request = urllib.request.Request(
        BASE + path,
        headers={"User-Agent": "BetVaultHQ/1.0"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def boxer_name(boxer):
    name = boxer.get("name", {})
    if isinstance(name, dict):
        return " ".join(
            str(name.get(part, ""))
            for part in ("first", "last")
        ).strip()
    return str(name)

def simplify(bout):
    boxers = bout.get("boxers", {})
    result = bout.get("result") or {}
    return {
        "date": bout.get("date"),
        "boxer_a": boxer_name(boxers.get("boxerA") or {}),
        "boxer_b": boxer_name(boxers.get("boxerB") or {}),
        "status": bout.get("status"),
        "winner": result.get("winner"),
        "method": result.get("methodOfVictory"),
        "weight": (bout.get("weight") or {}).get("class"),
    }

scheduled = fetch("/bouts/scheduled/index.json")
all_bouts = fetch("/bouts/all/index.json")
reigns = fetch("/reigns/all/index.json")

today = datetime.now(ZoneInfo("Europe/London")).date().isoformat()

def ordered(bouts, reverse=False):
    return sorted(bouts, key=lambda b: b.get("date") or "", reverse=reverse)

finished = [
    bout for bout in all_bouts
    if bout.get("status") == "FINISHED" and bout.get("date") and bout["date"] <= today
]

current_champions = [
    {
        "name": boxer_name(reign.get("champion") or {}),
        "weight": ((reign.get("title") or {}).get("weight") or {}).get("class"),
        "organisation": (
            (((reign.get("title") or {}).get("org") or {}).get("name") or {})
            .get("short")
        ),
    }
    for reign in reigns
    if (reign.get("period") or {}).get("current") is True
]

data = {
    "updated_utc": datetime.now(timezone.utc).isoformat(),
    "source": BASE,
    "coverage": "World-title boxing only",
    "upcoming": [simplify(b) for b in ordered([b for b in scheduled if b.get("status") == "SCHEDULED" and (b.get("date") or "") >= today])[:30]],
    "results": [simplify(b) for b in ordered(finished, reverse=True)[:30]],
    "champions": current_champions,
}

Path("data").mkdir(exist_ok=True)
target = Path("data/boxing.json")
if not all(isinstance(v, list) and v for v in (all_bouts, reigns)) or not isinstance(scheduled, list) or not finished or not current_champions:
    raise ValueError("Incomplete boxing feed; existing data retained")
if target.exists():
    previous = json.loads(target.read_text(encoding="utf-8"))
    if all(previous.get(k) == v for k, v in data.items() if k != "updated_utc"):
        print("Boxing data unchanged")
        raise SystemExit(0)
temporary = target.with_suffix(".tmp")
temporary.write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

temporary.replace(target)
print("Boxing data updated successfully.")
