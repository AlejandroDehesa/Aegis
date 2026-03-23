import { createContext, useEffect, useMemo, useState } from "react";

import { getCurrentUser, loginUser, signupUser } from "../api/authApi";
import { clearStoredToken, getStoredToken, setStoredToken } from "../utils/storage";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken());
  const [user, setUser] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    async function bootstrap() {
      const storedToken = getStoredToken();

      if (!storedToken) {
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

  async function login(credentials) {
    const tokenResponse = await loginUser(credentials);
    setStoredToken(tokenResponse.access_token);
    setToken(tokenResponse.access_token);
    const currentUser = await getCurrentUser();
    setUser(currentUser);
    return currentUser;
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
  }

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token && user),
      isBootstrapping,
      login,
      register,
      logout,
    }),
    [token, user, isBootstrapping],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
