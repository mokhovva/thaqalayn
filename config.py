import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'thaqalayn-game-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///thaqalayn.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 مگابایت
    
    @staticmethod
    def init_upload_folders():
        folders = ['backgrounds', 'audio']
        for folder in folders:
            path = os.path.join(Config.UPLOAD_FOLDER, folder)
            os.makedirs(path, exist_ok=True)
            print(f"✓ پوشه بررسی شد: {path}")

# ساخت خودکار پوشه‌ها هنگام import
Config.init_upload_folders()