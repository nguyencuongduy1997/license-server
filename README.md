# License Server cho Trading Bot

Server quản lý license cho ứng dụng Trading Bot, cho phép xác thực license từ xa và quản lý các license.

## Tính năng

- Xác thực license dựa trên hardware ID
- Tạo license mới với thời hạn tùy chọn
- Vô hiệu hóa license
- Xem danh sách license

## API Endpoints

### Kiểm tra License
- **URL**: `/api/verify-license`
- **Method**: POST
- **Body**:
  ```json
  {
    "hardware_id": "id_phần_cứng_của_máy_tính",
    "license_key": "khóa_license",
    "app_version": "phiên_bản_ứng_dụng"
  }
  ```

### Tạo License Mới
- **URL**: `/api/create-license`
- **Method**: POST
- **Body**:
  ```json
  {
    "hardware_id": "id_phần_cứng_của_máy_tính",
    "duration_days": 365,
    "admin_key": "khóa_admin"
  }
  ```

### Vô hiệu hóa License
- **URL**: `/api/deactivate-license`
- **Method**: POST
- **Body**:
  ```json
  {
    "license_key": "khóa_license",
    "admin_key": "khóa_admin"
  }
  ```

### Xem Danh Sách License
- **URL**: `/api/list-licenses`
- **Method**: POST
- **Body**:
  ```json
  {
    "admin_key": "khóa_admin"
  }
  ```

## Cài đặt và Chạy

### Cài đặt Local
1. Cài đặt các thư viện: `pip install -r requirements.txt`
2. Chạy server: `python app.py`

### Triển khai trên Render.com
Xem hướng dẫn bên dưới.
