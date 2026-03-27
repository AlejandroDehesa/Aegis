import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { FeedbackMessage } from "../components/FeedbackMessage";
import { ROUTES } from "../constants/routes";
import { useAuth } from "../hooks/useAuth";

export function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, authNotice, clearAuthNotice } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const redirectTo = location.state?.from?.pathname || ROUTES.DASHBOARD;

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
      setError(submitError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-panel auth-panel-highlight">
        <p className="eyebrow">Aegis</p>
        <h1>Task orchestration with visibility built in.</h1>
        <p className="auth-copy">
          Sign in to inspect tasks, execute pipelines, upload documents and
          review execution traces from a real interface.
        </p>
      </section>

      <section className="auth-panel">
        <div className="auth-tabs">
          <button
            className={mode === "login" ? "auth-tab auth-tab-active" : "auth-tab"}
            onClick={() => setMode("login")}
            type="button"
          >
            Login
          </button>
          <button
            className={mode === "register" ? "auth-tab auth-tab-active" : "auth-tab"}
            onClick={() => setMode("register")}
            type="button"
          >
            Register
          </button>
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>Email</span>
            <input
              name="email"
              onChange={updateField}
              placeholder="you@example.com"
              required
              type="email"
              value={form.email}
            />
          </label>

          <label className="form-field">
            <span>Password</span>
            <input
              name="password"
              onChange={updateField}
              placeholder="********"
              required
              type="password"
              value={form.password}
            />
          </label>

          <FeedbackMessage tone="info">{authNotice}</FeedbackMessage>
          {error ? <p className="form-error">{error}</p> : null}

          <button className="button button-primary" disabled={loading} type="submit">
            {loading
              ? "Working..."
              : mode === "login"
                ? "Login to Aegis"
                : "Create account"}
          </button>
        </form>
      </section>
    </div>
  );
}
