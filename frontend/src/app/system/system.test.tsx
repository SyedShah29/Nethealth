import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import PlatformHealthPage from "./page";

describe("PlatformHealthPage", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders accessible text for platform status indicators", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      status: "WARNING", collector_health: { HEALTHY: 2 },
      worker: { status: "ONLINE", last_seen: "now" }, queue_depth: 4,
      database_latency_ms: 3.2,
      api: { request_count: 12, error_count: 0, average_response_ms: 2.1 },
      failed_polls: 1, metrics_ingestion_per_minute: 40,
      disk: { used_percent: 50 }, database_size_bytes: 1000, notification_failures: 0,
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    render(<PlatformHealthPage />);
    await waitFor(() => expect(screen.getByText("Platform status")).toBeInTheDocument());
    expect(screen.getAllByText("warning")).toHaveLength(2);
    expect(screen.getByText("1 failed polls")).toBeInTheDocument();
  });
});
