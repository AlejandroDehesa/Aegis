import { createContext, useEffect, useMemo, useState } from "react";

import { getCurrentUser, loginUser, logoutUser, signupUser } from "../api/authApi";
import { setUnauthorizedHandler } from "../api/http";
import { useI18n } from "../hooks/useI18n";
import { getErrorMessage } from "../utils/errors";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const { t } = useI18n();
  const [user, setUser] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [authNotice, setAuthNotice] = useState("");

  function resetSession({ notice = "" } = {}) {
    setUser(null);
    setAuthNotice(notice);
  }

  useEffect(() => {
    async function bootstrap() {
      try {
        const currentUser = await getCurrentUser({ ignoreUnauthorized: true });
        setUser(currentUser);
      } catch (error) {
        resetSession({
          notice:
            error?.status === 401
              ? ""
              : getErrorMessage(error, t("auth.notice.sessionNoLongerValid")),
        });
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

  async function login(credentials) {
    await loginUser(credentials);

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

  async function logout() {
    await logoutUser().catch(() => null);
    resetSession();
  }

  function clearAuthNotice() {
    setAuthNotice("");
  }

  const value = useMemo(
    () => ({
      user,
      token: null,
      isAuthenticated: Boolean(user),
      isBootstrapping,
      authNotice,
      login,
      register,
      logout,
      clearAuthNotice,
    }),
    [user, isBootstrapping, authNotice, t],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
