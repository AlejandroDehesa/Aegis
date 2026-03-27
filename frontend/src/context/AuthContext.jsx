import { createContext, useEffect, useMemo, useState } from "react";

import { getCurrentUser, loginUser, signupUser } from "../api/authApi";
import { setUnauthorizedHandler } from "../api/http";
import { clearStoredToken, getStoredToken, setStoredToken } from "../utils/storage";
import { isJwtExpired } from "../utils/jwt";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken());
  const [user, setUser] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [authNotice, setAuthNotice] = useState("");

  useEffect(() => {
    async function bootstrap() {
      const storedToken = getStoredToken();

      if (!storedToken) {
        setIsBootstrapping(false);
        return;
      }

      if (isJwtExpired(storedToken)) {
        clearStoredToken();
        setToken(null);
        setUser(null);
        setAuthNotice("Your previous session expired. Please log in again.");
        setIsBootstrapping(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        setToken(storedToken);
      } catch {
        clearStoredToken();
        setToken(null);
        setUser(null);
      } finally {
        setIsBootstrapping(false);
      }
    }

    bootstrap();
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearStoredToken();
      setToken(null);
      setUser(null);
      setAuthNotice("Your session expired. Please log in again.");
    });

    return () => {
      setUnauthorizedHandler(null);
    };
  }, []);

  async function login(credentials) {
    const tokenResponse = await loginUser(credentials);

    if (!tokenResponse?.access_token) {
      throw new Error("The API did not return a valid access token.");
    }

    setStoredToken(tokenResponse.access_token);
    setToken(tokenResponse.access_token);

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setAuthNotice("");
      return currentUser;
    } catch (error) {
      clearStoredToken();
      setToken(null);
      setUser(null);
      throw error;
    }
  }

  async function register(payload) {
    await signupUser(payload);
    return login({
      email: payload.email,
      password: payload.password,
    });
  }

  function logout() {
    clearStoredToken();
    setToken(null);
    setUser(null);
    setAuthNotice("");
  }

  function clearAuthNotice() {
    setAuthNotice("");
  }

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token && user),
      isBootstrapping,
      authNotice,
      login,
      register,
      logout,
      clearAuthNotice,
    }),
    [token, user, isBootstrapping, authNotice],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
