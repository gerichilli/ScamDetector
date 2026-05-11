import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { CallReportItem, Page } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { RiskBadge } from "../components/RiskBadge";

export function HistoryPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["call-history"],
    queryFn: async () => (await api.get<Page<CallReportItem>>("/alerts/calls/my")).data,
  });

  return (
    <section className="panel">
      <h1>Lịch sử cuộc gọi</h1>
      <p className="muted">
        Mỗi mục bên dưới gồm thông tin cuộc gọi bác đã báo và lời nhắc của hệ thống. Bác chỉ cần xem một chỗ này là đủ ạ.
      </p>
      {isLoading && <p className="muted">Đang tải...</p>}
      {!isLoading && !data?.items.length && <EmptyState title="Chưa có cuộc gọi nào được ghi nhận" />}
      {!!data?.items.length && (
        <div className="combined-history-grid">
          {data.items.map((item) => (
            <article className={`combined-history-card history-risk-${item.risk_level}`} key={item.call_id}>
              <div className="result-header">
                <div>
                  <span className="eyebrow">Số gọi đến</span>
                  <h2>{item.phone_number}</h2>
                </div>
                <RiskBadge level={item.risk_level} />
              </div>

              <section className="history-section">
                <h3>Cuộc gọi bác đã báo</h3>
                <div className="call-report-meta">
                  <span>{new Date(item.call_time).toLocaleString("vi-VN")}</span>
                  <span>{item.duration_seconds ? `${item.duration_seconds} giây` : "Chưa nhập thời lượng"}</span>
                  <span>{item.status}</span>
                </div>
                <div className="history-text-box">
                  <strong>Nội dung bác đã ghi lại</strong>
                  <p>{item.transcript || "Bác chưa nhập nội dung cuộc gọi."}</p>
                </div>
                {item.note && (
                  <div className="history-text-box">
                    <strong>Ghi chú của bác</strong>
                    <p>{item.note}</p>
                  </div>
                )}
              </section>

              <section className="history-section system-suggestion">
                <h3>Cảnh báo của hệ thống</h3>
                <p>{item.message}</p>
                <p>
                  <strong>Bác nên làm: </strong>
                  {item.recommended_action}
                </p>
              </section>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
