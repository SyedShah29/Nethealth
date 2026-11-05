"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost } from "@/lib/api/client";

type TaskStatus = "ASSIGNED" | "ACCEPTED" | "IN_PROGRESS" | "RESTORED" | "CLOSED";
type FieldTask = {
  id: string;
  incident_id: string;
  subscriber_id: string | null;
  olt_id: string | null;
  pon_id: string | null;
  onu_id: string | null;
  last_rx: number | null;
  current_status: string;
  recommended_checks: string[];
  status: TaskStatus;
};

const nextAction: Partial<Record<TaskStatus, { action: string; label: string }>> = {
  ASSIGNED: { action: "ACCEPT", label: "Accept" },
  ACCEPTED: { action: "START_WORK", label: "Start work" },
  IN_PROGRESS: { action: "MARK_RESTORED", label: "Mark restored" },
  RESTORED: { action: "CLOSE", label: "Close task" },
};

export default function FieldOperationsPage() {
  const [tasks, setTasks] = useState<FieldTask[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    apiGet<FieldTask[]>("/field-tasks", controller.signal)
      .then(setTasks)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Unable to load field tasks.");
        }
      });
    return () => controller.abort();
  }, []);

  async function advance(task: FieldTask) {
    const transition = nextAction[task.status];
    if (!transition) return;
    try {
      const updated = await apiPost<FieldTask>(`/field-tasks/${task.id}/actions`, {
        action: transition.action,
      });
      setTasks((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to update field task.");
    }
  }

  return (
    <main className="foundation operations">
      <div>
        <p className="eyebrow">Phase 21</p>
        <h1>Field operations</h1>
        <p className="lede">Assigned restoration work with only the network context needed on site.</p>
      </div>
      {error && <p role="alert">{error}</p>}
      <section className="widget-grid" aria-label="Field tasks">
        {tasks.map((task) => {
          const transition = nextAction[task.status];
          return (
            <article className="status-card" key={task.id}>
              <span className={`status-label status-${task.status === "CLOSED" ? "healthy" : "loading"}`}>
                {task.status.replaceAll("_", " ")}
              </span>
              <h2>Incident {task.incident_id}</h2>
              <dl>
                <div><dt>Subscriber</dt><dd>{task.subscriber_id ?? "Not linked"}</dd></div>
                <div><dt>OLT / PON / ONU</dt><dd>{[task.olt_id, task.pon_id, task.onu_id].filter(Boolean).join(" / ") || "Not linked"}</dd></div>
                <div><dt>Last RX</dt><dd>{task.last_rx === null ? "Unknown" : `${task.last_rx} dBm`}</dd></div>
                <div><dt>Current status</dt><dd>{task.current_status}</dd></div>
              </dl>
              <h3>Recommended checks</h3>
              <ul>{task.recommended_checks.map((check) => <li key={check}>{check}</li>)}</ul>
              {transition && <button type="button" onClick={() => void advance(task)}>{transition.label}</button>}
            </article>
          );
        })}
      </section>
      {!error && tasks.length === 0 && <p>No field tasks assigned.</p>}
    </main>
  );
}
