import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusCard } from "./status-card";

describe("StatusCard", () => {
  it("renders a textual status and detail", () => {
    render(
      <StatusCard label="Backend API" status="healthy" detail="Service is responding." />,
    );

    expect(screen.getByRole("heading", { name: "Backend API" })).toBeInTheDocument();
    expect(screen.getByText("healthy")).toBeInTheDocument();
    expect(screen.getByText("Service is responding.")).toBeInTheDocument();
  });
});
