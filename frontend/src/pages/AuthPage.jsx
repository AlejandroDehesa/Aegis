import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { FeedbackMessage } from "../components/FeedbackMessage";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { ROUTES } from "../constants/routes";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../hooks/useI18n";
import { getErrorMessage } from "../utils/errors";

export function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    login,
    register,
    authNotice,
    clearAuthNotice,
    isAuthenticated,
    isBootstrapping,
  } = useAuth();
  const { t } = useI18n();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const redirectTo = location.state?.from?.pathname || ROUTES.DASHBOARD;

  if (isBootstrapping) {
    return <div className="screen-center">{t("auth.validatingSession")}</div>;
  }

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    clearAuthNotice();

    try {
      if (mode === "login") {
        await login(form);
      } else {
        await register(form);
      }

      navigate(redirectTo, { replace: true });
    } catch (submitError) {
      setError(getErrorMessage(submitError, t("auth.authFallbackError")));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-panel auth-panel-highlight">
        <p className="eyebrow">Aegis</p>
        <h1>{t("auth.heroTitle")}</h1>
        <p className="auth-copy">{t("auth.heroCopy")}</p>
        <p className="auth-copy">{t("auth.heroDemoCredentials")}</p>
      </section>

      <section className="auth-panel">
        <LanguageSwitcher />

        <div className="auth-tabs">
          <button
            aria-pressed={mode === "login"}
            className={mode === "login" ? "auth-tab auth-tab-active" : "auth-tab"}
            onClick={() => setMode("login")}
            type="button"
          >
            {t("auth.tabLogin")}
          </button>
          <button
            aria-pressed={mode === "register"}
            className={mode === "register" ? "auth-tab auth-tab-active" : "auth-tab"}
            onClick={() => setMode("register")}
            type="button"
          >
            {t("auth.tabRegister")}
          </button>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>{t("auth.email")}</span>
            <input
              name="email"
              onChange={updateField}
              placeholder={t("auth.emailPlaceholder")}
              required
              type="email"
              value={form.email}
            />
          </label>

          <label className="form-field">
            <span>{t("auth.password")}</span>
            <input
              name="password"
              onChange={updateField}
              placeholder={t("auth.passwordPlaceholder")}
              required
              type="password"
              value={form.password}
            />
          </label>

          <FeedbackMessage tone="info">{authNotice}</FeedbackMessage>
          <FeedbackMessage tone="error">{error}</FeedbackMessage>

          <button className="button button-primary" disabled={loading} type="submit">
            {loading
              ? t("auth.processing")
              : mode === "login"
                ? t("auth.enterAegis")
                : t("auth.createAccount")}
          </button>
        </form>
      </section>
    </div>
  );
}
