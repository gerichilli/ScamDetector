import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../state/auth";
import { isValidEmail } from "../utils/validation";

type LoginField = "email" | "password" | "form";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [errorField, setErrorField] = useState<LoginField | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setErrorField(null);
    const trimmedEmail = email.trim();
    if (!isValidEmail(trimmedEmail)) {
      setError("Vui lòng nhập đúng định dạng email.");
      setErrorField("email");
      return;
    }
    if (!password.trim()) {
      setError("Vui lòng nhập mật khẩu.");
      setErrorField("password");
      return;
    }
    try {
      await login(trimmedEmail, password);
      navigate("/");
    } catch {
      setError("Email hoặc mật khẩu không đúng.");
      setErrorField("form");
    }
  }

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={submit} noValidate>
        <h1>Đăng nhập</h1>
        <label>Email<input type="text" inputMode="email" value={email} onChange={(event) => {
          setEmail(event.target.value);
          if (errorField === "email") setErrorField(null);
        }} aria-invalid={errorField === "email"} /></label>
        <label>Mật khẩu<input type="password" value={password} onChange={(event) => {
          setPassword(event.target.value);
          if (errorField === "password") setErrorField(null);
        }} aria-invalid={errorField === "password"} /></label>
        {error && <div className="form-error">{error}</div>}
        <button className="button primary" type="submit">Đăng nhập</button>
        <p className="muted">Chưa có tài khoản? <Link to="/register">Đăng ký</Link></p>
      </form>
    </div>
  );
}
