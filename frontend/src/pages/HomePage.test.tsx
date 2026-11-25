import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getMe } from "../api/auth";
import { fetchHealth } from "../api/health";
import { renderWithProviders } from "../test/render";
import { HomePage } from "./HomePage";

vi.mock("../api/auth");
vi.mock("../api/health");

describe("HomePage", () => {
  beforeEach(() => {
    localStorage.setItem("vocab.token", "test-token");
    vi.mocked(fetchHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getMe).mockResolvedValue({
      id: 1,
      email: "sylwia@example.com",
      is_active: true,
      created_at: "2026-01-01T12:00:00Z",
    });
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

  it("shows who is logged in", async () => {
    renderWithProviders(<HomePage />);
    expect(
      await screen.findByText("Logged in as sylwia@example.com"),
    ).toBeInTheDocument();
  });

  it("removes the token on logout", async () => {
    const user = userEvent.setup();
    renderWithProviders(<HomePage />);
    await user.click(screen.getByRole("button", { name: "Log out" }));
    expect(localStorage.getItem("vocab.token")).toBeNull();
  });
});
