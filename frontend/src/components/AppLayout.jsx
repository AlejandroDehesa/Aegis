import { NavLink, Outlet } from "react-router-dom";

import { ROUTES } from "../constants/routes";
import { useAuth } from "../hooks/useAuth";

const NAV_ITEMS = [
  { label: "Dashboard", to: ROUTES.DASHBOARD, end: true },
  { label: "Tasks", to: ROUTES.TASKS },
  { label: "Documents", to: ROUTES.DOCUMENTS },
  { label: "Agents", to: ROUTES.AGENTS },
];

export function AppLayout() {
  const { logout, user } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <p className="eyebrow">Aegis</p>
          <h1>Task orchestration, visible.</h1>
          <p className="brand-copy">
            Frontend foundation for execution, traceability and document context.
          </p>
        </div>

        <nav className="nav-list">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              className={({ isActive }) =>
                isActive ? "nav-link nav-link-active" : "nav-link"
              }
              end={item.end}
              to={item.to}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p className="sidebar-label">Signed in as</p>
          <p className="sidebar-user">{user?.email}</p>
          <button className="button button-secondary button-full" onClick={logout} type="button">
            Logout
          </button>
        </div>
      </aside>

      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
