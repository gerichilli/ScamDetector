import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { CallReportItem, Page } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { RiskBadge } from "../components/RiskBadge";

export function MyReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["my-call-reports"],
    queryFn: async () => (await api.get<Page<CallReportItem>>("/alerts/calls/my")).data,
  });

  return (
    <section className="panel">
      <h1>Cuộc gọi đã báo</h1>
      <p className="muted">
        Đây là danh sách những cuộc gọi bác đã nhập vào hệ thống, gồm số điện thoại, nội dung bác ghi lại và trạng thái xử lý.
      </p>
      {isLoading && <p className="muted">Đang tải...</p>}
      {!isLoading && !data?.items.length && <EmptyState title="Bạn chưa báo cáo cuộc gọi nào" />}
      {!!data?.items.length && (
        <div className="call-report-grid">
          {data.items.map((item) => (
            <article className="call-report-card" key={item.call_id}>
              <div className="result-header">
                <div>
                  <span className="eyebrow">Số bác đã báo</span>
                  <h2>{item.phone_number}</h2>
                </div>
                <RiskBadge level={item.risk_level} />
              </div>
              <div className="call-report-meta">
                <span>{new Date(item.call_time).toLocaleString("vi-VN")}</span>
                <span>{item.duration_seconds ? `${item.duration_seconds} giây` : "Chưa nhập thời lượng"}</span>
                <span>{item.status}</span>
              </div>
              <div>
                <strong>Nội dung bác đã ghi lại</strong>
                <p>{item.transcript || "Bác chưa nhập nội dung cuộc gọi."}</p>
              </div>
              {item.note && (
                <div>
                  <strong>Ghi chú của bác</strong>
                  <p>{item.note}</p>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
