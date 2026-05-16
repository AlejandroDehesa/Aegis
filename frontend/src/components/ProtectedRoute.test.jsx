import { screen } from "@testing-library/react";

import { ProtectedRoute } from "./ProtectedRoute";
import { renderWithProviders } from "../test/testUtils";

describe("ProtectedRoute", () => {
  test("redirects to login when session is not authenticated", async () => {
    renderWithProviders(
      <ProtectedRoute>
        <div>Private Content</div>
      </ProtectedRoute>,
      {
        route: "/private",
        path: "/private",
        useRoutes: true,
        authValue: {
          isAuthenticated: false,
          isBootstrapping: false,
        },
      },
    );

    expect(await screen.findByText("Login Screen")).toBeInTheDocument();
    expect(screen.queryByText("Private Content")).not.toBeInTheDocument();
  });

  test("renders children when user is authenticated", () => {
    renderWithProviders(
      <ProtectedRoute>
        <div>Private Content</div>
      </ProtectedRoute>,
      {
        route: "/private",
        path: "/private",
        useRoutes: true,
        authValue: {
          isAuthenticated: true,
          isBootstrapping: false,
          user: { id: "u-1", email: "demo@aegis.local" },
          token: "token",
        },
      },
    );

    expect(screen.getByText("Private Content")).toBeInTheDocument();
  });
});
