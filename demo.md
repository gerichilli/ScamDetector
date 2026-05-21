# Kịch bản Demo

## 1. Tài khoản dùng để demo

### Tài khoản người dùng
- Email: `elder@example.com`
- Mật khẩu: `StrongPass123`

### Tài khoản quản trị
- Email: `admin@example.com`
- Mật khẩu: `AdminPass123`

---

## 2. Các mục demo

### 2.1 Đăng ký đơn giản với Google
- Dùng tài khoản Google thật của người demo
- Mục tiêu:
  - Chứng minh hệ thống hỗ trợ đăng nhập / đăng ký nhanh bằng Google

### 2.2 Đăng ký với email
- Thông tin nhập:
  - Họ tên: `Nguyễn Văn A`
  - Email: `demo_user@example.com`
  - Mật khẩu: `StrongPass123`
- Mục tiêu:
  - Tạo tài khoản mới bằng email

### 2.3 Đăng nhập
- Tài khoản:
  - Email: `elder@example.com`
  - Mật khẩu: `StrongPass123`
- Mục tiêu:
  - Đăng nhập thành công vào hệ thống

### 2.4 Tra cứu số điện thoại lừa đảo
- Số điện thoại nhập:
  - `0987654321`
- Kỳ vọng:
  - Hiển thị cảnh báo mức rất nguy hiểm

- Số điện thoại nhập:
  - `0934455667`
- Kỳ vọng:
  - Hiển thị cảnh báo mức Rủi ro cao

- Số điện thoại nhập:
  - `0922113344`
- Kỳ vọng:
  - Hiển thị cảnh báo mức Rủi ro thấp

### 2.5 Xem trang thống kê
- Tài khoản:
  - `elder@example.com` / `StrongPass123`
- Mục tiêu:
  - Mở trang thống kê và trình bày số liệu / biểu đồ tổng quan

### 2.6 Xem trang lịch sử
- Tài khoản: 
  - `elder@example.com` / `StrongPass123`
- Mục tiêu:
  - Mở trang lịch sử để xem lại dữ liệu đã tra cứu / cảnh báo

### 2.7 Demo báo cáo cuộc gọi nghi ngờ
- Thông tin nhập:
  - Số điện thoại: `0909998888`
  - Thời lượng: `90`
  - Nội dung:
    `Người này gọi yêu cầu đọc mã OTP để mở khóa tài khoản ngân hàng và chuyển tiền ngay.`
  - Ghi chú:
    `Demo báo cáo cuộc gọi nghi ngờ`
- Mục tiêu:
  - Tạo một báo cáo cuộc gọi mức rủi ro cao

### 2.8 Demo admin duyệt / từ chối
- Tài khoản admin:
  - `admin@example.com` / `AdminPass123`
- Dữ liệu dùng:
  - Báo cáo vừa tạo ở bước `2.7`
- Mục tiêu:
  - Vào trang quản trị
  - Duyệt hoặc từ chối báo cáo

### 2.9 Demo chatbot nhập văn bản
- Nội dung nhập:
  - `Người này nói tài khoản của tôi đang dính đến một giao dịch bất thường và yêu cầu tôi đọc mã OTP, rồi chuyển gấp 5 triệu đồng sang tài khoản khác để xác minh và tránh bị khóa tài khoản.`
- Mục tiêu:
  - Chatbot phân tích và đưa ra cảnh báo phù hợp

### 2.10 Demo chatbot gửi ảnh
- Ảnh chuẩn bị sẵn:
  - 1 ảnh chụp màn hình tin nhắn có nội dung:
    `Vui lòng cung cấp mã OTP để xác minh tài khoản của bạn.`
- Mục tiêu:
  - Hệ thống phân tích và đưa ra cảnh báo

---

## 3. Lưu ý trước khi demo

- Kiểm tra frontend đang chạy đúng cổng hiện tại
- Kiểm tra backend đang chạy tại `http://localhost:8000`
- Kiểm tra tài khoản demo còn đăng nhập được
- Nếu demo Google, kiểm tra Google OAuth đã cấu hình sẵn
- Nếu demo chatbot ảnh, chuẩn bị sẵn ảnh rõ chữ
