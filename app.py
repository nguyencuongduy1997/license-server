from flask import Flask, request, jsonify, render_template
import json
import os
import logging
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Cho phép cross-origin requests

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Đường dẫn đến file licenses.json
LICENSES_FILE = os.path.join(os.path.dirname(__file__), 'licenses.json')

# Hàm để đọc dữ liệu license từ file
def load_licenses():
    try:
        if os.path.exists(LICENSES_FILE):
            with open(LICENSES_FILE, 'r') as f:
                return json.load(f)
        else:
            # Tạo file mới nếu không tồn tại
            with open(LICENSES_FILE, 'w') as f:
                json.dump({}, f)
            return {}
    except Exception as e:
        logger.error(f"Lỗi khi đọc file licenses: {e}")
        return {}

# Hàm để lưu dữ liệu license vào file
def save_licenses(licenses):
    try:
        with open(LICENSES_FILE, 'w') as f:
            json.dump(licenses, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Lỗi khi lưu file licenses: {e}")
        return False

# Trang chủ
@app.route('/')
def home():
    return "<h1>License Server</h1><p>API đang hoạt động</p>"

# API kiểm tra license
@app.route("/api/verify-license", methods=["POST"])
def verify_license():
    try:
        data = request.json
        hardware_id = data.get("hardware_id")
        license_key = data.get("license_key")
        app_version = data.get("app_version", "unknown")
        
        if not hardware_id or not license_key:
            return jsonify({"valid": False, "message": "Thiếu thông tin hardware_id hoặc license_key"})
        
        # Log thông tin request
        logger.info(f"Kiểm tra license: {license_key[:10]}... cho hardware_id: {hardware_id[:10]}... (version: {app_version})")
        
        # Đọc dữ liệu license
        licenses = load_licenses()
        
        # Kiểm tra license có tồn tại không
        if license_key not in licenses:
            return jsonify({"valid": False, "message": "License không tồn tại"})
        
        license_info = licenses[license_key]
        
        # Kiểm tra hardware ID
        if license_info.get("hardware_id") != hardware_id:
            return jsonify({"valid": False, "message": "License không hợp lệ cho thiết bị này"})
        
        # Kiểm tra ngày hết hạn - SỬA LỖI Ở ĐÂY
        if "expires_at" in license_info and license_info["expires_at"] is not None:
            expires_at = datetime.fromisoformat(license_info["expires_at"])
            if datetime.now() > expires_at:
                return jsonify({"valid": False, "message": f"License đã hết hạn vào {expires_at.strftime('%d/%m/%Y')}"})
        
        # Cập nhật thông tin sử dụng
        license_info["last_check"] = datetime.now().isoformat()
        license_info["last_app_version"] = app_version
        save_licenses(licenses)
        
        # Trả về kết quả thành công
        response = {
            "valid": True,
            "message": "License hợp lệ"
        }
        
        # Thêm thông tin hết hạn nếu có
        if "expires_at" in license_info and license_info["expires_at"] is not None:
            response["expires_at"] = license_info["expires_at"]
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Lỗi xử lý request: {e}")
        return jsonify({"valid": False, "message": f"Lỗi server: {str(e)}"}), 500

# API tạo license mới
@app.route("/api/create-license", methods=["POST"])
def create_license():
    try:
        data = request.json
        hardware_id = data.get("hardware_id")
        duration_days = data.get("duration_days")  # Số ngày hợp lệ, None = vĩnh viễn
        admin_key = data.get("admin_key")
        
        # Kiểm tra admin key (thay thế bằng cơ chế xác thực an toàn hơn trong môi trường thực tế)
        if admin_key != os.environ.get("ADMIN_KEY", "admin_secret_key"):
            return jsonify({"success": False, "message": "Không có quyền tạo license"}), 403
        
        if not hardware_id:
            return jsonify({"success": False, "message": "Thiếu hardware_id"}), 400
        
        # Tạo license key mới
        import uuid
        license_key = str(uuid.uuid4())
        
        # Tính ngày hết hạn nếu có
        expires_at = None
        if duration_days:
            expires_at = (datetime.now() + timedelta(days=int(duration_days))).isoformat()
        
        # Đọc dữ liệu license hiện tại
        licenses = load_licenses()
        
        # Thêm license mới
        licenses[license_key] = {
            "hardware_id": hardware_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "active": True
        }
        
        # Lưu lại
        if save_licenses(licenses):
            return jsonify({
                "success": True,
                "license_key": license_key,
                "expires_at": expires_at
            })
        else:
            return jsonify({"success": False, "message": "Không thể lưu license"}), 500
            
    except Exception as e:
        logger.error(f"Lỗi tạo license: {e}")
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500

# API vô hiệu hóa license
@app.route("/api/deactivate-license", methods=["POST"])
def deactivate_license():
    try:
        data = request.json
        license_key = data.get("license_key")
        admin_key = data.get("admin_key")
        
        # Kiểm tra admin key
        if admin_key != os.environ.get("ADMIN_KEY", "admin_secret_key"):
            return jsonify({"success": False, "message": "Không có quyền vô hiệu hóa license"}), 403
        
        if not license_key:
            return jsonify({"success": False, "message": "Thiếu license_key"}), 400
        
        # Đọc dữ liệu license
        licenses = load_licenses()
        
        # Kiểm tra license có tồn tại không
        if license_key not in licenses:
            return jsonify({"success": False, "message": "License không tồn tại"}), 404
        
        # Vô hiệu hóa license
        licenses[license_key]["active"] = False
        licenses[license_key]["deactivated_at"] = datetime.now().isoformat()
        
        # Lưu lại
        if save_licenses(licenses):
            return jsonify({"success": True, "message": "License đã bị vô hiệu hóa"})
        else:
            return jsonify({"success": False, "message": "Không thể lưu thay đổi"}), 500
            
    except Exception as e:
        logger.error(f"Lỗi vô hiệu hóa license: {e}")
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500

# API lấy danh sách license
@app.route("/api/list-licenses", methods=["POST"])
def list_licenses():
    try:
        data = request.json
        admin_key = data.get("admin_key")
        
        # Kiểm tra admin key
        if admin_key != os.environ.get("ADMIN_KEY", "admin_secret_key"):
            return jsonify({"success": False, "message": "Không có quyền xem danh sách license"}), 403
        
        # Đọc dữ liệu license
        licenses = load_licenses()
        
        # Trả về danh sách
        return jsonify({
            "success": True,
            "licenses": licenses
        })
            
    except Exception as e:
        logger.error(f"Lỗi lấy danh sách license: {e}")
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500

# API kiểm tra sức khỏe server
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Server đang hoạt động bình thường"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
