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
    </section>
  );
}
