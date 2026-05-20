import { FormEvent, useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { TrustedContact } from "../api/types";
import { useAuth } from "../state/auth";

const userStatusLabels: Record<string, string> = {
  active: "Đang hoạt động",
  blocked: "Đã khóa",
};

const roleLabels: Record<string, string> = {
  user: "Người dùng",
  moderator: "Người kiểm duyệt",
  admin: "Quản trị viên",
};

export function ProfilePage() {
  const { user } = useAuth();
  const [contacts, setContacts] = useState<TrustedContact[]>([]);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function loadContacts() {
    setLoading(true);
    try {
      const response = await api.get<TrustedContact[]>("/trusted-contacts");
      setContacts(response.data);
    } catch {
      setError("Không thể tải danh sách người liên hệ tin cậy.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadContacts();
  }, []);

  const pendingCount = useMemo(() => contacts.filter((item) => item.status === "pending").length, [contacts]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const response = await api.post<TrustedContact>("/trusted-contacts", {
        full_name: fullName,
        email,
        phone_number: phoneNumber || null,
      });
      setContacts((current) => [response.data, ...current]);
      setFullName("");
      setEmail("");
      setPhoneNumber("");
      setNotice(
        response.data.confirmation_preview_url
          ? "Đã tạo liên hệ. Chưa cấu hình SMTP, vui lòng dùng liên kết xác nhận demo bên dưới."
          : "Đã tạo liên hệ và gửi email xác nhận."
      );
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Không thể thêm người liên hệ tin cậy.");
    } finally {
      setSaving(false);
    }
  }

  async function resendConfirmation(contactId: string) {
    setError(null);
    setNotice(null);
    try {
      const response = await api.post<TrustedContact>(`/trusted-contacts/${contactId}/resend-confirmation`);
      setContacts((current) => current.map((item) => (item.id === contactId ? response.data : item)));
      setNotice(
        response.data.confirmation_preview_url
          ? "Đã tạo lại liên kết xác nhận demo."
          : "Đã gửi lại email xác nhận."
      );
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Không thể gửi lại email xác nhận.");
    }
  }

  async function removeContact(contactId: string) {
    setError(null);
    setNotice(null);
    try {
      await api.delete(`/trusted-contacts/${contactId}`);
      setContacts((current) => current.filter((item) => item.id !== contactId));
      setNotice("Đã xóa người liên hệ tin cậy.");
    } catch {
      setError("Không thể xóa người liên hệ tin cậy.");
    }
  }

  return (
    <section className="content-narrow">
      <div className="panel">
        <h1>Tài khoản</h1>
        <div className="detail-list">
          <div><span>Email</span><strong>{user?.email || "Chưa cập nhật"}</strong></div>
          <div><span>Số điện thoại</span><strong>{user?.phone_number || "Chưa cập nhật"}</strong></div>
          <div><span>Họ tên</span><strong>{user?.full_name || "Chưa cập nhật"}</strong></div>
          <div><span>Vai trò</span><strong>{user?.role ? roleLabels[user.role] ?? user.role : ""}</strong></div>
          <div><span>Trạng thái</span><strong>{user?.status ? userStatusLabels[user.status] ?? "Chưa rõ" : ""}</strong></div>
        </div>
      </div>

      <div className="panel mt-6">
        <h2>Người liên hệ tin cậy</h2>
        <p className="muted">
          Hệ thống chỉ gửi cảnh báo cho người thân sau khi email đã được xác nhận.
          {pendingCount > 0 ? ` Hiện có ${pendingCount} liên hệ đang chờ xác nhận.` : ""}
        </p>

        {error && <div className="form-error mt-4">{error}</div>}
        {notice && <div className="success-box mt-4">{notice}</div>}

        <form className="form-grid mt-5" onSubmit={handleSubmit}>
          <label>
            Họ tên
            <input value={fullName} onChange={(event) => setFullName(event.target.value)} required />
          </label>
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label>
            Số điện thoại
            <input value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} placeholder="Không bắt buộc" />
          </label>
          <button className="button primary" type="submit" disabled={saving}>
            {saving ? "Đang lưu..." : "Thêm liên hệ"}
          </button>
        </form>

        <div className="mt-8 grid gap-4">
          {loading ? (
            <div className="page-note">Đang tải danh sách liên hệ...</div>
          ) : contacts.length === 0 ? (
            <div className="empty-state">
              <strong>Chưa có người liên hệ tin cậy</strong>
              <span>Thêm ít nhất một liên hệ để gửi cảnh báo khi có rủi ro cao.</span>
            </div>
          ) : (
            contacts.map((contact) => (
              <div key={contact.id} className="rounded-lg border-2 border-slate-300 bg-slate-50 p-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="grid gap-2">
                    <strong className="text-xl font-extrabold text-slate-950">{contact.full_name}</strong>
                    <span className="text-lg text-slate-700">{contact.email}</span>
                    <span className="text-base text-slate-600">{contact.phone_number || "Chưa có số điện thoại"}</span>
                    <div className="tag-row">
                      <span className={`status ${contact.status === "confirmed" ? "status-approved" : "status-pending"}`}>
                        {contact.status === "confirmed" ? "Đã xác nhận" : "Chờ xác nhận"}
                      </span>
                    </div>
                    {contact.confirmation_preview_url && (
                      <a className="text-base font-bold text-blue-800 underline" href={contact.confirmation_preview_url} target="_blank" rel="noreferrer">
                        Mở liên kết xác nhận demo
                      </a>
                    )}
                  </div>
                  <div className="actions-cell">
                    {contact.status !== "confirmed" && (
                      <button className="button ghost small" type="button" onClick={() => void resendConfirmation(contact.id)}>
                        Gửi lại email
                      </button>
                    )}
                    <button className="button ghost small" type="button" onClick={() => void removeContact(contact.id)}>
                      Xóa
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
