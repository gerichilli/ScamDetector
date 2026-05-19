import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../api/client";
import { useAuth } from "../state/auth";
import { validateEmailOrPhone } from "../utils/validation";

type LoginField = "email" | "password" | "form";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [errorField, setErrorField] = useState<LoginField | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setErrorField(null);
    const trimmedIdentifier = identifier.trim();
    const identifierValidation = validateEmailOrPhone(trimmedIdentifier);
    if (!identifierValidation.valid) {
      setError(identifierValidation.message ?? "Vui lòng nhập email hoặc số điện thoại hợp lệ.");
      setErrorField("email");
      return;
    }
    if (!password.trim()) {
      setError("Vui lòng nhập mật khẩu.");
      setErrorField("password");
      return;
    }
    try {
      await login(trimmedIdentifier, password);
      navigate("/");
    } catch {
      setError("Email/số điện thoại hoặc mật khẩu không đúng.");
      setErrorField("form");
    }
  }

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={submit} noValidate>
        <h1>Đăng nhập</h1>
        <label>Email hoặc số điện thoại<input type="text" inputMode="text" value={identifier} onChange={(event) => {
          setIdentifier(event.target.value);
          if (errorField === "email") setErrorField(null);
        }} aria-invalid={errorField === "email"} /></label>
        <label>Mật khẩu<input type="password" value={password} onChange={(event) => {
          setPassword(event.target.value);
          if (errorField === "password") setErrorField(null);
        }} aria-invalid={errorField === "password"} /></label>
        {error && <div className="form-error">{error}</div>}
        <button className="button primary" type="submit">Đăng nhập</button>
        <div className="auth-divider"><span>hoặc</span></div>
        <a className="button ghost google-button" href={`${API_BASE_URL}/auth/google/login`}>
          <span className="google-mark">G</span>
          Tiếp tục với Google
        </a>
        <p className="muted">Chưa có tài khoản? <Link to="/register">Đăng ký</Link></p>
      </form>
    </div>
  );
}
