import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { AuthPage } from "./AuthPage";
import { renderWithProviders } from "../test/testUtils";

describe("AuthPage", () => {
  test("renders login and register form controls", async () => {
    renderWithProviders(<AuthPage />);

    expect(screen.getByText("Entrar")).toBeInTheDocument();
    expect(screen.getByText("Registro")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /email/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/contrasena/i)).toBeInTheDocument();
    expect(screen.getByText("Introduce un email valido.")).toBeInTheDocument();
    expect(
      screen.getByText(
        "La contrasena debe tener entre 8 y 128 caracteres, incluir al menos una letra y un numero, y no puede estar vacia ni ser solo espacios.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrar en Aegis" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Registro" }));
    expect(screen.getByRole("button", { name: "Crear cuenta" })).toBeInTheDocument();
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

    await userEvent.click(screen.getByRole("button", { name: "Registro" }));
    await userEvent.type(screen.getByRole("textbox", { name: /email/i }), "valid@example.com");
    await userEvent.type(screen.getByLabelText(/contrasena/i), "Valid1234");
    await userEvent.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Introduce un email valido. La contrasena debe tener entre 8 y 128 caracteres, incluir al menos una letra y un numero, y no puede estar vacia ni ser solo espacios.",
    );
  });
});
