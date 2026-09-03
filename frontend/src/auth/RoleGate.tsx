import { Navigate, Outlet } from "react-router-dom";

import type { Role } from "../types/api";
import { useAuth } from "./useAuth";

// This hides what a role cannot use. It is not a security boundary: the API
// re-authorises every call, and a user who edits their way past this gains nothing.
export default function RoleGate({ allowedRoles }: { allowedRoles: Role[] }) {
  const { currentUser } = useAuth();

  if (currentUser === null || !allowedRoles.includes(currentUser.role)) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
