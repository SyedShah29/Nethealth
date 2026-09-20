"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api/client";

export type Site = { id: string; name: string; code: string; region: string };
export type Device = {
  id: string;
  name: string;
  hostname: string;
  management_ip: string;
  device_type: string;
  site_id: string;
  status: string;
  monitoring_enabled: boolean;
};
export type DeviceFilters = {
  search: string;
  siteId: string;
  deviceType: string;
  status: string;
  monitoring: string;
};

const DEVICE_TYPES = [
  "CORE_ROUTER",
  "EDGE_ROUTER",
  "BNG",
  "BRAS",
  "AGGREGATION_SWITCH",
  "ACCESS_SWITCH",
  "OLT",
  "OTHER",
];

export function groupDevicesBySite(devices: Device[], sites: Site[]) {
  const names = new Map(sites.map((site) => [site.id, site.name]));
  return devices.reduce<Record<string, Device[]>>((groups, device) => {
    const siteName = names.get(device.site_id) ?? "Unassigned site";
    (groups[siteName] ??= []).push(device);
    return groups;
  }, {});
}

export function buildDeviceQuery(filters: DeviceFilters): string {
  const query = new URLSearchParams();
  if (filters.search) query.set("search", filters.search);
  if (filters.siteId) query.set("site_id", filters.siteId);
  if (filters.deviceType) query.set("device_type", filters.deviceType);
  if (filters.status) query.set("status", filters.status);
  if (filters.monitoring) query.set("monitoring_enabled", filters.monitoring);
  const value = query.toString();
  return value ? `?${value}` : "";
}

export default function InventoryPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [filters, setFilters] = useState<DeviceFilters>({
    search: "",
    siteId: "",
    deviceType: "",
    status: "",
    monitoring: "",
  });
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      apiGet<Device[]>(`/devices${buildDeviceQuery(filters)}`, controller.signal),
      apiGet<Site[]>("/sites", controller.signal),
    ])
      .then(([loadedDevices, loadedSites]) => {
        setDevices(loadedDevices);
        setSites(loadedSites);
        setError("");
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Unable to load inventory.");
        }
      });
    return () => controller.abort();
  }, [filters]);

  const groupedDevices = useMemo(
    () => groupDevicesBySite(devices, sites),
    [devices, sites],
  );
  const update = (field: keyof DeviceFilters, value: string) => {
    setFilters((current) => ({ ...current, [field]: value }));
  };

  return (
    <main className="foundation inventory" aria-labelledby="inventory-title">
      <p className="eyebrow">Phase 2 · Inventory</p>
      <h1 id="inventory-title">Network inventory</h1>
      <p className="lede">Authoritative device inventory and monitoring state.</p>
      <div className="inventory-filters" aria-label="Device filters">
        <label htmlFor="device-search">Search devices</label>
        <input
          id="device-search"
          value={filters.search}
          onChange={(event) => update("search", event.target.value)}
          placeholder="Name, hostname, or management IP"
        />
        <label htmlFor="site-filter">Site</label>
        <select
          id="site-filter"
          value={filters.siteId}
          onChange={(event) => update("siteId", event.target.value)}
        >
          <option value="">All sites</option>
          {sites.map((site) => <option value={site.id} key={site.id}>{site.name}</option>)}
        </select>
        <label htmlFor="type-filter">Device type</label>
        <select
          id="type-filter"
          value={filters.deviceType}
          onChange={(event) => update("deviceType", event.target.value)}
        >
          <option value="">All types</option>
          {DEVICE_TYPES.map((type) => <option value={type} key={type}>{type}</option>)}
        </select>
        <label htmlFor="status-filter">Status</label>
        <select
          id="status-filter"
          value={filters.status}
          onChange={(event) => update("status", event.target.value)}
        >
          <option value="">All statuses</option>
          {['UNKNOWN', 'UP', 'DEGRADED', 'DOWN'].map((status) => (
            <option value={status} key={status}>{status}</option>
          ))}
        </select>
        <label htmlFor="monitoring-filter">Monitoring</label>
        <select
          id="monitoring-filter"
          value={filters.monitoring}
          onChange={(event) => update("monitoring", event.target.value)}
        >
          <option value="">All monitoring states</option>
          <option value="true">Enabled</option>
          <option value="false">Disabled</option>
        </select>
      </div>
      {error && <p role="alert">{error}</p>}
      {Object.entries(groupedDevices).map(([siteName, siteDevices]) => (
        <section className="inventory-group" key={siteName} aria-labelledby={`site-${siteName}`}>
          <h2 id={`site-${siteName}`}>{siteName}</h2>
          <ul className="device-list">
            {siteDevices.map((device) => (
              <li className="device-card" key={device.id}>
                <Link href={`/inventory/${device.id}`}><strong>{device.name}</strong></Link>
                <span>{device.device_type} · {device.management_ip}</span>
                <span className={device.monitoring_enabled ? "monitoring-on" : "monitoring-off"}>
                  {device.monitoring_enabled ? "Monitoring enabled" : "Monitoring disabled"}
                  {" · "}{device.status}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ))}
      {!error && devices.length === 0 && <p>No devices match the current filters.</p>}
    </main>
  );
}
