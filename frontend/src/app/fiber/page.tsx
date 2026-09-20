"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { apiGet } from "@/lib/api/client";

export type OLT = {
  id: string;
  device_id: string;
  vendor: string;
  model: string;
  frame_count: number;
  slot_information: Record<string, unknown>;
  uplinks: string[];
};

export type PON = {
  id: string;
  olt_id: string;
  frame: number;
  slot: number;
  port: number;
  technology: string;
  status: string;
  subscriber_count: number;
  configured_capacity: number;
};

export type ONU = {
  id: string;
  onu_identifier: string;
  serial_number: string;
  olt_id: string;
  pon_id: string;
  subscriber_id: string | null;
  status: string;
  registration_status: string;
  rx_power: number | null;
  tx_power: number | null;
};

export type FiberHierarchy = Array<{
  olt: OLT;
  pons: Array<{ pon: PON; onus: ONU[] }>;
}>;

export function buildFiberHierarchy(olts: OLT[], pons: PON[], onus: ONU[]): FiberHierarchy {
  return olts.map((olt) => ({
    olt,
    pons: pons
      .filter((pon) => pon.olt_id === olt.id)
      .map((pon) => ({
        pon,
        onus: onus.filter((onu) => onu.pon_id === pon.id),
      })),
  }));
}

export default function FiberPage() {
  const [olts, setOlts] = useState<OLT[]>([]);
  const [pons, setPons] = useState<PON[]>([]);
  const [onus, setOnus] = useState<ONU[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      apiGet<OLT[]>("/olts", controller.signal),
      apiGet<PON[]>("/pons", controller.signal),
      apiGet<ONU[]>("/onus?limit=500", controller.signal),
    ])
      .then(([loadedOlts, loadedPons, loadedOnus]) => {
        setOlts(loadedOlts);
        setPons(loadedPons);
        setOnus(loadedOnus);
        setError("");
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Unable to load fiber access data.");
        }
      });
    return () => controller.abort();
  }, []);

  const hierarchy = useMemo(() => buildFiberHierarchy(olts, pons, onus), [olts, pons, onus]);

  return (
    <main className="foundation fiber" aria-labelledby="fiber-title">
      <p className="eyebrow">Phase 6 · Fiber access</p>
      <h1 id="fiber-title">OLT, PON, and ONU inventory</h1>
      <p className="lede">Read-only access hierarchy and current optical state.</p>
      {error && <p role="alert">{error}</p>}
      {hierarchy.map(({ olt, pons: oltPons }) => (
        <section className="fiber-olt" key={olt.id}>
          <h2>{olt.vendor} {olt.model}</h2>
          <p>{olt.frame_count} frames · {olt.uplinks.length} uplinks</p>
          {oltPons.map(({ pon, onus: ponOnus }) => (
            <article className="fiber-pon" key={pon.id}>
              <h3>Frame {pon.frame} / Slot {pon.slot} / PON {pon.port}</h3>
              <p>
                {pon.technology} · {pon.status} · {pon.subscriber_count}/{pon.configured_capacity}
              </p>
              <ul className="fiber-onu-list">
                {ponOnus.map((onu) => (
                  <li key={onu.id}>
                    <Link href={`/fiber/onus/${onu.id}`}>{onu.onu_identifier}</Link>
                    <span>{onu.status} · RX {onu.rx_power ?? "unknown"} dBm</span>
                  </li>
                ))}
              </ul>
              {ponOnus.length === 0 && <p>No ONUs recorded.</p>}
            </article>
          ))}
        </section>
      ))}
      {!error && hierarchy.length === 0 && <p>No OLT records are available.</p>}
    </main>
  );
}
