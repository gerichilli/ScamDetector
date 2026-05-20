import { useMemo } from "react";
import { Link, useLocation } from "react-router-dom";

export function TrustedContactConfirmPage() {
  const { search } = useLocation();
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const status = params.get("status");
  const email = params.get("email");

  const success = status === "success";

  return (
    <section className="content-narrow">
      <div className="panel">
        <h1>{success ? "Xác nhận thành công" : "Liên kết không hợp lệ"}</h1>
        <p className={success ? "success-box" : "form-error"}>
          {success
            ? `Người liên hệ tin cậy ${email ? `(${email}) ` : ""}đã được xác nhận. Hệ thống chỉ gửi cảnh báo khi phát hiện rủi ro cao.`
            : "Liên kết xác nhận đã hết hạn hoặc không hợp lệ. Bác vui lòng yêu cầu gửi lại email xác nhận."}
        </p>
        <div className="mt-5">
          <Link className="button primary" to="/login">Quay về hệ thống</Link>
        </div>
      </div>
    </section>
  );
}
