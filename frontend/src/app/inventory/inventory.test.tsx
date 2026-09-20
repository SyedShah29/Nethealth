import { describe, expect, it } from "vitest";
import { groupDevicesBySite, type Device, type Site } from "./page";
const sites: Site[] = [{ id: "site-1", name: "West", code: "WEST", region: "west" }];
const devices: Device[] = [{ id: "device-1", name: "Core", hostname: "core-1", management_ip: "192.0.2.1", device_type: "CORE_ROUTER", site_id: "site-1", status: "UNKNOWN", monitoring_enabled: true }, { id: "device-2", name: "Edge", hostname: "edge-1", management_ip: "192.0.2.2", device_type: "EDGE_ROUTER", site_id: "missing", status: "UNKNOWN", monitoring_enabled: false }];
describe("inventory grouping", () => { it("groups devices by site and labels missing sites", () => { const grouped = groupDevicesBySite(devices, sites); expect(grouped.West).toHaveLength(1); expect(grouped["Unassigned site"][0].name).toBe("Edge"); }); });
