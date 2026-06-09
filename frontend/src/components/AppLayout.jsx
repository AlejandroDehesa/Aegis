import { NavLink, Outlet } from "react-router-dom";

import { LanguageSwitcher } from "./LanguageSwitcher";
import { ROUTES } from "../constants/routes";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../hooks/useI18n";

export function AppLayout() {
  const { logout, user } = useAuth();
  const { t } = useI18n();

  const navItems = [
    { label: t("layout.nav.dashboard"), to: ROUTES.DASHBOARD, end: true },
    { label: t("layout.nav.insights"), to: ROUTES.INSIGHTS },
    { label: t("layout.nav.tasks"), to: ROUTES.TASKS },
    { label: t("layout.nav.documents"), to: ROUTES.DOCUMENTS },
    { label: t("layout.nav.agents"), to: ROUTES.AGENTS },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <p className="eyebrow">Aegis</p>
          <h1>{t("layout.brandTitle")}</h1>
          <p className="brand-copy">{t("layout.brandCopy")}</p>
          <LanguageSwitcher compact />
        </div>

        <div className="sidebar-callout">
          <p className="sidebar-label">{t("layout.demoPath")}</p>
          <p className="sidebar-callout-copy">{t("layout.demoPathCopy")}</p>
        </div>

        <nav aria-label={t("layout.primaryNav")} className="nav-list">
          {navItems.map((item) => (
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
          <p className="sidebar-label">{t("layout.signedInAs")}</p>
          <p className="sidebar-user">{user?.email}</p>
          <button className="button button-secondary button-full" onClick={logout} type="button">
            {t("layout.logout")}
          </button>
        </div>
      </aside>

      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
