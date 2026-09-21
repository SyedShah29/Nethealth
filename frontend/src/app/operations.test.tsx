import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CapacityPage from "./capacity/page";
import DashboardPage from "./dashboard/page";
import SubscriberDiagnosticsPage from "./diagnostics/[subscriberId]/page";
import IncidentsPage from "./incidents/page";
import { apiGet } from "@/lib/api/client";

vi.mock("next/navigation", () => ({
  useParams: () => ({ subscriberId: "SUB-42" }),
}));

vi.mock("@/lib/api/client", () => ({
  apiGet: vi.fn(),
}));

const mockedApiGet = vi.mocked(apiGet);

describe("operations screens", () => {
  beforeEach(() => mockedApiGet.mockReset());

  it("renders the NOC summary and operational widgets", async () => {
    mockedApiGet.mockResolvedValue({
      summary: { devices: { total: 3, UP: 2, DOWN: 1 } },
      widgets: { active_incidents: [{ title: "PON outage", severity: "HIGH" }] },
    });
    render(<DashboardPage />);
    expect(await screen.findByText("PON outage", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("devices")).toBeInTheDocument();
    expect(screen.getByText("active incidents")).toBeInTheDocument();
  });

  it("renders all Customer 360 sections and an explainable health score", async () => {
    mockedApiGet.mockResolvedValue({
      identity: { subscriber_id: "SUB-42", package_speed: "100 Mbps" },
      session: { nas: "NAS-1" },
      fiber: { olt: "OLT-1", pon: "PON-7", onu: "ONU-9", rx: -20, tx: 2 },
      performance: { latency_ms: 10, packet_loss_percent: 0 },
      stability: { disconnects_today: 1, disconnects_last_7_days: 2 },
      incident: null,
      diagnosis: {
        status: "CUSTOMER-SPECIFIC ISSUE",
        evidence: ["Customer RX degraded"],
        recommended_action: "Inspect drop fiber and connector.",
      },
      health: {
        score: 62,
        category: "WARNING",
        components: [{ component: "optical_health", contribution: 12, maximum: 25 }],
      },
    });
    render(<SubscriberDiagnosticsPage />);
    expect(await screen.findByText("Diagnosis: CUSTOMER-SPECIFIC ISSUE")).toBeInTheDocument();
    expect(screen.getByText("62/100", { exact: false })).toBeInTheDocument();
    for (const section of ["Identity", "Session", "Fiber", "Performance", "Stability"]) {
      expect(screen.getByRole("heading", { name: section })).toBeInTheDocument();
    }
  });

  it("labels capacity projections as estimates and shows assumptions", async () => {
    mockedApiGet.mockImplementation(async (path: string) => {
      if (path === "/capacity/assessments") {
        return [{ id: "a1", entity_id: "uplink-1", metric_name: "utilization_percent", current_percent: 84, sustained_percent: 82, duration_seconds: 600, category: "WARNING" }];
      }
      return [{ id: "t1", entity_id: "uplink-1", metric_name: "utilization_percent", window_days: 90, slope_per_day: 0.2, threshold_percent: 80, projected_crossing_at: "2026-12-01T00:00:00Z", assumptions: ["The projection is an estimate, not a certainty."] }];
    });
    render(<CapacityPage />);
    expect(await screen.findByText("WARNING")).toBeInTheDocument();
    expect(screen.getByText("May cross 80% around", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("The projection is an estimate, not a certainty.")).toBeInTheDocument();
  });

  it("renders incident scope without emitting per-subscriber alerts", async () => {
    mockedApiGet.mockResolvedValue([{ id: "i1", title: "Critical PON outage", category: "PON_OUTAGE", severity: "CRITICAL", status: "OPEN", affected_subscribers: ["S1", "S2"], recommendations: ["Inspect PON uplink."] }]);
    render(<IncidentsPage />);
    await waitFor(() => expect(screen.getByText("Critical PON outage")).toBeInTheDocument());
    expect(screen.getByText("2 subscribers affected")).toBeInTheDocument();
  });
});
