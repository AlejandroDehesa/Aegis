import { createContext, useEffect, useMemo, useState } from "react";

import { getCurrentUser, loginUser, signupUser } from "../api/authApi";
import { setUnauthorizedHandler } from "../api/http";
import { TOKEN_STORAGE_KEY } from "../constants/storage";
import { getErrorMessage } from "../utils/errors";
import { isJwtExpired, readJwtExpiration } from "../utils/jwt";
import { clearStoredToken, getStoredToken, setStoredToken } from "../utils/storage";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken());
  const [user, setUser] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [authNotice, setAuthNotice] = useState("");

  function resetSession({ notice = "" } = {}) {
    clearStoredToken();
    setToken(null);
    setUser(null);
    setAuthNotice(notice);
  }

  async function syncUserFromToken(storedToken) {
    if (!storedToken || isJwtExpired(storedToken)) {
      resetSession({
        notice: storedToken ? "Your session expired. Please log in again." : "",
      });
      return;
    }

    try {
      const currentUser = await getCurrentUser();
      setToken(storedToken);
      setUser(currentUser);
      setAuthNotice("");
    } catch (error) {
      resetSession({
        notice: getErrorMessage(error, "Your session is no longer valid. Please log in again."),
      });
    }
  }

  useEffect(() => {
    async function bootstrap() {
      const storedToken = getStoredToken();

      if (!storedToken) {
        setIsBootstrapping(false);
        return;
      }

      if (isJwtExpired(storedToken)) {
        resetSession({ notice: "Your previous session expired. Please log in again." });
        setIsBootstrapping(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        setToken(storedToken);
      } catch {
        resetSession();
      } finally {
        setIsBootstrapping(false);
      }
    }

    bootstrap();
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      resetSession({
        notice: "Your session expired. Please log in again.",
      });
    });

    return () => {
      setUnauthorizedHandler(null);
    };
  }, []);

  useEffect(() => {
    function handleStorageChange(event) {
      if (event.key !== TOKEN_STORAGE_KEY) {
        return;
      }

      const nextToken = getStoredToken();

      if (!nextToken) {
        setToken(null);
        setUser(null);
        setAuthNotice("Session ended in another tab.");
        return;
      }

      void syncUserFromToken(nextToken);
    }

    window.addEventListener("storage", handleStorageChange);
    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, []);

  useEffect(() => {
    if (!token) {
      return undefined;
    }

    const expiration = readJwtExpiration(token);

    if (!expiration) {
      return undefined;
    }

    const expiresInMs = expiration * 1000 - Date.now();

    if (expiresInMs <= 0) {
      resetSession({
        notice: "Your session expired. Please log in again.",
      });
      return undefined;
    }

    const timeout = window.setTimeout(() => {
      resetSession({
        notice: "Your session expired. Please log in again.",
      });
    }, expiresInMs + 1000);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [token]);

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
      resetSession();
      throw new Error(
        getErrorMessage(error, "Login failed due to an invalid session response."),
      );
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
    resetSession();
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
