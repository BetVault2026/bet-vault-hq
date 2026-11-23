
(async function () {
  const updated = document.getElementById("boxing-updated");
  const results = document.getElementById("boxing-results");

  if (!updated || !results) return;

  function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, function (c) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[c];
    });
  }

  function section(title, items, format) {
    const heading = document.createElement("h3");
    heading.textContent = title;
    results.appendChild(heading);

    if (!items.length) {
      const p = document.createElement("p");
      p.textContent = "No verified information available.";
      results.appendChild(p);
      return;
    }

    const list = document.createElement("ul");

    items.forEach(function (item) {
      const li = document.createElement("li");
      li.textContent = format(item);
      list.appendChild(li);
    });

    results.appendChild(list);
  }

  try {
    const response = await fetch("data/boxing.json", {
      cache: "no-store"
    });

    if (!response.ok) throw new Error("Data unavailable");

    const data = await response.json();

    updated.textContent = data.updated_utc
      ? "Last refreshed: " +
        new Date(data.updated_utc).toLocaleString("en-GB")
      : "Update time unavailable";

    section("Upcoming world-title fights", data.upcoming || [],
      b => `${b.date || "Date TBC"}: ${b.boxer_a || "TBC"} vs ${b.boxer_b || "TBC"}`
    );

    section("Recent results", data.results || [],
      b => `${b.boxer_a || "TBC"} vs ${b.boxer_b || "TBC"} — ${b.method || b.status || "Result pending"}`
    );

    section("Champions", data.champions || [],
      c => `${c.name || "Unknown"} — ${c.weight || "Weight TBC"} (${c.organisation || "Organisation TBC"})`
    );

  } catch (error) {
    updated.textContent = "Boxing information is temporarily unavailable.";
    results.textContent = "Please check back later.";
  }
})();
