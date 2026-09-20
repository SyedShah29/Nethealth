import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiGet } from "@/lib/api/client";
import FiberPage, { buildFiberHierarchy, type OLT, type ONU, type PON } from "./page";
import ONUDetailPage, { opticalHistoryPath } from "./onus/[onuId]/page";

vi.mock("@/lib/api/client", () => ({ apiGet: vi.fn() }));
vi.mock("next/navigation", () => ({ useParams: () => ({ onuId: "onu-1" }) }));

const olt: OLT = {
  id: "olt-1",
  device_id: "device-1",
  vendor: "Huawei",
  model: "MA5800",
  frame_count: 2,
  slot_information: { "0": [1] },
  uplinks: ["uplink-1"],
};
const pon: PON = {
  id: "pon-1",
  olt_id: "olt-1",
  frame: 0,
  slot: 1,
  port: 2,
  technology: "GPON",
  status: "UP",
  subscriber_count: 1,
  configured_capacity: 128,
};
const onu: ONU = {
  id: "onu-1",
  onu_identifier: "ONU-001",
  serial_number: "HWTC00000001",
  olt_id: "olt-1",
  pon_id: "pon-1",
  subscriber_id: "SUB-10482",
  status: "ONLINE",
  registration_status: "REGISTERED",
  rx_power: -18,
  tx_power: 2,
};

describe("fiber access presentation", () => {
  beforeEach(() => vi.mocked(apiGet).mockReset());

  it("builds the OLT to PON to ONU hierarchy", () => {
    const hierarchy = buildFiberHierarchy([olt], [pon], [onu]);
    expect(hierarchy[0].pons[0].onus[0].onu_identifier).toBe("ONU-001");
  });

  it("renders the complete access hierarchy", async () => {
    vi.mocked(apiGet).mockImplementation(async (path: string) => {
      if (path === "/olts") return [olt] as never;
      if (path === "/pons") return [pon] as never;
      return [onu] as never;
    });
    render(<FiberPage />);
    await waitFor(() => expect(screen.getByText("Huawei MA5800")).toBeInTheDocument());
    expect(screen.getByText("Frame 0 / Slot 1 / PON 2")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ONU-001" })).toHaveAttribute(
      "href",
      "/fiber/onus/onu-1",
    );
  });

  it("builds bounded optical history queries", () => {
    expect(opticalHistoryPath("onu-1", "current")).toBe(
      "/onus/onu-1/optical-history?window=current",
    );
    expect(opticalHistoryPath("onu/unsafe", "30d")).toContain("onu%2Funsafe");
  });

  it("displays current classifications and every required history window", async () => {
    vi.mocked(apiGet).mockImplementation(async (path: string) => {
      if (!path) return [] as never;
      if (path.endsWith("/optical-status")) {
        return {
          onu_id: "onu-1",
          observed_at: "2026-09-20T00:00:00Z",
          metrics: [
            { metric_name: "RX_POWER", value: -18, unit: "dBm", classification: "GOOD" },
          ],
        } as never;
      }
      if (path.includes("/optical-history")) {
        return { onu_id: "onu-1", window: "current", resolution: "current", points: [] } as never;
      }
      return onu as never;
    });
    render(<ONUDetailPage />);
    await waitFor(() => expect(screen.getByText("ONU-001")).toBeInTheDocument());
    expect(screen.getByText("GOOD")).toBeInTheDocument();
    for (const label of ["Current", "24 hours", "7 days", "30 days"]) {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    }
    fireEvent.click(screen.getByRole("button", { name: "24 hours" }));
    await waitFor(() =>
      expect(apiGet).toHaveBeenCalledWith(
        "/onus/onu-1/optical-history?window=24h",
        expect.any(AbortSignal),
      ),
    );
  });
});
