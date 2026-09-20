import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TopologyPage, { downstreamIds, statusPresentation } from "./page";

const graph = {
  nodes: [
    { id: "core", node_type: "CORE", name: "CORE-01", entity_type: "DEVICE", entity_id: "1", status: "UP", attributes: {} },
    { id: "olt", node_type: "OLT", name: "OLT-04", entity_type: "OLT", entity_id: "2", status: "WARNING", attributes: {} },
    { id: "pon", node_type: "PON", name: "PON-7", entity_type: "PON", entity_id: "3", status: "DOWN", attributes: {} },
  ],
  edges: [
    { id: "e1", source_node_id: "core", target_node_id: "olt", relation: "DEPENDS_ON" },
    { id: "e2", source_node_id: "olt", target_node_id: "pon", relation: "DEPENDS_ON" },
  ],
};

describe("topology", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => graph }));
  });

  it("walks all downstream dependencies", () => {
    expect([...downstreamIds("core", graph.edges)]).toEqual(["olt", "pon"]);
  });

  it("provides text and icons in addition to status color", () => {
    expect(statusPresentation("UP")).toMatchObject({ label: "Healthy", symbol: "✓" });
    expect(statusPresentation("WARNING").label).toBe("Warning");
    expect(statusPresentation("DOWN").label).toBe("Critical");
    expect(statusPresentation("UNREACHABLE").label).toBe("Unknown or unreachable");
  });

  it("renders an interactive failure-impact view", async () => {
    render(<TopologyPage />);
    await waitFor(() => expect(screen.getByText("CORE-01")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /CORE-01/ }));
    expect(screen.getByText("2 downstream entities depend on this node.")).toBeInTheDocument();
    expect(screen.getByText("PON: PON-7")).toBeInTheDocument();
  });
});
