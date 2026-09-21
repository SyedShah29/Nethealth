"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api/client";

type Diagnostics = {
  identity: Record<string, unknown>;
  session: Record<string, unknown>;
  fiber: Record<string, unknown>;
  performance: Record<string, unknown>;
  stability: Record<string, unknown>;
  incident: Record<string, unknown> | null;
  diagnosis: { status: string; evidence: string[]; recommended_action: string };
  health: null | { score: number; category: string; components: Array<{ component: string; contribution: number; maximum: number }> };
};

function Facts({ title, value }: { title: string; value: Record<string, unknown> | null }) {
  return <article className="status-card"><h2>{title}</h2>{value ? <dl>{Object.entries(value).map(([name, fact]) => <div key={name}><dt>{name.replaceAll("_", " ")}</dt><dd>{typeof fact === "object" ? JSON.stringify(fact) : String(fact ?? "Unknown")}</dd></div>)}</dl> : <p>None.</p>}</article>;
}

export default function SubscriberDiagnosticsPage() {
  const { subscriberId } = useParams<{ subscriberId: string }>();
  const [data, setData] = useState<Diagnostics>();
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    apiGet<Diagnostics>(`/subscribers/${encodeURIComponent(subscriberId)}/diagnostics`, controller.signal).then(setData).catch((reason: unknown) => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Unable to load diagnostics.");
    });
    return () => controller.abort();
  }, [subscriberId]);
  return <main className="foundation operations" aria-labelledby="diagnostics-title"><p className="eyebrow">Subscriber 360</p><h1 id="diagnostics-title">{subscriberId}</h1>{error && <p role="alert">{error}</p>}{data && <><section className="widget-grid"><Facts title="Identity" value={data.identity} /><Facts title="Session" value={data.session} /><Facts title="Fiber" value={data.fiber} /><Facts title="Performance" value={data.performance} /><Facts title="Stability" value={data.stability} /><Facts title="Active incident" value={data.incident} /></section><section className="status-card"><h2>Diagnosis: {data.diagnosis.status}</h2><ul>{data.diagnosis.evidence.map((item) => <li key={item}>{item}</li>)}</ul><p><strong>Recommended action:</strong> {data.diagnosis.recommended_action}</p></section><section className="status-card"><h2>Health score</h2>{data.health ? <><strong className="score">{data.health.score}/100 · {data.health.category}</strong><ul>{data.health.components.map((item) => <li key={item.component}>{item.component.replaceAll("_", " ")}: {item.contribution}/{item.maximum}</li>)}</ul></> : <p>No score has been evaluated.</p>}</section></>}</main>;
}
