"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiGet } from "@/lib/api/client";

export type Site = { id: string; name: string; code: string; region: string };
export type Device = { id: string; name: string; hostname: string; management_ip: string; device_type: string; site_id: string; status: string; monitoring_enabled: boolean };

export function groupDevicesBySite(devices: Device[], sites: Site[]) {
  const names = new Map(sites.map((site) => [site.id, site.name]));
  return devices.reduce<Record<string, Device[]>>((groups, device) => {
    const siteName = names.get(device.site_id) ?? "Unassigned site";
    (groups[siteName] ??= []).push(device);
    return groups;
  }, {});
}

export default function InventoryPage() {
  const [devices, setDevices] = useState<Device[]>([]); const [sites, setSites] = useState<Site[]>([]); const [search, setSearch] = useState(""); const [error, setError] = useState("");
  useEffect(() => { const controller = new AbortController(); Promise.all([apiGet<Device[]>(`/devices${search ? `?search=${encodeURIComponent(search)}` : ""}`, controller.signal), apiGet<Site[]>("/sites", controller.signal)]).then(([loadedDevices, loadedSites]) => { setDevices(loadedDevices); setSites(loadedSites); setError(""); }).catch((reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Unable to load inventory."); }); return () => controller.abort(); }, [search]);
  const groupedDevices = useMemo(() => groupDevicesBySite(devices, sites), [devices, sites]);
  return <main className="foundation inventory" aria-labelledby="inventory-title"><p className="eyebrow">Phase 2 · Inventory</p><h1 id="inventory-title">Network inventory</h1><p className="lede">Authoritative device inventory and monitoring state.</p><label htmlFor="device-search">Search devices</label><input id="device-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name, hostname, or management IP" />{error && <p role="alert">{error}</p>}{Object.entries(groupedDevices).map(([siteName, siteDevices]) => <section className="inventory-group" key={siteName} aria-labelledby={`site-${siteName}`}><h2 id={`site-${siteName}`}>{siteName}</h2><ul className="device-list">{siteDevices.map((device) => <li className="device-card" key={device.id}><Link href={`/inventory/${device.id}`}><strong>{device.name}</strong></Link><span>{device.device_type} · {device.management_ip}</span><span className={device.monitoring_enabled ? "monitoring-on" : "monitoring-off"}>{device.monitoring_enabled ? "Monitoring enabled" : "Monitoring disabled"} · {device.status}</span></li>)}</ul></section>)}{!error && devices.length === 0 && <p>No devices match the current search.</p>}</main>;
}
