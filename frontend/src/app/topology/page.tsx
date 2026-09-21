"use client";

import { useEffect, useMemo, useState } from "react";

import { apiGet } from "@/lib/api/client";

export type TopologyNode = {
  id: string;
  node_type: string;
  name: string;
  entity_type: string | null;
  entity_id: string | null;
  status: string;
  attributes: Record<string, unknown>;
};

export type TopologyEdge = {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relation: string;
};

export type TopologyGraph = {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
};

export type TopologyFilters = {
  site: string;
  deviceType: string;
  severity: string;
  vendor: string;
  region: string;
};

const healthy = new Set(["GREEN", "HEALTHY", "UP", "ONLINE"]);
const warning = new Set(["YELLOW", "WARNING", "DEGRADED"]);
const critical = new Set(["RED", "CRITICAL", "DOWN", "OFFLINE"]);

export function statusPresentation(status: string): { label: string; symbol: string; tone: string } {
  const normalized = status.toUpperCase();
  if (healthy.has(normalized)) return { label: "Healthy", symbol: "✓", tone: "healthy" };
  if (warning.has(normalized)) return { label: "Warning", symbol: "!", tone: "warning" };
  if (critical.has(normalized)) return { label: "Critical", symbol: "×", tone: "critical" };
  return { label: "Unknown or unreachable", symbol: "?", tone: "unknown" };
}

export function downstreamIds(nodeId: string, edges: TopologyEdge[]): Set<string> {
  const result = new Set<string>();
  const queue = edges.filter((edge) => edge.source_node_id === nodeId).map((edge) => edge.target_node_id);
  while (queue.length > 0) {
    const current = queue.shift();
    if (!current || result.has(current)) continue;
    result.add(current);
    queue.push(
      ...edges.filter((edge) => edge.source_node_id === current).map((edge) => edge.target_node_id),
    );
  }
  return result;
}

export function nodeMatchesFilters(node: TopologyNode, filters: TopologyFilters): boolean {
  const presentation = statusPresentation(node.status);
  const value = (name: string) => String(node.attributes[name] ?? "");
  return (!filters.site || value("site_id") === filters.site)
    && (!filters.deviceType || node.node_type === filters.deviceType)
    && (!filters.severity || presentation.tone === filters.severity)
    && (!filters.vendor || value("vendor") === filters.vendor)
    && (!filters.region || value("region") === filters.region);
}

export default function TopologyPage() {
  const [graph, setGraph] = useState<TopologyGraph>({ nodes: [], edges: [] });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filters, setFilters] = useState<TopologyFilters>({
    site: "", deviceType: "", severity: "", vendor: "", region: "",
  });
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    apiGet<TopologyGraph>("/topology", controller.signal)
      .then((loaded) => {
        setGraph(loaded);
        setError("");
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "Unable to load topology.");
        }
      });
    return () => controller.abort();
  }, []);

  const selected = graph.nodes.find((node) => node.id === selectedId) ?? null;
  const affectedIds = useMemo(
    () => (selectedId ? downstreamIds(selectedId, graph.edges) : new Set<string>()),
    [selectedId, graph.edges],
  );
  const visibleNodes = graph.nodes.filter((node) => nodeMatchesFilters(node, filters));
  const nodeTypes = [...new Set(graph.nodes.map((node) => node.node_type))].sort();
  const options = (name: string) => [...new Set(graph.nodes.map((node) => String(node.attributes[name] ?? "")).filter(Boolean))].sort();
  const update = (name: keyof TopologyFilters, value: string) => setFilters((current) => ({ ...current, [name]: value }));

  return (
    <main className="foundation topology" aria-labelledby="topology-title">
      <p className="eyebrow">Phase 7 · Dependency topology</p>
      <h1 id="topology-title">Network dependency map</h1>
      <p className="lede">Select a node to reveal its downstream failure impact.</p>
      <div className="inventory-filters" aria-label="Topology filters">
        <label>Site<select aria-label="Site" value={filters.site} onChange={(event) => update("site", event.target.value)}><option value="">All sites</option>{options("site_id").map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Device type<select aria-label="Device type" value={filters.deviceType} onChange={(event) => update("deviceType", event.target.value)}><option value="">All types</option>{nodeTypes.map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Severity<select aria-label="Severity" value={filters.severity} onChange={(event) => update("severity", event.target.value)}><option value="">All severities</option>{["healthy", "warning", "critical", "unknown"].map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Vendor<select aria-label="Vendor" value={filters.vendor} onChange={(event) => update("vendor", event.target.value)}><option value="">All vendors</option>{options("vendor").map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Region<select aria-label="Region" value={filters.region} onChange={(event) => update("region", event.target.value)}><option value="">All regions</option>{options("region").map((item) => <option key={item}>{item}</option>)}</select></label>
      </div>
      {error && <p role="alert">{error}</p>}
      <section className="topology-grid" aria-label="Interactive topology">
        {visibleNodes.map((node) => {
          const status = statusPresentation(node.status);
          const affected = affectedIds.has(node.id);
          return (
            <button
              className={`topology-node topology-${status.tone}${selectedId === node.id ? " selected" : ""}${affected ? " affected" : ""}`}
              key={node.id}
              onClick={() => setSelectedId(node.id)}
              type="button"
              aria-pressed={selectedId === node.id}
            >
              <span className="topology-node-type">{node.node_type}</span>
              <strong>{node.name}</strong>
              <span><span aria-hidden="true">{status.symbol}</span> {status.label}</span>
            </button>
          );
        })}
      </section>
      {!error && graph.nodes.length === 0 && <p>No topology nodes are available.</p>}
      {selected && (
        <aside className="topology-impact" aria-live="polite">
          <h2>Failure impact: {selected.name}</h2>
          <p>{affectedIds.size} downstream entities depend on this node.</p>
          <p>{graph.nodes.filter((node) => affectedIds.has(node.id) && node.node_type === "SUBSCRIBER").length} subscribers and {graph.nodes.filter((node) => affectedIds.has(node.id) && node.node_type === "PON").length} PONs would be affected.</p>
          <ul>
            {graph.nodes.filter((node) => affectedIds.has(node.id)).map((node) => (
              <li key={node.id}>{node.node_type}: {node.name}</li>
            ))}
          </ul>
        </aside>
      )}
      <section className="topology-links" aria-label="Dependency links">
        <h2>Dependency links</h2>
        <ul>
          {graph.edges.map((edge) => {
            const source = graph.nodes.find((node) => node.id === edge.source_node_id);
            const target = graph.nodes.find((node) => node.id === edge.target_node_id);
            return <li key={edge.id}>{source?.name ?? "Unknown"} → {target?.name ?? "Unknown"}</li>;
          })}
        </ul>
      </section>
    </main>
  );
}
