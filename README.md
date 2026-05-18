# Scam Warning Platform

Ứng dụng cảnh báo lừa đảo qua điện thoại, thiết kế ưu tiên cho người lớn tuổi. Hệ thống gồm frontend React và backend FastAPI, có dữ liệu mẫu để demo các chức năng chính.

## 1. Cách install các thư viện cần thiết

### Yêu cầu môi trường

- Python 3.12 trở lên
- Node.js 20 trở lên
- npm
- Docker Desktop, nếu muốn chạy PostgreSQL bằng Docker

### Cài thư viện backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Cài thư viện frontend

```bash
cd frontend
npm install
```

## 2. Cách chạy

### Chạy backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend mặc định dùng SQLite tại:

```txt
backend/scam_warning.db
```

Nếu muốn dùng PostgreSQL, cấu hình biến môi trường `DATABASE_URL`.

### Chạy frontend

Mở terminal khác:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

### Chạy bằng Docker Compose

```bash
docker compose up --build
```

Docker Compose sẽ chạy:

- PostgreSQL
- FastAPI backend
- React frontend

## 3. Cách mở

Sau khi chạy server, mở các đường dẫn sau:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Tài liệu API Swagger: http://localhost:8000/docs

Nếu frontend tự chạy ở port khác, ví dụ `5174`, terminal sẽ hiển thị URL mới.

## 4. Các tác vụ cơ bản

### Đăng ký / đăng nhập

Người dùng có thể tạo tài khoản hoặc dùng tài khoản demo ở phần mock data.

### Tra cứu cảnh báo lừa đảo

Vào trang **Tra cứu**, nhập số điện thoại để kiểm tra số đó có nằm trong dữ liệu cảnh báo hay không.

Kết quả được tô màu theo mức nguy hiểm:

- Xanh lá: rủi ro thấp
- Vàng: đáng nghi
- Đỏ nhạt: rủi ro cao
- Đỏ đậm: rất nguy hiểm

### Báo cáo cuộc gọi nghi ngờ

Vào trang **Báo cáo cuộc gọi**, nhập:

- Số điện thoại gọi đến
- Thời lượng cuộc gọi
- Nội dung người gọi đã nói
- Ghi chú thêm

Hệ thống sẽ tạo cảnh báo và gợi ý bác nên làm gì.

### Xem lịch sử cuộc gọi

Vào trang **Lịch sử cuộc gọi** để xem lại:

- Cuộc gọi bác đã báo
- Nội dung bác ghi lại
- Mức cảnh báo
- Lời khuyên của hệ thống

### Xem thống kê

Vào trang **Thống kê** để xem:

- Tổng cảnh báo
- Cảnh báo cần chú ý
- Số điện thoại / mẫu lừa đảo đã biết
- Xu hướng 30 ngày
- Các kiểu lừa đảo thường gặp

### Quản trị dữ liệu lừa đảo

Đăng nhập bằng tài khoản admin, vào **Quản trị** để thêm:

- Số điện thoại nghi ngờ
- Kiểu lừa đảo
- Mô tả dễ hiểu
- Mức rủi ro

## 5. Mock data để nhập vào xác nhận

### Nạp dữ liệu mẫu

```bash
cd backend
source .venv/bin/activate
python scripts/seed_mock_data.py
```

Script này có thể chạy nhiều lần. Dữ liệu chính sẽ được cập nhật, không cần tạo thủ công.

### Tài khoản demo

Người dùng thường:

```txt
Email: elder@example.com
Mật khẩu: StrongPass123
```

Quản trị viên:

```txt
Email: admin@example.com
Mật khẩu: AdminPass123
```

### Số điện thoại để tra cứu

Rất nguy hiểm:

```txt
0987654321
```

Rủi ro cao:

```txt
0901122334
0934455667
```

Đáng nghi:

```txt
0919988776
```

Chưa có cảnh báo rõ:

```txt
0977001122
```

### Nội dung mẫu để báo cáo cuộc gọi

Trường hợp rủi ro cao:

```txt
Người gọi tự xưng là ngân hàng, yêu cầu bác đọc mã OTP để mở khóa tài khoản.
```

Trường hợp giả danh công an:

```txt
Người gọi nói bác liên quan đến vụ án và yêu cầu chuyển tiền để xác minh.
```

Trường hợp đáng nghi:

```txt
Bác đã trúng thưởng, chỉ cần đóng phí vận chuyển để nhận quà.
```

Trường hợp đầu tư:

```txt
Người gọi hứa đầu tư lợi nhuận cao, nạp tiền hôm nay sẽ nhận lại gấp đôi.
```

## Cấu trúc project

```txt
backend/
  app/
    api/
    core/
    models/
    schemas/
    services/
  scripts/
    seed_mock_data.py

frontend/
  src/
    api/
    components/
    pages/
    state/
```

## Ghi chú

- UC chatbot AI chưa làm trong phase hiện tại.
- Backend hiện hỗ trợ:
  - `POST /api/v1/chat/analyze` để phân tích văn bản nhập tay.
  - `POST /api/v1/chat/analyze-image` để nhận diện text trong ảnh bằng Tesseract OCR.
- Phần phát hiện rủi ro đang dùng rule-based detector tạm thời.
- Khi đưa lên production, nên thêm migration Alembic đầy đủ và cấu hình biến môi trường an toàn.
