import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/useAuth";

export default function HomeRedirect() {
  const { currentUser } = useAuth();

  // Accounting exists to process validated claims, so the all-reports view is
  // their working screen; everybody else starts on their own list.
  if (currentUser?.role === "ACCOUNTING") {
    return <Navigate to="/expenses/all" replace />;
  }
  return <Navigate to="/expenses" replace />;
}
