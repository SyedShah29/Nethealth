import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiGet } from "@/lib/api/client";
import {
  default as InventoryPage,
  buildDeviceQuery,
  groupDevicesBySite,
  type Device,
  type Site,
} from "./page";

vi.mock("@/lib/api/client", () => ({ apiGet: vi.fn() }));

const sites: Site[] = [{ id: "site-1", name: "West", code: "WEST", region: "west" }];
const devices: Device[] = [
  {
    id: "device-1",
    name: "Core",
    hostname: "core-1",
    management_ip: "192.0.2.1",
    device_type: "CORE_ROUTER",
    site_id: "site-1",
    status: "UNKNOWN",
    monitoring_enabled: true,
  },
  {
    id: "device-2",
    name: "Edge",
    hostname: "edge-1",
    management_ip: "192.0.2.2",
    device_type: "EDGE_ROUTER",
    site_id: "missing",
    status: "UNKNOWN",
    monitoring_enabled: false,
  },
];

describe("inventory presentation", () => {
  beforeEach(() => {
    vi.mocked(apiGet).mockImplementation(async (path: string) => {
      return (path === "/sites" ? sites : devices) as never;
    });
  });

  it("groups devices by site and labels missing sites", () => {
    const grouped = groupDevicesBySite(devices, sites);
    expect(grouped.West).toHaveLength(1);
    expect(grouped["Unassigned site"][0].name).toBe("Edge");
  });

  it("builds all required inventory filters", () => {
    const query = buildDeviceQuery({
      search: "core router",
      siteId: "site-1",
      deviceType: "CORE_ROUTER",
      status: "UP",
      monitoring: "true",
    });
    expect(query).toContain("search=core+router");
    expect(query).toContain("site_id=site-1");
    expect(query).toContain("device_type=CORE_ROUTER");
    expect(query).toContain("status=UP");
    expect(query).toContain("monitoring_enabled=true");
  });

  it("renders inventory, grouping, and every roadmap filter", async () => {
    render(<InventoryPage />);
    await waitFor(() => expect(screen.getByText("Core")).toBeInTheDocument());
    expect(screen.getByLabelText("Search devices")).toBeInTheDocument();
    expect(screen.getByLabelText("Site")).toBeInTheDocument();
    expect(screen.getByLabelText("Device type")).toBeInTheDocument();
    expect(screen.getByLabelText("Status")).toBeInTheDocument();
    expect(screen.getByLabelText("Monitoring")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "West" })).toBeInTheDocument();
  });
});
