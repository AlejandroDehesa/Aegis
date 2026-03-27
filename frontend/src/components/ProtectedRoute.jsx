import { Navigate, useLocation } from "react-router-dom";

import { ROUTES } from "../constants/routes";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../hooks/useI18n";

export function ProtectedRoute({ children }) {
  const { isAuthenticated, isBootstrapping } = useAuth();
  const { t } = useI18n();
  const location = useLocation();

  if (isBootstrapping) {
    return <div className="screen-center">{t("protected.validatingSession")}</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace state={{ from: location }} />;
  }

  return children;
}
