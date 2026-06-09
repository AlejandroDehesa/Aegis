import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { AuthPage } from "./AuthPage";
import { renderWithProviders } from "../test/testUtils";

describe("AuthPage", () => {
  test("renders login and register form controls", async () => {
    renderWithProviders(<AuthPage />);

    expect(screen.getByText("Login")).toBeInTheDocument();
    expect(screen.getByText("Register")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /email/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByText("Enter a valid email address.")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Password must be 8-128 characters, include at least one letter and one number, and cannot be empty or only spaces.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enter Aegis" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Register" }));
    expect(screen.getByRole("button", { name: "Create account" })).toBeInTheDocument();
  });

  test("shows friendly validation errors for signup 422 responses", async () => {
    const register = vi.fn().mockRejectedValue({
      status: 422,
      payload: {
        detail: [
          { loc: ["body", "email"], msg: "value is not a valid email address" },
          { loc: ["body", "password"], msg: "String should have at least 8 characters" },
        ],
      },
    });

    renderWithProviders(<AuthPage />, {
      authValue: {
        register,
      },
    });

    await userEvent.click(screen.getByRole("button", { name: "Register" }));
    await userEvent.type(screen.getByRole("textbox", { name: /email/i }), "valid@example.com");
    await userEvent.type(screen.getByLabelText(/password/i), "Valid1234");
    await userEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Enter a valid email address. Password must be 8-128 characters, include at least one letter and one number, and cannot be empty or only spaces.",
    );
  });
});
