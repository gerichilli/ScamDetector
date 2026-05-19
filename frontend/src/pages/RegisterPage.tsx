import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../state/auth";
import { isValidEmail } from "../utils/validation";

type RegisterField = "fullName" | "email" | "password" | "form";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [errorField, setErrorField] = useState<RegisterField | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setErrorField(null);
    const trimmedEmail = email.trim();
    const trimmedName = fullName.trim();
    if (!isValidEmail(trimmedEmail)) {
      setError("Vui lòng nhập đúng định dạng email.");
      setErrorField("email");
      return;
    }
    if (password.length < 8) {
      setError("Mật khẩu cần tối thiểu 8 ký tự.");
      setErrorField("password");
      return;
    }
    if (trimmedName.length > 255) {
      setError("Họ tên không được vượt quá 255 ký tự.");
      setErrorField("fullName");
      return;
    }
    try {
      await register(trimmedEmail, password, trimmedName);
      navigate("/");
    } catch {
      setError("Không thể đăng ký. Kiểm tra email hoặc mật khẩu tối thiểu 8 ký tự.");
      setErrorField("form");
    }
  }

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={submit} noValidate>
        <h1>Đăng ký</h1>
        <label>Họ tên<input value={fullName} onChange={(event) => {
          setFullName(event.target.value);
          if (errorField === "fullName") setErrorField(null);
        }} aria-invalid={errorField === "fullName"} /></label>
        <label>Email<input type="text" inputMode="email" value={email} onChange={(event) => {
          setEmail(event.target.value);
          if (errorField === "email") setErrorField(null);
        }} aria-invalid={errorField === "email"} /></label>
        <label>Mật khẩu<input type="password" value={password} onChange={(event) => {
          setPassword(event.target.value);
          if (errorField === "password") setErrorField(null);
        }} aria-invalid={errorField === "password"} /></label>
        {error && <div className="form-error">{error}</div>}
        <button className="button primary" type="submit">Tạo tài khoản</button>
        <p className="muted">Đã có tài khoản? <Link to="/login">Đăng nhập</Link></p>
      </form>
    </div>
  );
}
