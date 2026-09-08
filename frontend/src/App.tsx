import { Route, Routes } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import ProtectedRoute from "./auth/ProtectedRoute";
import RoleGate from "./auth/RoleGate";
import AppLayout from "./components/AppLayout";
import ActivatePage from "./pages/ActivatePage";
import AllReportsPage from "./pages/AllReportsPage";
import HomeRedirect from "./pages/HomeRedirect";
import LoginPage from "./pages/LoginPage";
import MyReportsPage from "./pages/MyReportsPage";
import NewReportPage from "./pages/NewReportPage";
import NewUserPage from "./pages/NewUserPage";
import ProfilePage from "./pages/ProfilePage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/activate" element={<ActivatePage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomeRedirect />} />
            <Route path="/expenses" element={<MyReportsPage />} />
            <Route path="/expenses/new" element={<NewReportPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route element={<RoleGate allowedRoles={["MANAGER", "ACCOUNTING"]} />}>
              <Route path="/expenses/all" element={<AllReportsPage />} />
            </Route>
            <Route element={<RoleGate allowedRoles={["MANAGER"]} />}>
              <Route path="/users/new" element={<NewUserPage />} />
            </Route>
          </Route>
        </Route>
        {/* Without this an unknown path matches nothing and React Router renders a
            blank page, which reads as a broken application rather than a wrong URL. */}
        <Route path="*" element={<HomeRedirect />} />
      </Routes>
    </AuthProvider>
  );
}
