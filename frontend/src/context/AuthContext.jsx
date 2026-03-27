import { createContext, useEffect, useMemo, useState } from "react";

import { getCurrentUser, loginUser, signupUser } from "../api/authApi";
import { setUnauthorizedHandler } from "../api/http";
import { TOKEN_STORAGE_KEY } from "../constants/storage";
import { useI18n } from "../hooks/useI18n";
import { getErrorMessage } from "../utils/errors";
import { isJwtExpired, readJwtExpiration } from "../utils/jwt";
import { clearStoredToken, getStoredToken, setStoredToken } from "../utils/storage";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const { t } = useI18n();
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
        notice: storedToken ? t("auth.notice.sessionExpired") : "",
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
        notice: getErrorMessage(error, t("auth.notice.sessionNoLongerValid")),
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
        resetSession({ notice: t("auth.notice.previousSessionExpired") });
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
  }, [t]);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      resetSession({
        notice: t("auth.notice.sessionExpired"),
      });
    });

    return () => {
      setUnauthorizedHandler(null);
    };
  }, [t]);

  useEffect(() => {
    function handleStorageChange(event) {
      if (event.key !== TOKEN_STORAGE_KEY) {
        return;
      }

      const nextToken = getStoredToken();

      if (!nextToken) {
        setToken(null);
        setUser(null);
        setAuthNotice(t("auth.notice.sessionEndedAnotherTab"));
        return;
      }

      void syncUserFromToken(nextToken);
    }

    window.addEventListener("storage", handleStorageChange);
    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, [t]);

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
        notice: t("auth.notice.sessionExpired"),
      });
      return undefined;
    }

    const timeout = window.setTimeout(() => {
      resetSession({
        notice: t("auth.notice.sessionExpired"),
      });
    }, expiresInMs + 1000);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [token, t]);

  async function login(credentials) {
    const tokenResponse = await loginUser(credentials);

    if (!tokenResponse?.access_token) {
      throw new Error(t("auth.notice.tokenMissing"));
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
        getErrorMessage(error, t("auth.notice.loginInvalidSessionResponse")),
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
    [token, user, isBootstrapping, authNotice, t],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
