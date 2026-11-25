import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../App";
import { getMe, login } from "../api/auth";
import { ApiError } from "../api/errors";
import { fetchHealth } from "../api/health";
import { renderWithProviders } from "../test/render";

vi.mock("../api/auth");
vi.mock("../api/health");

describe("LoginPage", () => {
  beforeEach(() => {
    vi.mocked(fetchHealth).mockResolvedValue({ status: "ok" });
    vi.mocked(getMe).mockResolvedValue({
      id: 1,
      email: "sylwia@example.com",
      is_active: true,
      created_at: "2026-01-01T12:00:00Z",
    });
  });

  it("shows an error for a wrong password", async () => {
    vi.mocked(login).mockRejectedValue(
      new ApiError("Incorrect email or password", 401),
    );
    const user = userEvent.setup();
    renderWithProviders(<App />, { route: "/login" });

    await user.type(screen.getByLabelText("Email"), "sylwia@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong password");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Incorrect email or password",
    );
    expect(localStorage.getItem("vocab.token")).toBeNull();
  });

  it("stores the token and opens the home page", async () => {
    vi.mocked(login).mockResolvedValue("token-123");
    const user = userEvent.setup();
    renderWithProviders(<App />, { route: "/login" });

    await user.type(screen.getByLabelText("Email"), "sylwia@example.com");
    await user.type(screen.getByLabelText("Password"), "my test password");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(
      await screen.findByRole("heading", { name: "Vocab App" }),
    ).toBeInTheDocument();
    expect(login).toHaveBeenCalledWith(
      "sylwia@example.com",
      "my test password",
    );
    expect(localStorage.getItem("vocab.token")).toBe("token-123");
  });
});
