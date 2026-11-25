import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { getMe } from "./api/auth";
import { fetchHealth } from "./api/health";
import { renderWithProviders } from "./test/render";

vi.mock("./api/auth");
vi.mock("./api/health");

describe("App routing", () => {
  beforeEach(() => {
    vi.mocked(fetchHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getMe).mockResolvedValue({
      id: 1,
      email: "sylwia@example.com",
      is_active: true,
      created_at: "2026-01-01T12:00:00Z",
    });
  });

  it("sends a visitor without a token to the login page", async () => {
    renderWithProviders(<App />);
    expect(
      await screen.findByRole("heading", { name: "Log in" }),
    ).toBeInTheDocument();
  });

  it("shows the home page to a logged-in user", async () => {
    localStorage.setItem("vocab.token", "test-token");
    renderWithProviders(<App />);
    expect(
      await screen.findByRole("heading", { name: "Vocab App" }),
    ).toBeInTheDocument();
  });
});
