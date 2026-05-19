import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api } from "../api/client";
import type { Page, ReportListItem, RiskLevel } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { validatePhone, validateRequiredText } from "../utils/validation";

type ScamDatabaseEntry = {
  id: string;
  phone_number: string | null;
  pattern: string;
  description: string;
  risk_level: RiskLevel;
  updated_at: string;
};

export function AdminPage() {
  const client = useQueryClient();
  const [entryError, setEntryError] = useState("");
  const reports = useQuery({
    queryKey: ["admin-reports"],
    queryFn: async () => (await api.get<Page<ReportListItem>>("/admin/reports", { params: { status: "pending" } })).data,
  });
  const scamDatabase = useQuery({
    queryKey: ["scam-database"],
    queryFn: async () => (await api.get<Page<ScamDatabaseEntry>>("/scam-database")).data,
  });
  const moderate = useMutation({
    mutationFn: async ({ id, status, riskLevel }: { id: string; status: string; riskLevel?: RiskLevel }) =>
      api.patch(`/admin/reports/${id}/moderate`, { status, risk_level: riskLevel }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["admin-reports"] }),
  });
  const createEntry = useMutation({
    mutationFn: async (form: HTMLFormElement) => {
      const data = new FormData(form);
      return api.post("/scam-database", {
        phone_number: data.get("phone_number") || null,
        pattern: data.get("pattern"),
        description: data.get("description"),
        risk_level: data.get("risk_level"),
      });
    },
    onSuccess: (_, form) => {
      form.reset();
      setEntryError("");
      client.invalidateQueries({ queryKey: ["scam-database"] });
    },
  });

  function submitEntry(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEntryError("");
    const data = new FormData(event.currentTarget);
    const phoneNumber = String(data.get("phone_number") || "").trim();
    if (phoneNumber) {
      const phoneValidation = validatePhone(phoneNumber, "Số điện thoại nghi ngờ");
      if (!phoneValidation.valid) {
        setEntryError(phoneValidation.message ?? "Số điện thoại không hợp lệ.");
        return;
      }
    }
    const patternValidation = validateRequiredText(String(data.get("pattern") || ""), "Kiểu lừa đảo", 2);
    if (!patternValidation.valid) {
      setEntryError(patternValidation.message ?? "Kiểu lừa đảo không hợp lệ.");
      return;
    }
    const descriptionValidation = validateRequiredText(String(data.get("description") || ""), "Mô tả", 5);
    if (!descriptionValidation.valid) {
      setEntryError(descriptionValidation.message ?? "Mô tả không hợp lệ.");
      return;
    }
    createEntry.mutate(event.currentTarget);
  }

  return (
    <section className="admin-layout">
      <div className="panel">
        <h1>Quản trị dữ liệu lừa đảo</h1>
        <form className="form-grid" onSubmit={submitEntry} noValidate>
          <label>Số điện thoại nghi ngờ<input name="phone_number" placeholder="Có thể bỏ trống nếu chỉ thêm mẫu lừa đảo" /></label>
          <label>Kiểu lừa đảo<input name="pattern" placeholder="VD: Giả danh ngân hàng xin mã OTP" aria-invalid={!!entryError} /></label>
          <label>Mô tả dễ hiểu<textarea name="description" rows={4} aria-invalid={!!entryError} /></label>
          <label>Mức rủi ro
            <select name="risk_level" defaultValue="medium">
              <option value="low">Thấp</option>
              <option value="medium">Đáng nghi</option>
              <option value="high">Cao</option>
              <option value="critical">Rất nguy hiểm</option>
            </select>
          </label>
          {entryError && <div className="form-error">{entryError}</div>}
          {createEntry.isError && <div className="form-error">Không thể thêm dữ liệu lừa đảo.</div>}
          <button className="button primary" type="submit" disabled={createEntry.isPending}>
            {createEntry.isPending ? "Đang lưu" : "Thêm vào kho dữ liệu"}
          </button>
        </form>
      </div>

      <div className="panel">
        <h2>Kho dữ liệu lừa đảo</h2>
        {!scamDatabase.isLoading && !scamDatabase.data?.items.length && <EmptyState title="Chưa có dữ liệu lừa đảo" />}
        {!!scamDatabase.data?.items.length && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Số điện thoại</th>
                  <th>Kiểu lừa đảo</th>
                  <th>Mức rủi ro</th>
                  <th>Cập nhật</th>
                </tr>
              </thead>
              <tbody>
                {scamDatabase.data.items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.phone_number || "Không áp dụng"}</td>
                    <td>{item.pattern}</td>
                    <td>{item.risk_level}</td>
                    <td>{new Date(item.updated_at).toLocaleString("vi-VN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="panel">
        <h2>Báo cáo cũ đang chờ duyệt</h2>
        {!reports.isLoading && !reports.data?.items.length && <EmptyState title="Không có báo cáo đang chờ duyệt" />}
        {!!reports.data?.items.length && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Đối tượng</th>
                  <th>Loại lừa đảo</th>
                  <th>Ngày gửi</th>
                  <th>Duyệt</th>
                </tr>
              </thead>
              <tbody>
                {reports.data.items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.entity_type}: {item.entity_value}</td>
                    <td>{item.scam_type}</td>
                    <td>{new Date(item.created_at).toLocaleString("vi-VN")}</td>
                    <td className="actions-cell">
                      <button className="button small primary" onClick={() => moderate.mutate({ id: item.id, status: "approved", riskLevel: "high" })}>
                        Duyệt
                      </button>
                      <button className="button small ghost" onClick={() => moderate.mutate({ id: item.id, status: "rejected" })}>
                        Từ chối
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
