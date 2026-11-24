import { Navigate, Outlet, useLocation } from "react-router";

import { useAuth } from "./AuthContext";

export function RequireAuth() {
  const { token } = useAuth();
  const location = useLocation();

  if (token === null) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}
