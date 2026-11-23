(async function () {
  const root = document.getElementById("tennis-feed");
  const updated = document.getElementById("tennis-updated");
  if (!root || !updated) return;
  function el(tag, text, parent) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    (parent || root).appendChild(node);
    return node;
  }
  try {
    const response = await fetch("data/tennis.json", {cache: "no-store"});
    if (!response.ok) throw new Error("No data");
    const data = await response.json();
    updated.textContent = data.updated_utc
      ? "Data last fetched: " + new Date(data.updated_utc).toLocaleString("en-GB")
      : "Update time unavailable";
    const now = Date.now();
    for (const [key, name] of [["atp", "ATP"], ["wta", "WTA"]]) {
      const tour = data[key] || {};
      el("h3", name + " tennis");
      const upcoming = (tour.upcoming || []).filter(m =>
        m.status === "scheduled" && m.starts_at &&
        Date.parse(m.starts_at) >= now
      ).slice(0, 12);
      el("h4", "Upcoming matches");
      if (!upcoming.length) el("p", "No upcoming matches currently listed.");
      else {
        const list = el("ul");
        upcoming.forEach(m => {
          const date = new Date(m.starts_at).toLocaleString("en-GB", {dateStyle:"medium", timeStyle:"short"});
          el("li", date + " — " + (m.player1 || "TBC") + " vs " + (m.player2 || "TBC") + " (" + (m.tournament || "Tournament TBC") + ")", list);
        });
      }
      const results = (tour.results || []).filter(m =>
        ["finished", "completed", "final"].includes(String(m.status || "").toLowerCase()) &&
        m.player1 && m.player2
      ).slice(0, 12);
      el("h4", "Recent completed results");
      if (!results.length) el("p", "No completed results in the latest feed.");
      else {
        const list = el("ul");
        results.forEach(m => el("li", m.player1 + " vs " + m.player2 +
          (m.score ? " — " + m.score : "") + " (" + (m.tournament || "Tennis") + ")", list));
      }
      el("h4", "Rankings (provider snapshot)");
      const ranks = (tour.rankings || []).slice(0, 10);
      if (!ranks.length) el("p", "Rankings not available yet.");
      else {
        const list = el("ol");
        ranks.forEach(p => el("li", (p.name || "Unknown") + (p.points != null ? " — " + p.points + " points" : ""), list));
      }
    }
  } catch (err) {
    updated.textContent = "Tennis data is temporarily unavailable.";
    el("p", "Please use the official ATP and WTA links above.");
  }
})();