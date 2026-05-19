import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { App } from "./App";
import "@fontsource/lexend/400.css";
import "@fontsource/lexend/500.css";
import "@fontsource/lexend/600.css";
import "@fontsource/lexend/700.css";
import "@fontsource/lexend/800.css";
import "@fontsource/lexend/900.css";
import { AuthProvider, useAuth } from "./state/auth";
import { AdminPage } from "./pages/AdminPage";
import { GoogleCallbackPage } from "./pages/GoogleCallbackPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LoginPage } from "./pages/LoginPage";
import { LookupPage } from "./pages/LookupPage";
import { ProfilePage } from "./pages/ProfilePage";
import { RegisterPage } from "./pages/RegisterPage";
import { ReportPage } from "./pages/ReportPage";
import { StatsPage } from "./pages/StatsPage";
import "./styles.css";

const queryClient = new QueryClient();

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page-note">Đang kiểm tra phiên đăng nhập...</div>;
  return user ? children : <Navigate to="/login" replace />;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page-note">Đang kiểm tra quyền truy cập...</div>;
  return user && ["admin", "moderator"].includes(user.role) ? children : <Navigate to="/" replace />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<App />}>
              <Route path="/" element={<LookupPage />} />
              <Route path="/stats" element={<StatsPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />
              <Route
                path="/report"
                element={
                  <PrivateRoute>
                    <ReportPage />
                  </PrivateRoute>
                }
              />
              <Route
                path="/my-reports"
                element={
                  <PrivateRoute>
                    <Navigate to="/history" replace />
                  </PrivateRoute>
                }
              />
              <Route
                path="/history"
                element={
                  <PrivateRoute>
                    <HistoryPage />
                  </PrivateRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <PrivateRoute>
                    <ProfilePage />
                  </PrivateRoute>
                }
              />
              <Route
                path="/admin"
                element={
                  <AdminRoute>
                    <AdminPage />
                  </AdminRoute>
                }
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
