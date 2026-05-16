import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { LanguageProvider } from "../context/LanguageContext";
import { AuthContext } from "../context/AuthContext";

const defaultAuthValue = {
  token: null,
  user: null,
  isAuthenticated: false,
  isBootstrapping: false,
  authNotice: "",
  login: async () => {},
  register: async () => {},
  logout: () => {},
  clearAuthNotice: () => {},
};

export function renderWithProviders(
  ui,
  {
    route = "/",
    path = "/",
    authValue = defaultAuthValue,
    useRoutes = false,
    loginElement = <div>Login Screen</div>,
  } = {},
) {
  const wrapped = (
    <LanguageProvider>
      <AuthContext.Provider value={{ ...defaultAuthValue, ...authValue }}>
        <MemoryRouter initialEntries={[route]}>
          {useRoutes ? (
            <Routes>
              <Route path="/login" element={loginElement} />
              <Route path={path} element={ui} />
            </Routes>
          ) : (
            ui
          )}
        </MemoryRouter>
      </AuthContext.Provider>
    </LanguageProvider>
  );

  return render(wrapped);
}
