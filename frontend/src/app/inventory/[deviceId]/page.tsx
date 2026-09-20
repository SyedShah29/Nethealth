"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet } from "@/lib/api/client";
import type { Device, Site } from "../page";
type Interface = { id: string; name: string; description: string | null; admin_status: string | null; oper_status: string | null };
export default function DeviceDetailPage() {
  const { deviceId } = useParams<{ deviceId: string }>(); const [device, setDevice] = useState<Device>(); const [site, setSite] = useState<Site>(); const [interfaces, setInterfaces] = useState<Interface[]>([]); const [error, setError] = useState("");
  useEffect(() => { const controller = new AbortController(); Promise.all([apiGet<Device>(`/devices/${deviceId}`, controller.signal), apiGet<Interface[]>(`/interfaces?device_id=${encodeURIComponent(deviceId)}`, controller.signal), apiGet<Site[]>("/sites", controller.signal)]).then(([loadedDevice, loadedInterfaces, sites]) => { setDevice(loadedDevice); setInterfaces(loadedInterfaces); setSite(sites.find((candidate) => candidate.id === loadedDevice.site_id)); }).catch((reason: unknown) => { if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "Unable to load device."); }); return () => controller.abort(); }, [deviceId]);
  if (error) return <main className="foundation"><p role="alert">{error}</p><Link href="/inventory">Back to inventory</Link></main>;
  if (!device) return <main className="foundation"><p>Loading device…</p></main>;
  return <main className="foundation inventory" aria-labelledby="device-title"><Link href="/inventory">← Back to inventory</Link><p className="eyebrow">Device detail</p><h1 id="device-title">{device.name}</h1><p className="lede">{device.hostname} · {device.management_ip} · {site?.name ?? "Unassigned site"}</p><p className={device.monitoring_enabled ? "monitoring-on" : "monitoring-off"}>{device.monitoring_enabled ? "Monitoring enabled" : "Monitoring disabled"} · {device.status}</p><section className="inventory-group" aria-labelledby="interfaces-title"><h2 id="interfaces-title">Interfaces</h2>{interfaces.length === 0 ? <p>No interfaces recorded.</p> : <ul className="device-list">{interfaces.map((item) => <li className="device-card" key={item.id}><strong>{item.name}</strong><span>{item.description ?? "No description"}</span><span>{item.admin_status ?? "admin unknown"} · {item.oper_status ?? "oper unknown"}</span></li>)}</ul>}</section></main>;
}
