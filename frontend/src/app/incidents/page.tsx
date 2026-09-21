"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api/client";

type Incident = { id: string; title: string; category: string; severity: string; status: string; affected_subscribers: string[]; recommendations: string[] };

export default function IncidentsPage() {
  const [items, setItems] = useState<Incident[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { const controller = new AbortController(); apiGet<Incident[]>("/incidents", controller.signal).then(setItems).catch((reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Unable to load incidents."); }); return () => controller.abort(); }, []);
  return <main className="foundation operations"><p className="eyebrow">Phases 14–15</p><h1>Incidents</h1>{error && <p role="alert">{error}</p>}<section className="widget-grid">{items.map((item) => <article className="status-card" key={item.id}><span className={`severity-${item.severity.toLowerCase()}`}>{item.severity}</span><h2>{item.title}</h2><p>{item.category} · {item.status}</p><p>{item.affected_subscribers.length} subscribers affected</p><p>{item.recommendations[0]}</p></article>)}</section>{!error && items.length === 0 && <p>No incidents.</p>}</main>;
}
