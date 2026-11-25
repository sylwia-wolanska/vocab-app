import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";
import { getMe, login, register } from "../api/auth";
import { fetchHealth } from "../api/health";
import { renderWithProviders } from "../test/render";

vi.mock("../api/auth");
vi.mock("../api/health");

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.mocked(fetchHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getMe).mockResolvedValue({
      id: 2,
      email: "new@example.com",
      is_active: true,
      created_at: "2026-01-01T12:00:00Z",
    });
  });

  it("rejects passwords that do not match", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />, { route: "/register" });

    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.type(
      screen.getByLabelText("Password (at least 8 characters)"),
      "password one",
    );
    await user.type(screen.getByLabelText("Repeat password"), "password two");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The passwords do not match",
    );
    expect(register).not.toHaveBeenCalled();
  });

  it("creates the account and logs in", async () => {
    vi.mocked(register).mockResolvedValue(undefined);
    vi.mocked(login).mockResolvedValue("token-456");
    const user = userEvent.setup();
    renderWithProviders(<App />, { route: "/register" });

    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.type(
      screen.getByLabelText("Password (at least 8 characters)"),
      "password one",
    );
    await user.type(screen.getByLabelText("Repeat password"), "password one");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByRole("heading", { name: "Vocab App" }),
    ).toBeInTheDocument();
    expect(register).toHaveBeenCalledWith("new@example.com", "password one");
    expect(localStorage.getItem("vocab.token")).toBe("token-456");
  });
});
