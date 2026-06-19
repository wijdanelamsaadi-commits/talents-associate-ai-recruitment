import { Navigate, Outlet, useLocation } from "react-router-dom";

import { getStoredCandidateToken } from "../lib/portalAuthStorage";

export function CandidateProtectedRoute() {
  const location = useLocation();

  if (!getStoredCandidateToken()) {
    return <Navigate to="/portal/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
