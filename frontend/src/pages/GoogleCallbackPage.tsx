import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

export function GoogleCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState("Đang hoàn tất đăng nhập Google...");

  useEffect(() => {
    const token = searchParams.get("access_token");
    const error = searchParams.get("error");
    if (token) {
      localStorage.setItem("access_token", token);
      window.location.replace("/");
      return;
    }
    setMessage(error ? "Không thể đăng nhập bằng Google. Vui lòng thử lại." : "Thiếu mã đăng nhập Google.");
    const timeout = window.setTimeout(() => navigate("/login", { replace: true }), 2200);
    return () => window.clearTimeout(timeout);
  }, [navigate, searchParams]);

  return (
    <section className="content-narrow">
      <div className="panel auth-card">
        <h1>Google</h1>
        <p className="muted">{message}</p>
      </div>
    </section>
  );
}
