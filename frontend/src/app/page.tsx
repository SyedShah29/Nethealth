"use client";

import { useEffect, useState } from "react";

import { getApiHealth, type ApiHealth } from "@/lib/api/health";
import { StatusCard } from "@/ui/status-card";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; health: ApiHealth }
  | { status: "unavailable" };

export default function Home() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    getApiHealth(controller.signal)
      .then((health) => setState({ status: "ready", health }))
      .catch(() => {
        if (!controller.signal.aborted) {
          setState({ status: "unavailable" });
        }
      });
    return () => controller.abort();
  }, []);

  const status = state.status === "ready" ? state.health.status : state.status;
  const detail =
    state.status === "ready"
      ? `${state.health.service} responded successfully.`
      : state.status === "loading"
        ? "Checking the backend API."
        : "The backend API did not respond.";

  return (
    <section className="foundation" aria-labelledby="page-title">
      <div>
        <p className="eyebrow">Phase 0 · Foundation</p>
        <h1 id="page-title">Platform services</h1>
        <p className="lede">
          The NetHealth application foundation is ready for the next planned phase.
        </p>
      </div>
      <div className="status-grid">
        <StatusCard label="Backend API" status={status} detail={detail} />
      </div>
    </section>
  );
}
