
import json
import urllib.request
from datetime import datetime, timezone
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

finished = [
    bout for bout in all_bouts
    if bout.get("status") == "FINISHED"
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
    "upcoming": [simplify(b) for b in scheduled[:30]],
    "results": [simplify(b) for b in finished[-30:][::-1]],
    "champions": current_champions,
}

Path("data").mkdir(exist_ok=True)
Path("data/boxing.json").write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("Boxing data updated successfully.")
