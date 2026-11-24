import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { fetchHealth } from "../api/health";
import { renderWithProviders } from "../test/render";
import { HomePage } from "./HomePage";

vi.mock("../api/health");

describe("HomePage", () => {
  beforeEach(() => {
    vi.mocked(fetchHealth).mockResolvedValue({ status: "ok" });
  });

  it("shows the app name", () => {
    renderWithProviders(<HomePage />);
    expect(
      screen.getByRole("heading", { name: "Vocab App" }),
    ).toBeInTheDocument();
  });

  it("shows the API status when the backend responds", async () => {
    renderWithProviders(<HomePage />);
    expect(await screen.findByText("API: ok")).toBeInTheDocument();
  });

  it("shows unreachable when the request fails", async () => {
    vi.mocked(fetchHealth).mockRejectedValue(new Error("down"));
    renderWithProviders(<HomePage />);
    expect(await screen.findByText("API: unreachable")).toBeInTheDocument();
  });
});
