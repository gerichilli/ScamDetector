import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api } from "../api/client";
import type { ReportCreateResponse, RiskLevel } from "../api/types";
import { RiskBadge } from "../components/RiskBadge";
import { validateNonNegativeNumber, validatePhone, validateRequiredText } from "../utils/validation";

type PreliminaryReview = {
  riskLevel: RiskLevel;
  message: string;
  action: string;
};

const highRiskWords = ["otp", "mã xác minh", "ma xac minh", "chuyển tiền", "chuyen tien", "công an", "cong an", "khóa tài khoản", "khoa tai khoan", "rút tiền", "rut tien"];
const mediumRiskWords = ["trúng thưởng", "trung thuong", "nhận quà", "nhan qua", "phí", "phi", "đặt cọc", "dat coc", "đầu tư", "dau tu"];

function getPreliminaryReview(transcript: string): PreliminaryReview {
  const text = transcript.toLowerCase();
  if (highRiskWords.some((word) => text.includes(word))) {
    return {
      riskLevel: "high",
      message: "Tình huống có dấu hiệu nguy hiểm: người gọi nhắc đến OTP, chuyển tiền, khóa tài khoản hoặc giả danh cơ quan.",
      action: "Không đọc OTP, không chuyển tiền, không cung cấp thông tin cá nhân. Hãy dừng lại và xác minh qua kênh chính thức.",
    };
  }
  if (mediumRiskWords.some((word) => text.includes(word))) {
    return {
      riskLevel: "medium",
      message: "Tình huống có dấu hiệu đáng nghi: có yếu tố quà tặng, phí, đặt cọc hoặc đầu tư.",
      action: "Không vội làm theo yêu cầu. Hãy hỏi người thân hoặc kiểm tra lại nguồn liên hệ trước.",
    };
  }
  return {
    riskLevel: "low",
    message: "Chưa thấy dấu hiệu lừa đảo rõ ràng từ nội dung đã nhập.",
    action: "Vẫn nên cẩn thận, không chia sẻ OTP, mật khẩu hoặc thông tin ngân hàng qua điện thoại.",
  };
}

export function ReportPage() {
  const [result, setResult] = useState<ReportCreateResponse | null>(null);
  const [preliminaryReview, setPreliminaryReview] = useState<PreliminaryReview | null>(null);
  const [formError, setFormError] = useState("");
  const mutation = useMutation({
    mutationFn: async (form: HTMLFormElement) => {
      const data = new FormData(form);
      const phoneNumber = String(data.get("phone_number") || "").trim();
      const transcript = String(data.get("transcript") || "").trim();
      const note = String(data.get("note") || "").trim();
      const duration = String(data.get("duration_seconds") || "").trim();
      const reportData = new FormData();
      reportData.set("entity_type", "phone");
      reportData.set("entity_value", phoneNumber);
      reportData.set("scam_type", note || "Cuộc gọi đáng nghi");
      reportData.set("title", `Báo cáo cuộc gọi từ ${phoneNumber}`);
      reportData.set(
        "description",
        [
          transcript,
          note ? `Ghi chú: ${note}` : "",
          duration ? `Thời lượng: ${duration} giây` : "",
        ].filter(Boolean).join("\n\n"),
      );
      const response = await api.post<ReportCreateResponse>("/reports", reportData);
      return response.data;
    },
    onSuccess: (data) => setResult(data),
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setResult(null);
    setPreliminaryReview(null);
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
    const transcriptValidation = validateRequiredText(String(data.get("transcript") || ""), "Nội dung cuộc gọi", 10);
    if (!transcriptValidation.valid) {
      setFormError(transcriptValidation.message ?? "Nội dung cuộc gọi cần tối thiểu 10 ký tự.");
      return;
    }
    setPreliminaryReview(getPreliminaryReview(String(data.get("transcript") || "")));
    mutation.mutate(event.currentTarget);
  }

  return (
    <section className="content-narrow">
      <form className="panel form-grid" onSubmit={submit} noValidate>
        <h1>Báo cáo cuộc gọi nghi ngờ</h1>
        <p className="muted">
          Báo cáo sẽ chuyển vào hàng chờ quản trị. Chỉ khi admin duyệt, số điện thoại này mới vào dữ liệu scam chính thức.
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
        {result && preliminaryReview && (
          <div className={`call-alert-result call-alert-risk-${preliminaryReview.riskLevel}`}>
            <div className="result-header">
              <div>
                <span className="eyebrow">Đã gửi báo cáo</span>
                <h2>Đánh giá sơ bộ</h2>
              </div>
              <RiskBadge level={preliminaryReview.riskLevel} />
            </div>
            <p>{preliminaryReview.message}</p>
            <p>
              <strong>Bác nên làm: </strong>
              {preliminaryReview.action}
            </p>
            <p>
              <strong>Trạng thái báo cáo: </strong>
              Đang chờ admin duyệt. Sau khi admin duyệt, dữ liệu này mới xuất hiện trong tra cứu chính thức.
            </p>
          </div>
        )}
        <button className="button primary" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Đang gửi" : "Gửi báo cáo chờ duyệt"}
        </button>
      </form>
    </section>
  );
}
