import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HomePage } from "./HomePage";

describe("HomePage", () => {
  it("shows the app name as the main heading", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: "Vocab App" }),
    ).toBeInTheDocument();
  });
});
