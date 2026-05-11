import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../state/auth";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await register(email, password, fullName);
      navigate("/");
    } catch {
      setError("Không thể đăng ký. Kiểm tra email hoặc mật khẩu tối thiểu 8 ký tự.");
    }
  }

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={submit}>
        <h1>Đăng ký</h1>
        <label>Họ tên<input value={fullName} onChange={(event) => setFullName(event.target.value)} /></label>
        <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label>Mật khẩu<input type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        {error && <div className="form-error">{error}</div>}
        <button className="button primary" type="submit">Tạo tài khoản</button>
        <p className="muted">Đã có tài khoản? <Link to="/login">Đăng nhập</Link></p>
      </form>
    </div>
  );
}
