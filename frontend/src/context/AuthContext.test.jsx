import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AuthProvider, AuthContext } from "./AuthContext";
import { LanguageProvider } from "./LanguageContext";

const authApiMocks = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  loginUser: vi.fn(),
  logoutUser: vi.fn(),
  signupUser: vi.fn(),
}));

vi.mock("../api/authApi", () => authApiMocks);

function AuthConsumerHarness() {
  return (
    <AuthContext.Consumer>
      {(value) => (
        <div>
          <p>{value.isAuthenticated ? value.user?.email : "anonymous"}</p>
          <button onClick={() => value.login({ email: "demo@aegis.local", password: "Demo12345" })}>
            Login
          </button>
          <button onClick={() => value.logout()}>Logout</button>
        </div>
      )}
    </AuthContext.Consumer>
  );
}

describe("AuthProvider", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  beforeEach(() => {
    authApiMocks.getCurrentUser.mockReset();
    authApiMocks.loginUser.mockReset();
    authApiMocks.logoutUser.mockReset();
    authApiMocks.signupUser.mockReset();
    window.localStorage.clear();
  });

  test("bootstraps the session through /me", async () => {
    authApiMocks.getCurrentUser.mockResolvedValueOnce({
      id: "u-1",
      email: "demo@aegis.local",
    });

    render(
      <LanguageProvider>
        <AuthProvider>
          <AuthConsumerHarness />
        </AuthProvider>
      </LanguageProvider>,
    );

    await screen.findByText("demo@aegis.local");
    expect(authApiMocks.getCurrentUser).toHaveBeenCalledWith({ ignoreUnauthorized: true });
  });

  test("login does not persist JWT in localStorage", async () => {
    const setItemSpy = vi.spyOn(window.localStorage.__proto__, "setItem");
    authApiMocks.getCurrentUser
      .mockRejectedValueOnce(Object.assign(new Error("unauthorized"), { status: 401 }))
      .mockResolvedValueOnce({
        id: "u-1",
        email: "demo@aegis.local",
      });
    authApiMocks.loginUser.mockResolvedValueOnce({ access_token: "server-token" });

    render(
      <LanguageProvider>
        <AuthProvider>
          <AuthConsumerHarness />
        </AuthProvider>
      </LanguageProvider>,
    );

    await waitFor(() => {
      expect(authApiMocks.getCurrentUser).toHaveBeenCalledWith({ ignoreUnauthorized: true });
    });

    await userEvent.click(screen.getByRole("button", { name: "Login" }));

    await screen.findByText("demo@aegis.local");
    expect(setItemSpy).not.toHaveBeenCalled();
  });

  test("logout calls backend endpoint and clears local auth state", async () => {
    authApiMocks.getCurrentUser.mockResolvedValueOnce({
      id: "u-1",
      email: "demo@aegis.local",
    });
    authApiMocks.logoutUser.mockResolvedValueOnce(null);

    render(
      <LanguageProvider>
        <AuthProvider>
          <AuthConsumerHarness />
        </AuthProvider>
      </LanguageProvider>,
    );

    await screen.findByText("demo@aegis.local");

    await userEvent.click(screen.getByRole("button", { name: "Logout" }));

    expect(authApiMocks.logoutUser).toHaveBeenCalledTimes(1);
    await screen.findByText("anonymous");
  });
});
