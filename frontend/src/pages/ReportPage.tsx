import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api } from "../api/client";
import type { CallAlertResponse } from "../api/types";
import { RiskBadge } from "../components/RiskBadge";
import { validateNonNegativeNumber, validatePhone } from "../utils/validation";

export function ReportPage() {
  const [result, setResult] = useState<CallAlertResponse | null>(null);
  const [formError, setFormError] = useState("");
  const mutation = useMutation({
    mutationFn: async (form: HTMLFormElement) => {
      const data = new FormData(form);
      const payload = {
        phone_number: String(data.get("phone_number") || ""),
        duration_seconds: data.get("duration_seconds") ? Number(data.get("duration_seconds")) : null,
        transcript: String(data.get("transcript") || ""),
        note: String(data.get("note") || ""),
      };
      const response = await api.post<CallAlertResponse>("/alerts/calls", payload);
      return response.data;
    },
    onSuccess: (data) => setResult(data),
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setResult(null);
    setFormError("");
    const data = new FormData(event.currentTarget);
    const phoneValidation = validatePhone(String(data.get("phone_number") || ""), "Số điện thoại gọi đến");
    if (!phoneValidation.valid) {
      setFormError(phoneValidation.message ?? "Số điện thoại không hợp lệ.");
      return;
    }
    const durationValidation = validateNonNegativeNumber(String(data.get("duration_seconds") || ""), "Thời lượng cuộc gọi");
    if (!durationValidation.valid) {
      setFormError(durationValidation.message ?? "Thời lượng cuộc gọi không hợp lệ.");
      return;
    }
    mutation.mutate(event.currentTarget);
  }

  return (
    <section className="content-narrow">
      <form className="panel form-grid" onSubmit={submit} noValidate>
        <h1>Báo cáo cuộc gọi nghi ngờ</h1>
        <p className="muted">
          Nhập số điện thoại và nội dung chính của cuộc gọi. Hệ thống sẽ tạo cảnh báo để bạn xem lại và rút kinh nghiệm.
        </p>
        <label>
          Số điện thoại gọi đến
          <input name="phone_number" placeholder="VD: 0987654321" aria-invalid={!!formError} />
        </label>
        <label>
          Thời lượng cuộc gọi, tính bằng giây
          <input name="duration_seconds" type="text" inputMode="numeric" placeholder="VD: 120" aria-invalid={!!formError} />
        </label>
        <label>
          Người gọi đã nói gì?
          <textarea
            name="transcript"
            rows={6}
            placeholder="VD: Người gọi tự xưng là ngân hàng, yêu cầu đọc mã OTP hoặc chuyển tiền..."
          />
        </label>
        <label>
          Ghi chú thêm
          <textarea name="note" rows={3} placeholder="VD: Người gọi nói rất gấp, không cho tôi hỏi người thân." />
        </label>
        {formError && <div className="form-error">{formError}</div>}
        {mutation.isError && <div className="form-error">Không thể gửi báo cáo cuộc gọi.</div>}
        {result && (
          <div className={`call-alert-result call-alert-risk-${result.risk_level}`}>
            <div className="result-header">
              <div>
                <span className="eyebrow">Kết quả cảnh báo</span>
                <h2>{result.phone_number}</h2>
              </div>
              <RiskBadge level={result.risk_level} />
            </div>
            <p>{result.message}</p>
            <p>
              <strong>Bác nên làm: </strong>
              {result.recommended_action}
            </p>
          </div>
        )}
        <button className="button primary" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Đang kiểm tra" : "Gửi và tạo cảnh báo"}
        </button>
      </form>
    </section>
  );
}
