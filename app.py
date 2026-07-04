from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import os
import random
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'game'

# ==================== MODELS ====================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.relationship('UserProgress', backref='user', lazy=True, cascade='all, delete-orphan')

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    language = db.Column(db.String(10), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    score = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'language', 'level', name='unique_user_progress'),)

class GameSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    background_image = db.Column(db.String(200), default='')
    background_audio = db.Column(db.String(200), default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HelpContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_fa = db.Column(db.Text, default='')
    content_ar = db.Column(db.Text, default='')
    content_en = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AboutContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_fa = db.Column(db.Text, default='')
    content_ar = db.Column(db.Text, default='')
    content_en = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==================== GAME DATA ====================
GAME_DATA = {
    'fa': {
        'easy': [
            {"answer": "الله", "hint": "نام خداوند متعال"},
            {"answer": "قرآن", "hint": "کتاب آسمانی مسلمانان"},
            {"answer": "نماز", "hint": "عبادت پنج‌گانه روزانه"},
            {"answer": "روزه", "hint": "امساک از خوردن و آشامیدن"},
            {"answer": "حمد", "hint": "نام دیگر سوره فاتحه"},
            {"answer": "توحید", "hint": "سوره اخلاص - یگانگی خدا"},
            {"answer": "مکه", "hint": "شهر خانه خدا"},
            {"answer": "کعبه", "hint": "قبله مسلمانان"},
            {"answer": "محمد", "hint": "نام پیامبر اسلام (ص)"},
            {"answer": "علی", "hint": "امام اول شیعیان"}
        ],
        'medium': [
            {"answer": "کربلا", "hint": "سرزمین شهادت امام حسین (ع)"},
            {"answer": "غدیر", "hint": "محل اعلام ولایت امام علی (ع)"},
            {"answer": "صادق", "hint": "امام ششم شیعیان"},
            {"answer": "رضا", "hint": "امام هشتم - مدفون در مشهد"},
            {"answer": "زینب", "hint": "خواهر امام حسین (ع)"},
            {"answer": "عاشورا", "hint": "روز دهم محرم"},
            {"answer": "نجف", "hint": "شهر مرقد امام علی (ع)"},
            {"answer": "مدینه", "hint": "شهر هجرت پیامبر (ص)"}
        ],
        'hard': [
            {"answer": "استغفار", "hint": "طلب آمرزش از خداوند"},
            {"answer": "مناجات", "hint": "راز و نیاز عاشقانه با خدا"},
            {"answer": "معراج", "hint": "سفر آسمانی پیامبر (ص)"},
            {"answer": "بعثت", "hint": "آغاز رسالت پیامبر (ص)"},
            {"answer": "هجرت", "hint": "کوچ از مکه به مدینه"},
            {"answer": "غدیرخم", "hint": "محل اعلام جانشینی علی (ع)"}
        ],
        'expert': [
            {"answer": "امیرالمومنین", "hint": "لقب امام علی علیه السلام"},
            {"answer": "سیدالشهداء", "hint": "لقب امام حسین علیه السلام"},
            {"answer": "زین‌العابدین", "hint": "لقب امام سجاد علیه السلام"},
            {"answer": "باقرالعلوم", "hint": "لقب امام محمد باقر (ع)"}
        ]
    },
    'ar': {
        'easy': [
            {"answer": "الله", "hint": "اسم الرب العظيم"},
            {"answer": "قرآن", "hint": "الكتاب السماوي"},
            {"answer": "صلاة", "hint": "العبادة الخمس يومياً"},
            {"answer": "صوم", "hint": "الامتناع عن الأكل"},
            {"answer": "محمد", "hint": "اسم النبي (ص)"},
            {"answer": "علي", "hint": "الإمام الأول"}
        ],
        'medium': [
            {"answer": "كربلاء", "hint": "أرض استشهاد الحسين"},
            {"answer": "غدير", "hint": "موضع إعلان الولاية"},
            {"answer": "صادق", "hint": "الإمام السادس"},
            {"answer": "رضا", "hint": "الإمام الثامن"},
            {"answer": "زينب", "hint": "أخت الإمام الحسين"},
            {"answer": "عاشوراء", "hint": "يوم استشهاد الحسين"}
        ],
        'hard': [
            {"answer": "استغفار", "hint": "طلب المغفرة من الله"},
            {"answer": "مناجاة", "hint": "الحديث السري مع الله"},
            {"answer": "معراج", "hint": "رحلة النبي السماوية"},
            {"answer": "بعثة", "hint": "بداية رسالة النبي"}
        ],
        'expert': [
            {"answer": "أميرالمؤمنين", "hint": "لقب الإمام علي (ع)"},
            {"answer": "سيدالشهداء", "hint": "لقب الإمام الحسين (ع)"},
            {"answer": "زين‌العابدين", "hint": "لقب الإمام السجاد (ع)"}
        ]
    },
    'en': {
        'easy': [
            {"answer": "ALLAH", "hint": "Name of God Almighty"},
            {"answer": "QURAN", "hint": "Holy book of Muslims"},
            {"answer": "SALAT", "hint": "Daily five prayers"},
            {"answer": "SAWM", "hint": "Fasting in Ramadan"},
            {"answer": "IMAM", "hint": "Religious leader"}
        ],
        'medium': [
            {"answer": "KARBALA", "hint": "Land of Hussain's martyrdom"},
            {"answer": "GHADIR", "hint": "Place of Ali's appointment"},
            {"answer": "SADIQ", "hint": "The sixth Imam"},
            {"answer": "RIDHA", "hint": "Eighth Imam in Mashhad"},
            {"answer": "ASHURA", "hint": "Day of Hussain's martyrdom"}
        ],
        'hard': [
            {"answer": "ISTIGHFAR", "hint": "Seeking forgiveness"},
            {"answer": "MUNAJAT", "hint": "Intimate prayer with God"},
            {"answer": "MIRAJ", "hint": "Prophet's night journey"},
            {"answer": "HIJRAH", "hint": "Migration to Medina"}
        ],
        'expert': [
            {"answer": "AMIRALMU'MININ", "hint": "Title of Imam Ali"},
            {"answer": "SAYYIDUSHUHADA", "hint": "Title of Imam Hussain"},
            {"answer": "ZAYNULABIDIN", "hint": "Title of Imam Sajjad"}
        ]
    }
}

LEVEL_CONFIG = {
    'easy': {'answer_length': 4, 'extra_letters': 0, 'question_count': 5},
    'medium': {'answer_length': 5, 'extra_letters': 2, 'question_count': 5},
    'hard': {'answer_length': 6, 'extra_letters': 4, 'question_count': 5},
    'expert': {'answer_length': 7, 'extra_letters': 7, 'question_count': 5}
}

LEVEL_ORDER = ['easy', 'medium', 'hard', 'expert']

# ==================== HELPERS ====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin_user():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin_user)
        
        settings = GameSettings.query.first()
        if not settings:
            settings = GameSettings(background_image='', background_audio='')
            db.session.add(settings)
        
        if not HelpContent.query.first():
            db.session.add(HelpContent(
                content_fa='راهنمای بازی:\n\n1. حروف را به ترتیب صحیح انتخاب کنید\n2. برای پاک کردن از دکمه پاک کردن استفاده کنید\n3. پس از تکمیل هر مرحله، مرحله بعد باز می‌شود',
                content_ar='إرشادات اللعبة:\n\n1. اختر الحروف بالترتيب الصحيح\n2. استخدم زر المسح للمسح\n3. بعد إكمال كل مرحلة، تفتح المرحلة التالية',
                content_en='Game Instructions:\n\n1. Select letters in correct order\n2. Use clear button to reset\n3. After completing each level, next level unlocks'
            ))
        
        if not AboutContent.query.first():
            db.session.add(AboutContent(
                content_fa='بازی ثقلین\n\nیک بازی آموزشی مذهبی برای یادگیری مفاهیم قرآنی و عترت.\n\nتوسعه داده شده با ❤️',
                content_ar='لعبة الثقلين\n\nلعبة تعليمية دينية لتعلم المفاهيم القرآنية والعترة.\n\nتم التطوير بـ ❤️',
                content_en='Thaqalayn Game\n\nAn educational religious game for learning Quranic and Ahlulbayt concepts.\n\nDeveloped with ❤️'
            ))
        
        db.session.commit()
        print("✓ Admin created: admin / admin123")

def init_audio_file():
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', 'background-audio.mp3')
    if os.path.exists(audio_path):
        settings = GameSettings.query.first()
        if settings and not settings.background_audio:
            settings.background_audio = 'background-audio.mp3'
            db.session.commit()
            print("✓ فایل صوتی پس‌زمینه در دیتابیس ثبت شد")

def can_access_level(user, lang, level):
    if not user:
        return False
    if user.is_admin:
        return True
    level_index = LEVEL_ORDER.index(level)
    if level_index == 0:
        return True
    previous_level = LEVEL_ORDER[level_index - 1]
    progress = UserProgress.query.filter_by(user_id=user.id, language=lang, level=previous_level).first()
    return progress is not None

# ==================== ROUTES ====================
def initialize_app():
    with app.app_context():
        db.create_all()
        create_admin_user()
        init_audio_file()

initialize_app()
@app.route('/')
def intro():
    return render_template('intro_judge.html')

@app.route('/game')
def index():
    return render_template('index.html')

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    current_lang = request.args.get('lang', 'fa')
    users = User.query.filter(User.username != 'admin').all()
    settings = GameSettings.query.first()
    help_content = HelpContent.query.first()
    about_content = AboutContent.query.first()
    
    return render_template('admin.html', 
                         users=users, 
                         settings=settings,
                         help_content_fa=help_content.content_fa if help_content else '',
                         help_content_ar=help_content.content_ar if help_content else '',
                         help_content_en=help_content.content_en if help_content else '',
                         about_content_fa=about_content.content_fa if about_content else '',
                         about_content_ar=about_content.content_ar if about_content else '',
                         about_content_en=about_content.content_en if about_content else '',
                         current_lang=current_lang)

# ==================== PWA ROUTES (اضافه شده) ====================
@app.route('/manifest.json')
def serve_manifest():
    """سرو کردن فایل مانیفست برای PWA"""
    response = send_from_directory('static', 'manifest.json')
    response.headers['Content-Type'] = 'application/manifest+json'
    return response

@app.route('/sw.js')
def serve_sw():
    """سرو کردن فایل Service Worker برای PWA"""
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

# ==================== PUBLIC API ====================
@app.route('/api/public/settings')
def get_public_settings():
    settings = GameSettings.query.first()
    if not settings:
        return jsonify({'background_image': '', 'background_audio': ''})
    return jsonify({
        'background_image': settings.background_image,
        'background_audio': settings.background_audio
    })

@app.route('/api/content/about')
def get_about_content():
    lang = request.args.get('lang', 'fa')
    content = AboutContent.query.first()
    if not content:
        content = AboutContent()
        db.session.add(content)
        db.session.commit()
    
    field = f'content_{lang}'
    text = getattr(content, field, None) or content.content_fa
    return jsonify({'success': True, 'content': text})

# ==================== AUTH API ====================
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Empty fields'})
    if len(username) < 3:
        return jsonify({'success': False, 'error': 'Username too short'})
    if len(password) < 4:
        return jsonify({'success': False, 'error': 'Password too short'})
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'User exists'})
    
    user = User(username=username, password_hash=generate_password_hash(password))
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user, remember=True)
        return jsonify({'success': True, 'is_admin': user.is_admin, 'username': user.username})
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})

@app.route('/api/user/check')
def check_user():
    if current_user.is_authenticated:
        return jsonify({'logged_in': True, 'username': current_user.username, 'is_admin': current_user.is_admin})
    return jsonify({'logged_in': False})

# ==================== GAME API ====================
@app.route('/api/game/levels')
@login_required
def get_levels():
    lang = request.args.get('lang', 'fa')
    levels = []
    for level_name in LEVEL_ORDER:
        progress = UserProgress.query.filter_by(user_id=current_user.id, language=lang, level=level_name).first()
        levels.append({
            'name': level_name,
            'completed': progress is not None,
            'score': progress.score if progress else 0,
            'accessible': can_access_level(current_user, lang, level_name)
        })
    return jsonify({'levels': levels})

@app.route('/api/game/questions')
@login_required
def get_questions():
    lang = request.args.get('lang', 'fa')
    level = request.args.get('level', 'easy')
    
    if not can_access_level(current_user, lang, level):
        return jsonify({'error': 'Access denied'}), 403
    
    questions = GAME_DATA.get(lang, {}).get(level, [])
    config = LEVEL_CONFIG[level]
    valid_questions = [q for q in questions if len(q['answer']) >= config['answer_length']]
    selected = random.sample(valid_questions, min(config['question_count'], len(valid_questions)))
    return jsonify({'questions': selected})

@app.route('/api/game/save_progress', methods=['POST'])
@login_required
def save_progress():
    data = request.json
    lang = data.get('lang', 'fa')
    level = data.get('level', 'easy')
    score = data.get('score', 0)
    
    progress = UserProgress.query.filter_by(user_id=current_user.id, language=lang, level=level).first()
    if progress:
        if score > progress.score:
            progress.score = score
            progress.completed_at = datetime.utcnow()
    else:
        progress = UserProgress(user_id=current_user.id, language=lang, level=level, score=score)
        db.session.add(progress)
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'})

@app.route('/api/content/help')
def get_help_content():
    lang = request.args.get('lang', 'fa')
    content = HelpContent.query.first()
    if not content:
        content = HelpContent()
        db.session.add(content)
        db.session.commit()
    
    field = f'content_{lang}'
    text = getattr(content, field, None) or content.content_fa
    return jsonify({'success': True, 'content': text})

# ==================== ADMIN API ====================
@app.route('/api/admin/delete_user', methods=['POST'])
@login_required
def delete_user():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    user = User.query.get(user_id)
    
    if user and user.id != current_user.id:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'})

@app.route('/api/admin/reset_password', methods=['POST'])
@login_required
def reset_password():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    new_password = data.get('new_password')
    
    if not user_id or not new_password:
        return jsonify({'success': False, 'error': 'Missing data'})
    
    if len(new_password) < 4:
        return jsonify({'success': False, 'error': 'Password too short'})
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'})
    
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Password updated'})

@app.route('/api/admin/upload_background', methods=['POST'])
@login_required
def upload_background():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'backgrounds', filename)
    file.save(filepath)
    
    settings = GameSettings.query.first()
    if not settings:
        settings = GameSettings()
        db.session.add(settings)
    settings.background_image = filename
    db.session.commit()
    return jsonify({'success': True, 'filename': filename})

@app.route('/api/admin/upload_audio', methods=['POST'])
@login_required
def upload_audio():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', filename)
    file.save(filepath)
    
    settings = GameSettings.query.first()
    if not settings:
        settings = GameSettings()
        db.session.add(settings)
    settings.background_audio = filename
    db.session.commit()
    return jsonify({'success': True, 'filename': filename})

@app.route('/api/admin/content/help', methods=['POST'])
@login_required
def update_help_content():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    content = HelpContent.query.first()
    if not content:
        content = HelpContent()
        db.session.add(content)
    
    if 'content_fa' in data:
        content.content_fa = data['content_fa']
    if 'content_ar' in data:
        content.content_ar = data['content_ar']
    if 'content_en' in data:
        content.content_en = data['content_en']
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'راهنما بروزرسانی شد'})

@app.route('/api/admin/content/about', methods=['POST'])
@login_required
def update_about_content():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    content = AboutContent.query.first()
    if not content:
        content = AboutContent()
        db.session.add(content)
    
    if 'content_fa' in data:
        content.content_fa = data['content_fa']
    if 'content_ar' in data:
        content.content_ar = data['content_ar']
    if 'content_en' in data:
        content.content_en = data['content_en']
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'درباره ما بروزرسانی شد'})

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== MAIN ====================
if __name__ == '__main__':
    print("=" * 50)
    print("🎮 ثقلین بازی")
    print("🌐 وب: Running...")
    print("👤 Username: admin | Password: admin123")
    print("=" * 50)

    app.run(
        debug=False,
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 5000))
    )
