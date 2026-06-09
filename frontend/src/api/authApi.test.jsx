import { getCurrentUser, loginUser, logoutUser, signupUser } from "./authApi";

const httpMocks = vi.hoisted(() => ({
  apiRequest: vi.fn(),
}));

vi.mock("./http", () => httpMocks);

describe("authApi", () => {
  beforeEach(() => {
    httpMocks.apiRequest.mockReset();
    httpMocks.apiRequest.mockResolvedValue({});
  });

  test("loginUser posts to /login", async () => {
    await loginUser({ email: "demo@aegis.local", password: "Demo12345" });
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/login", {
      method: "POST",
      body: { email: "demo@aegis.local", password: "Demo12345" },
      ignoreUnauthorized: true,
    });
  });

  test("signupUser posts to /signup", async () => {
    await signupUser({ email: "demo@aegis.local", password: "Demo12345" });
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/signup", {
      method: "POST",
      body: { email: "demo@aegis.local", password: "Demo12345" },
    });
  });

  test("getCurrentUser requests /me", async () => {
    await getCurrentUser({ ignoreUnauthorized: true });
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/me", {
      ignoreUnauthorized: true,
    });
  });

  test("logoutUser posts to /logout", async () => {
    await logoutUser();
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/logout", {
      method: "POST",
      ignoreUnauthorized: true,
    });
  });
});
