import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiGet, apiPost } from "@/lib/api/client";
import FieldOperationsPage from "./page";

vi.mock("@/lib/api/client", () => ({ apiGet: vi.fn(), apiPost: vi.fn() }));
const mockedGet = vi.mocked(apiGet);
const mockedPost = vi.mocked(apiPost);

describe("field operations", () => {
  beforeEach(() => {
    mockedGet.mockReset();
    mockedPost.mockReset();
  });

  it("shows assigned network context and advances an ordered task", async () => {
    const task = {
      id: "task-1", incident_id: "incident-1", subscriber_id: "SUB-42", olt_id: "OLT-1",
      pon_id: "PON-7", onu_id: "ONU-9", last_rx: -23.5, current_status: "ASSIGNED",
      recommended_checks: ["Inspect drop fiber."], status: "ASSIGNED" as const,
    };
    mockedGet.mockResolvedValue([task]);
    mockedPost.mockResolvedValue({ ...task, status: "ACCEPTED", current_status: "ACCEPTED" });
    render(<FieldOperationsPage />);

    expect(await screen.findByText("SUB-42")).toBeInTheDocument();
    expect(screen.getByText("OLT-1 / PON-7 / ONU-9")).toBeInTheDocument();
    expect(screen.getByText("-23.5 dBm")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Accept" }));
    expect(await screen.findByRole("button", { name: "Start work" })).toBeInTheDocument();
    expect(mockedPost).toHaveBeenCalledWith("/field-tasks/task-1/actions", { action: "ACCEPT" });
  });
});
