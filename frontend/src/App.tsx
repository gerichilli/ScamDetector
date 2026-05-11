import { Link, NavLink, Outlet } from "react-router-dom";
import { LogOut, ShieldAlert } from "lucide-react";
import { useAuth } from "./state/auth";
import { ChatbotWidget } from "./components/ChatbotWidget";

export function App() {
  const { user, logout } = useAuth();

  return (
    <div className="app">
      <header className="topbar">
        <Link className="brand" to="/">
          <ShieldAlert size={24} />
          <span>Cảnh báo lừa đảo</span>
        </Link>
        <nav className="nav">
          <NavLink to="/">Tra cứu</NavLink>
          <NavLink to="/stats">Thống kê</NavLink>
          {user && <NavLink to="/report">Báo cáo cuộc gọi</NavLink>}
          {user && <NavLink to="/history">Lịch sử cuộc gọi</NavLink>}
          {user && ["admin", "moderator"].includes(user.role) && <NavLink to="/admin">Quản trị</NavLink>}
        </nav>
        <div className="auth-actions">
          {user ? (
            <>
              <Link to="/profile" className="user-chip">{user.email}</Link>
              <button className="icon-button" onClick={logout} title="Đăng xuất">
                <LogOut size={18} />
              </button>
            </>
          ) : (
            <>
              <Link className="button ghost" to="/login">Đăng nhập</Link>
              <Link className="button primary" to="/register">Đăng ký</Link>
            </>
          )}
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <ChatbotWidget />
    </div>
  );
}
