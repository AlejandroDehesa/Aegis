import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AuthPage } from "./AuthPage";
import { renderWithProviders } from "../test/testUtils";

describe("AuthPage", () => {
  test("renders login and register form controls", async () => {
    renderWithProviders(<AuthPage />);

    expect(screen.getByText("Login")).toBeInTheDocument();
    expect(screen.getByText("Register")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enter Aegis" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Register" }));
    expect(screen.getByRole("button", { name: "Create account" })).toBeInTheDocument();
  });
});
