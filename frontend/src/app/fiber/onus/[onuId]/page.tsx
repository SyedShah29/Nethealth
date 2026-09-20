"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api/client";
import type { ONU } from "../../page";

export type OpticalWindow = "current" | "24h" | "7d" | "30d";
type OpticalMetric = {
  metric_name: string;
  value: number | null;
  unit: string;
  classification: "GOOD" | "WARNING" | "CRITICAL" | "UNKNOWN";
};
type OpticalStatus = { onu_id: string; observed_at: string | null; metrics: OpticalMetric[] };
type HistoryPoint = {
  timestamp: string;
  metric_name: string;
  value: number;
  value_min: number;
  value_max: number;
  unit: string | null;
};
type OpticalHistory = {
  onu_id: string;
  window: OpticalWindow;
  resolution: string;
  points: HistoryPoint[];
};

const WINDOWS: Array<{ value: OpticalWindow; label: string }> = [
  { value: "current", label: "Current" },
  { value: "24h", label: "24 hours" },
  { value: "7d", label: "7 days" },
  { value: "30d", label: "30 days" },
];

export function opticalHistoryPath(onuId: string, window: OpticalWindow): string {
  return `/onus/${encodeURIComponent(onuId)}/optical-history?window=${window}`;
}

export default function ONUDetailPage() {
  const { onuId } = useParams<{ onuId: string }>();
  const [onu, setOnu] = useState<ONU>();
  const [status, setStatus] = useState<OpticalStatus>();
  const [history, setHistory] = useState<OpticalHistory>();
  const [window, setWindow] = useState<OpticalWindow>("current");
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      apiGet<ONU>(`/onus/${encodeURIComponent(onuId)}`, controller.signal),
      apiGet<OpticalStatus>(
        `/onus/${encodeURIComponent(onuId)}/optical-status`,
        controller.signal,
      ),
    ])
      .then(([loadedOnu, loadedStatus]) => {
        setOnu(loadedOnu);
        setStatus(loadedStatus);
        setError("");
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Unable to load ONU status.");
        }
      });
    return () => controller.abort();
  }, [onuId]);

  useEffect(() => {
    const controller = new AbortController();
    apiGet<OpticalHistory>(opticalHistoryPath(onuId, window), controller.signal)
      .then(setHistory)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Unable to load optical history.");
        }
      });
    return () => controller.abort();
  }, [onuId, window]);

  if (error) {
    return <main className="foundation"><p role="alert">{error}</p><Link href="/fiber">Back</Link></main>;
  }
  if (!onu || !status) return <main className="foundation"><p>Loading ONU…</p></main>;

  return (
    <main className="foundation fiber" aria-labelledby="onu-title">
      <Link href="/fiber">← Back to fiber access</Link>
      <p className="eyebrow">ONU optical diagnostics</p>
      <h1 id="onu-title">{onu.onu_identifier}</h1>
      <p className="lede">{onu.serial_number} · {onu.status} · {onu.registration_status}</p>
      <section className="optical-grid" aria-label="Current optical status">
        {status.metrics.map((metric) => (
          <article className="status-card" key={metric.metric_name}>
            <h2>{metric.metric_name.replaceAll("_", " ")}</h2>
            <strong>{metric.value ?? "Unknown"} {metric.value === null ? "" : metric.unit}</strong>
            <span className={`optical-${metric.classification.toLowerCase()}`}>
              {metric.classification}
            </span>
          </article>
        ))}
      </section>
      <section aria-labelledby="history-title">
        <h2 id="history-title">Optical history</h2>
        <div className="history-windows" aria-label="Optical history window">
          {WINDOWS.map((item) => (
            <button
              aria-pressed={window === item.value}
              key={item.value}
              onClick={() => setWindow(item.value)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
        <p>Resolution: {history?.resolution ?? "loading"}</p>
        <ul className="history-list">
          {history?.points.map((point) => (
            <li key={`${point.timestamp}-${point.metric_name}`}>
              <strong>{point.metric_name.replaceAll("_", " ")}</strong>
              <span>{point.value} {point.unit ?? ""}</span>
              <time dateTime={point.timestamp}>{new Date(point.timestamp).toLocaleString()}</time>
            </li>
          ))}
        </ul>
        {history?.points.length === 0 && <p>No optical samples in this window.</p>}
      </section>
    </main>
  );
}
