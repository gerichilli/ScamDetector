import { useMutation } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { FormEvent, useState } from "react";
import { api } from "../api/client";
import type { LookupResponse } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { RiskBadge } from "../components/RiskBadge";
import { validateLookupValue } from "../utils/validation";

const entityTypeLabels: Record<string, string> = {
  phone: "Số điện thoại",
  bank_account: "Tài khoản ngân hàng",
  e_wallet: "Ví điện tử",
  social_account: "Tài khoản mạng xã hội",
};

const statusLabels: Record<string, string> = {
  active: "Đang có cảnh báo",
  under_review: "Đang xem xét",
  cleared: "Đã xác minh an toàn",
  blocked: "Đã khóa",
};

const scamTypeLabels: Record<string, string> = {
  bank_transfer: "Chuyển khoản nhận tiền rồi biến mất",
  fake_seller: "Bán hàng giả hoặc không giao hàng",
  fake_job: "Việc làm giả, bắt đóng phí trước",
  investment: "Đầu tư lợi nhuận cao bất thường",
  impersonation: "Giả danh người quen hoặc cơ quan",
  "Thông báo trúng thưởng, yêu cầu đóng phí": "Thông báo trúng thưởng, yêu cầu đóng phí",
  "Giả danh ngân hàng xin mã OTP": "Giả danh ngân hàng xin mã OTP",
  "Giả danh công an, dọa liên quan vụ án": "Giả danh công an, dọa liên quan vụ án",
  "Mời đầu tư lợi nhuận cao": "Mời đầu tư lợi nhuận cao",
};

export function LookupPage() {
  const [type, setType] = useState("phone");
  const [value, setValue] = useState("");
  const [formError, setFormError] = useState("");

  const lookup = useMutation({
    mutationFn: async () => {
      const response = await api.get<LookupResponse>("/lookup", { params: { type, value: value.trim() } });
      return response.data;
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError("");
    const validation = validateLookupValue(type, value);
    if (!validation.valid) {
      setFormError(validation.message ?? "Dữ liệu tra cứu không hợp lệ.");
      return;
    }
    lookup.mutate();
  }

  return (
    <section className="page-grid">
      <div className="panel lookup-panel">
        <h1>Tra cứu cảnh báo lừa đảo</h1>
        <p className="muted">Kiểm tra nhanh số điện thoại, tài khoản ngân hàng, ví điện tử hoặc tài khoản mạng xã hội.</p>
        <form className="lookup-form" onSubmit={onSubmit} noValidate>
          <label>
            Loại đối tượng
            <select
              value={type}
              onChange={(event) => {
                setType(event.target.value);
                setFormError("");
              }}
            >
              <option value="phone">Số điện thoại</option>
              <option value="bank_account">Tài khoản ngân hàng</option>
              <option value="e_wallet">Ví điện tử</option>
              <option value="social_account">Tài khoản xã hội</option>
            </select>
          </label>
          <label>
            Giá trị cần tra cứu
            <input
              value={value}
              onChange={(event) => {
                setValue(event.target.value);
                setFormError("");
              }}
              placeholder="VD: 0987654321"
              aria-invalid={!!formError}
            />
          </label>
          {formError && <div className="form-error">{formError}</div>}
          {lookup.isError && <div className="form-error">Không thể tra cứu ngay bây giờ. Vui lòng thử lại sau.</div>}
          <button className="button primary" type="submit" disabled={lookup.isPending}>
            <Search size={18} />
            {lookup.isPending ? "Đang tra cứu" : "Tra cứu"}
          </button>
        </form>
      </div>

      <div className="panel result-panel">
        {!lookup.data && <EmptyState title="Chưa có kết quả" description="Nhập thông tin bên trái để kiểm tra cảnh báo." />}
        {lookup.data && !lookup.data.found && (
          <EmptyState title="Chưa tìm thấy cảnh báo" description="Không có bản ghi lừa đảo đã biết cho truy vấn này." />
        )}
        {lookup.data?.found && lookup.data.entity && (
          <div className={`result-card lookup-risk-${lookup.data.entity.risk_level}`}>
            <div className="result-header">
              <div>
                <span className="eyebrow">{entityTypeLabels[lookup.data.entity.entity_type] ?? lookup.data.entity.entity_type}</span>
                <h2>{lookup.data.entity.value}</h2>
              </div>
              <RiskBadge level={lookup.data.entity.risk_level} />
            </div>
            <div className="metric-grid">
              <div><span>Báo cáo</span><strong>{lookup.data.entity.report_count}</strong></div>
              <div><span>Đã duyệt</span><strong>{lookup.data.entity.verified_report_count}</strong></div>
              <div className={`status-card status-${lookup.data.entity.status}`}>
                <span>Trạng thái</span>
                <strong>{statusLabels[lookup.data.entity.status] ?? "Chưa rõ"}</strong>
              </div>
            </div>
            <h3>Loại lừa đảo phổ biến</h3>
            <div className="tag-row">
              {lookup.data.summary?.top_scam_types.length ? lookup.data.summary.top_scam_types.map((item) => (
                <span className="tag" key={item.scam_type}>{scamTypeLabels[item.scam_type] ?? item.scam_type}: {item.count}</span>
              )) : <span className="muted">Chưa có báo cáo đã duyệt.</span>}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
