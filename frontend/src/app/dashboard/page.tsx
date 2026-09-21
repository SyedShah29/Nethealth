"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api/client";

type Dashboard = {
  summary: Record<string, Record<string, number>>;
  widgets: Record<string, Array<Record<string, unknown>>>;
};

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard>();
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    apiGet<Dashboard>("/dashboard", controller.signal).then(setData).catch((reason: unknown) => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Unable to load dashboard.");
    });
    return () => controller.abort();
  }, []);
  return (
    <main className="foundation operations" aria-labelledby="dashboard-title">
      <p className="eyebrow">Phase 17 · NOC</p>
      <h1 id="dashboard-title">Network operations dashboard</h1>
      {error && <p role="alert">{error}</p>}
      <section className="summary-grid" aria-label="Network summary">
        {Object.entries(data?.summary ?? {}).map(([group, values]) => (
          <article className="status-card" key={group}>
            <h2>{group.replaceAll("_", " ")}</h2>
            <dl>{Object.entries(values).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
          </article>
        ))}
      </section>
      <section className="widget-grid" aria-label="Operational widgets">
        {Object.entries(data?.widgets ?? {}).map(([name, rows]) => (
          <article className="status-card" key={name}>
            <h2>{name.replaceAll("_", " ")}</h2>
            {rows.length === 0 ? <p>No current items.</p> : <ul>{rows.map((row, index) => <li key={`${name}-${index}`}>{Object.entries(row).map(([key, value]) => `${key}: ${String(value)}`).join(" · ")}</li>)}</ul>}
          </article>
        ))}
      </section>
    </main>
  );
}
