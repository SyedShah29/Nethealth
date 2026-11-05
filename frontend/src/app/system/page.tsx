"use client";

import { useEffect, useState } from "react";

import { apiGet } from "@/lib/api/client";
import { StatusCard } from "@/ui/status-card";

type PlatformHealth = {
  status: "HEALTHY" | "WARNING" | "CRITICAL" | "UNKNOWN";
  collector_health: Record<string, number>;
  worker: { status: string; last_seen?: string | null };
  queue_depth: number;
  database_latency_ms: number;
  api: { request_count: number; error_count: number; average_response_ms: number };
  failed_polls: number;
  metrics_ingestion_per_minute: number;
  disk: { used_percent: number };
  database_size_bytes: number;
  notification_failures: number;
};

function displayStatus(status: string): "healthy" | "warning" | "critical" | "unknown" {
  const normalized = status.toLowerCase();
  if (normalized === "online") return "healthy";
  return normalized === "healthy" || normalized === "warning" || normalized === "critical"
    ? normalized
    : "unknown";
}

export default function PlatformHealthPage() {
  const [health, setHealth] = useState<PlatformHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    apiGet<PlatformHealth>("/system/platform-health", controller.signal)
      .then(setHealth)
      .catch((reason: unknown) =>
        setError(reason instanceof Error ? reason.message : "Unavailable"),
      );
    return () => controller.abort();
  }, []);

  if (error) return <main><h1>Platform Health</h1><p role="alert">{error}</p></main>;
  if (!health) return <main><h1>Platform Health</h1><p>Loading platform health…</p></main>;

  return (
    <main className="foundation operations">
      <p className="eyebrow">Phase 39 · Platform observability</p>
      <h1>Platform Health</h1>
      <section className="status-grid" aria-label="Platform health indicators">
        <StatusCard label="Overall" status={displayStatus(health.status)} detail="Platform status" />
        <StatusCard label="Worker" status={displayStatus(health.worker.status)} detail={health.worker.last_seen ?? "No heartbeat"} />
        <StatusCard label="Queue" status={health.queue_depth > 1000 ? "warning" : "healthy"} detail={`${health.queue_depth} queued tasks`} />
        <StatusCard label="Database" status={health.database_latency_ms > 250 ? "warning" : "healthy"} detail={`${health.database_latency_ms} ms · ${health.database_size_bytes} bytes`} />
        <StatusCard label="API" status={health.api.error_count > 0 ? "warning" : "healthy"} detail={`${health.api.average_response_ms} ms average`} />
        <StatusCard label="Collectors" status={health.failed_polls > 0 ? "warning" : "healthy"} detail={`${health.failed_polls} failed polls`} />
        <StatusCard label="Ingestion" status="healthy" detail={`${health.metrics_ingestion_per_minute} metrics/min`} />
        <StatusCard label="Disk" status={health.disk.used_percent >= 90 ? "critical" : health.disk.used_percent >= 80 ? "warning" : "healthy"} detail={`${health.disk.used_percent}% used`} />
        <StatusCard label="Notifications" status={health.notification_failures > 0 ? "warning" : "healthy"} detail={`${health.notification_failures} failed`} />
      </section>
    </main>
  );
}
