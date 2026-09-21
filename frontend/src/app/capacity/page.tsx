"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api/client";

type Assessment = { id: string; entity_id: string; metric_name: string; current_percent: number; sustained_percent: number; duration_seconds: number; category: string };
type Trend = { id: string; entity_id: string; metric_name: string; window_days: number; slope_per_day: number; threshold_percent: number; projected_crossing_at: string | null; assumptions: string[] };

export default function CapacityPage() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { const controller = new AbortController(); Promise.all([apiGet<Assessment[]>("/capacity/assessments", controller.signal), apiGet<Trend[]>("/capacity/trends", controller.signal)]).then(([a, t]) => { setAssessments(a); setTrends(t); }).catch((reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Unable to load capacity data."); }); return () => controller.abort(); }, []);
  return <main className="foundation operations"><p className="eyebrow">Phases 19–20</p><h1>Capacity monitoring and trends</h1>{error && <p role="alert">{error}</p>}<section><h2>Sustained load</h2><div className="widget-grid">{assessments.map((item) => <article className="status-card" key={item.id}><h3>{item.entity_id}</h3><strong>{item.category}</strong><p>{item.metric_name}: {item.sustained_percent.toFixed(1)}% sustained ({item.current_percent.toFixed(1)}% current)</p><p>Observed for {item.duration_seconds} seconds.</p></article>)}</div></section><section><h2>Projected threshold crossings</h2><div className="widget-grid">{trends.map((item) => <article className="status-card" key={item.id}><h3>{item.entity_id}</h3><p>{item.projected_crossing_at ? `May cross ${item.threshold_percent}% around ${new Date(item.projected_crossing_at).toLocaleDateString()}.` : "No future crossing is projected from the current trend."}</p><p>Slope: {item.slope_per_day.toFixed(3)} percentage points/day over {item.window_days} days.</p><ul>{item.assumptions.map((assumption) => <li key={assumption}>{assumption}</li>)}</ul></article>)}</div></section></main>;
}
