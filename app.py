

# Import standard and third-party modules used in the Flask application
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort, send_file, Response # Response add kiya
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import get_db, init_db
from groq import Groq
import os
import requests
import sqlite3
import json
import re
import csv # csv add kiya export ke liye
import io # io add kiya
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from io import BytesIO
import zipfile

# Load environment variables from.env file
load_dotenv()

# Create Flask app and configure secret key and CSRF protection
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "Linkkiwi2026")
csrf = CSRFProtect(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'myproject.db')
# Initialize AI clients and API keys
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
HIVE_API_KEY = os.getenv("HIVE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # FIX 1: Variable banaya

# Upload folder paths and maximum allowed upload size
UPLOAD_FOLDER_PROFILE = 'static/uploads/profile_photos'
UPLOAD_FOLDER_EVIDENCE = 'static/uploads/evidence'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER_PROFILE, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_EVIDENCE, exist_ok=True)

# Flask-Login setup for user session management
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize local database file if it does not already exist
if not os.path.exists('myproject.db'):
    init_db()

# Utility to validate uploaded file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'wav', 'pdf'}

# ========== AI FUNCTIONS ==========

def analyze_complaint_with_groq(text):
    """Returns dict: category, priority, summary"""
    if not GROQ_API_KEY: # FIX 1: Variable use kiya
        return {"category": "Other", "priority": "Medium", "summary": text[:100]}

    prompt = f"""Analyze complaint: "{text}"
    Return ONLY JSON: {{"category": "Cheating/Paper Leak/Invigilator Issue/Technical Issue/Harassment/Other",
    "priority": "High/Medium/Low", "summary": "1 line summary"}}"""
    try:
        chat = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(chat.choices[0].message.content)
    except:
        return {"category": "Other", "priority": "Medium", "summary": text[:100]}

def chatbot_reply(user_msg):
    prompt = f"You are exam help bot. Answer in 2 lines: {user_msg}"
    chat = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat.choices[0].message.content

def is_fake_report(text, user_id):
    db = get_db()
    cur = db.execute("SELECT description FROM entries WHERE user_id=? ORDER BY created_at DESC LIMIT 3", (user_id,))
    for row in cur.fetchall():
        if row[0] and text[:50] == row[0][:50]:
            return True
    if not GROQ_API_KEY: # FIX 1: Variable use kiya
        return False
    prompt = f"Is this spam or fake complaint: '{text}'. Reply only Yes or No"
    chat = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return "yes" in chat.choices[0].message.content.lower()

def get_sentiment(text):
    prompt = f"What is sentiment of: '{text}'. Reply only: Angry, Normal, Urgent"
    chat = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat.choices[0].message.content

def professional_report(points):
    prompt = f"Convert these points into formal complaint letter: {points}"
    chat = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat.choices[0].message.content

def dashboard_insights():
    db = get_db()
    data = db.execute("SELECT category, COUNT(*) FROM entries GROUP BY category").fetchall()
    if not GROQ_API_KEY:
        return ["Data not available"]
    prompt = f"Analyze this complaint data: {data}. Give 3 bullet points: Most common issue, Trend, Recommendation"
    try:
        chat = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        return chat.choices[0].message.content.split('\n')
    except:
        return ["AI Error"]

# ========== ROUTES ==========
@app.route('/submit_complaint', methods=['POST'])
@login_required
def submit_complaint():
    text = request.form['complaint']
    file = request.files.get('evidence')
    filepath = None

    if file and file.filename!= '' and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER_EVIDENCE, filename)
        file.save(filepath)
        text += f"\n[Evidence Uploaded]: {filename}"

    ai_data = analyze_complaint_with_groq(text)
    category = ai_data.get('category', 'Other')
    priority = ai_data.get('priority', 'Medium')
    summary = ai_data.get('summary', text[:100])
    sentiment = get_sentiment(text)

    db = get_db()
    db.execute("""INSERT INTO entries
    (user_id, description, category, priority, ai_summary, sentiment, status, created_at)
    VALUES (?,?,?,?,?,?,?,?)""",
    (current_user.id, text, category, priority, summary, sentiment, 'Pending', datetime.now()))

    db.commit()
    db.close()

    flash("Complaint submitted with AI Analysis", "success")
    return redirect(url_for('dashboard'))

@app.route('/chatbot', methods=['POST'])
def chatbot():
    msg = request.json['message']
    reply = chatbot_reply(msg)
    return jsonify({"reply": reply})

@app.route('/ai_report_writer', methods=['POST'])
@login_required
def ai_report_writer():
    points = request.form['points']
    professional = professional_report(points)
    return jsonify({"report": professional})

class User(UserMixin):
    def __init__(self, id, username, name, role='student', is_mobile_verified=0, is_email_verified=0, is_blocked=0):
        self.id = id
        self.username = username
        self.name = name
        self.role = role
        self.is_mobile_verified = is_mobile_verified
        self.is_email_verified = is_email_verified
        self.is_blocked = is_blocked
@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user_row = conn.execute('SELECT * FROM users WHERE id =?', (user_id,)).fetchone()
    conn.close()
    if user_row:
        user = dict(user_row)
        return User(
            id=user['id'],
            username=user['username'],
            name=user.get('name', 'User'),
            role=user.get('role', 'student'),
            is_mobile_verified=user.get('is_mobile_verified', 0),
            is_email_verified=user.get('is_email_verified', 0),
            is_blocked=user.get('is_blocked', 0)
        )
    return None

DUMMY_REPORTS = [
    {
        "id": 1,
        "exam_name": "MSBTE Summer 2026",
        "subject_name": "MICROPROCESSOR PROGRAMMING",
        "college_name": "Government Polytechnic Hingoli",
        "report_date": "01-06-2026",
        "description": "Sample leak report for testing. This is a dummy entry.",
        "is_dummy": True
    },
    {
        "id": 2,
        "exam_name": "MSBTE Summer 2026",
        "subject_name": "Data Structure",
        "college_name": "Government Polytechnic Khamgaon",
        "report_date": "02-06-2026",
        "description": "Sample resolved case for testing. This is a dummy entry.",
        "is_dummy": True
    }
]

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '').strip()
        state = request.form.get('state', '').strip()
        district = request.form.get('district', '').strip()

        email_verified = request.form.get('email_verified') == '1'

        if not email_verified:
            flash('Please verify Email first!', 'error')
            return redirect(url_for('register'))

        if not all([name, username, email, mobile, password, state, district]):
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return redirect(url_for('register'))

        if len(mobile)!= 10 or not mobile.isdigit():
            flash('Mobile number must be 10 digits!', 'error')
            return redirect(url_for('register'))

        conn = get_db()
        existing_user = conn.execute('SELECT * FROM users WHERE username =? OR email =? OR mobile =?',
                                     (username, email, mobile)).fetchone()

        if existing_user:
            flash('Username, Email or Mobile already exists!', 'error')
            conn.close()
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)

        # FIX: 10 columns = 10 ?
        conn.execute('''INSERT INTO users
                     (name, username, email, mobile, password, state, district,
                      signup_ip, signup_user_agent, role, is_email_verified, is_mobile_verified)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', # 12 ?
                     (name, username, email, mobile, hashed_pw, state, district,
                      request.remote_addr, request.headers.get('User-Agent'),
                      'student', 1, 0))

        conn.commit()
        conn.close()

        flash('Registration successful! You can login now.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username').strip()
        password = request.form.get('password')

        conn = get_db()
        c = conn.cursor()

        user_row = c.execute("SELECT * FROM users WHERE username =? OR email =?",
                             (username_or_email, username_or_email)).fetchone()
        conn.close()

        if not user_row:
            flash('Invalid username or email', 'error')
            return render_template('login.html')

        user = dict(user_row)

        if not check_password_hash(user['password'], password):
            flash('Invalid password', 'error')
            return render_template('login.html')

        if user.get('is_email_verified', 0) == 0:
            flash('Please verify your email first', 'error')
            return render_template('login.html')

        if user.get('is_blocked', 0) == 1:
            flash('Your account is blocked. Contact admin.', 'error')
            return render_template('login.html')

        user_obj = User(
            id=user['id'],
            username=user['username'],
            name=user.get('name','User'),
            role=user['role'],
            is_email_verified=user['is_email_verified'],
            is_blocked=user['is_blocked']
        )
        login_user(user_obj)

        flash(f'Welcome back, {user.get("name","User")}!', 'success')

        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login first', 'error')
            return redirect(url_for('login'))

        if current_user.role!= 'admin':
            flash('You do not have admin permission', 'error')
            return redirect(url_for('dashboard'))

        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db()
    c = conn.cursor()
    c.row_factory = sqlite3.Row

    stats = {
        'total_users': c.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
        'total_reports': c.execute("SELECT COUNT(*) FROM entries").fetchone()[0],
        'pending': c.execute("SELECT COUNT(*) FROM entries WHERE status='Pending' OR status IS NULL").fetchone()[0],
        'resolved': c.execute("SELECT COUNT(*) FROM entries WHERE status='Resolved'").fetchone()[0],
        'blocked': c.execute("SELECT COUNT(*) FROM users WHERE is_blocked=1").fetchone()[0],
        'today_reports': c.execute("SELECT COUNT(*) FROM entries WHERE date(created_at)=date('now')").fetchone()[0]
    }

    recent_reports = c.execute('''
        SELECT e.id, u.name, e.exam_name, e.status, e.created_at, e.category, e.ai_summary, e.urgency_score, e.sentiment
        FROM entries e
        JOIN users u ON e.user_id = u.id
        ORDER BY e.created_at DESC
        LIMIT 10
    ''').fetchall()

    monthly_reports = c.execute("""
        SELECT strftime('%b %Y', created_at) as month, COUNT(*) as cnt
        FROM entries
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY strftime('%Y-%m', created_at)
    """).fetchall()

    monthly_users = c.execute("""
        SELECT strftime('%b %Y', created_at) as month, COUNT(*) as cnt
        FROM users
        WHERE role='student'
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY strftime('%Y-%m', created_at)
    """).fetchall()

    conn.close()
    insights = dashboard_insights()
    return render_template('admin_dashboard.html',
                           user=current_user,
                           stats=stats,
                           insights=insights,
                           recent_reports=recent_reports,
                           monthly_reports=monthly_reports,
                           monthly_users=monthly_users)

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db()
    users = conn.execute("SELECT * FROM users WHERE role='student' ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin_users.html', user=current_user, users=[dict(u) for u in users])

@app.route('/admin/user/block/<int:user_id>')
@admin_required
def toggle_block(user_id):
    if current_user.id == user_id:
        flash('You cannot block yourself', 'error')
        return redirect(url_for('admin_users'))

    conn = get_db()
    current_status = conn.execute("SELECT is_blocked FROM users WHERE id=?", (user_id,)).fetchone()[0]
    new_status = 0 if current_status else 1
    conn.execute("UPDATE users SET is_blocked=? WHERE id=?", (new_status, user_id))
    conn.commit()
    conn.close()
    flash('User status updated!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/delete/<int:user_id>')
@admin_required
def delete_user(user_id):
    if current_user.id == user_id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.execute("DELETE FROM entries WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    flash('User and their reports deleted!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/reports')
@admin_required
def admin_reports():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db()
    conn.row_factory = sqlite3.Row

    total_reports = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]

    reports = conn.execute("""
        SELECT e.*, u.name
        FROM entries e
        JOIN users u ON e.user_id=u.id
        ORDER BY e.id DESC
        LIMIT ? OFFSET ? -- ITHA SPACE TAKLA
    """, (per_page, offset)).fetchall()

    conn.close()

    return render_template('admin_reports.html',
                           user=current_user,
                           reports=[dict(r) for r in reports],
                           page=page,
                           total=total_reports,
                           per_page=per_page)

@app.route('/admin/update_status/<int:id>', methods=['POST'])
@admin_required
def update_status(id):
    db = None
    try:
        new_status = request.form['status']
        db = get_db()
        db.execute('BEGIN IMMEDIATE')

        # 1. Status update
        db.execute('UPDATE entries SET status =? WHERE id =?', (new_status, id))

        # 2. Student ko notification pathao
        complaint = db.execute('SELECT user_id, category FROM entries WHERE id =?', (id,)).fetchone()
        if complaint and complaint['user_id']:
            title = f"Complaint Status Updated" # YE NEW ADD KIYA
            msg = f"Your complaint for '{complaint['category']}' is now: {new_status}"
            link = f"/report/{id}"

            db.execute(
                "INSERT INTO notifications (user_id, title, type, message, link, is_read, created_at) VALUES (?,?,?,?,?,?,?)",
                (complaint['user_id'], title, 'Status Update', msg, link, 0, datetime.now()) # title add
            )
        else:
            flash("Error: Complaint me user_id nahi mila", "danger")
            db.rollback()
            return redirect(url_for('admin_reports'))

        db.commit()
        flash(f"Status updated to {new_status}", "success")

    except sqlite3.OperationalError as e:
        if db: db.rollback()
        flash("Database busy. Please try again.", "danger")
    except sqlite3.IntegrityError as e:
        if db: db.rollback()
        flash(f"DB Error: {e}", "danger")
    finally:
        if db: db.close()

    return redirect(url_for('admin_reports'))

@app.route('/admin/evidence')
@admin_required
def admin_evidence():
    conn = get_db()
    conn.row_factory = sqlite3.Row

    query = '''SELECT e.id, e.exam_name, e.created_at, u.name,
                      e.photos
               FROM entries e
               JOIN users u ON e.user_id = u.id
               WHERE e.photos IS NOT NULL AND e.photos!= '[]' '''

    params = []
    exam = request.args.get('exam')
    file_type = request.args.get('file_type')

    if exam:
        query += ' AND e.exam_name LIKE?'
        params.append(f'%{exam}%')

    query += ' ORDER BY e.created_at DESC'
    entries = conn.execute(query, params).fetchall()
    conn.close()

    files = []
    for entry in entries:
        photos = json.loads(entry['photos']) if entry['photos'] else []
        for photo in photos:
            ext = photo.rsplit('.', 1)[1].lower()
            ftype = 'image' if ext in ['jpg','jpeg','png','gif'] else 'pdf' if ext == 'pdf' else 'video'

            if file_type and file_type!= ftype: continue

            files.append({
                'id': entry['id'],
                'name': entry['name'],
                'exam_name': entry['exam_name'],
                'created_at': entry['created_at'],
                'filename': photo,
                'file_type': ftype,
                'file_size': os.path.getsize(os.path.join(UPLOAD_FOLDER_EVIDENCE, photo)) if os.path.exists(os.path.join(UPLOAD_FOLDER_EVIDENCE, photo)) else 0 # size add
            })

    return render_template('admin_evidence.html', files=files)

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    conn = get_db()

    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_entries = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    total_files = conn.execute("SELECT COUNT(*) FROM entry_files").fetchone()[0]
    total_reports = total_entries

    labels = []
    data = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        count = conn.execute("SELECT COUNT(*) FROM entries WHERE DATE(created_at) =?", (day,)).fetchone()[0]
        labels.append(day[5:])
        data.append(count)

    conn.close()
    return render_template('admin_analytics.html',
                           total_users=total_users,
                           total_entries=total_entries,
                           total_files=total_files,
                           total_reports=total_reports,
                           labels=labels, data=data)

@app.route('/admin/notifications')
@admin_required
def admin_notifications():
    conn = get_db()
    notes = conn.execute("SELECT * FROM notifications ORDER BY created_at DESC").fetchall()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()
    return render_template('admin_notifications.html', notes=notes)

@app.context_processor
def inject_notifications():
    if current_user.is_authenticated: # FIX: session ki jagah current_user
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0").fetchone()[0]
        conn.close()
        return dict(unread_count=count)
    return dict(unread_count=0)

# FIX 3: YE DONO FUNCTION REPLACE KARO
@app.route('/admin/notifications/mark_all_read')
@admin_required
def admin_mark_all_read():
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read = 1")
    conn.commit()
    conn.close()
    flash('All notifications marked as read', 'success')
    return redirect(url_for('admin_notifications'))

@app.route('/admin/notifications/mark_read/<int:id>')
@admin_required
def mark_notification_read(id):
    conn = get_db()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE id =?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

def get_settings():
    conn = get_db()
    s = conn.execute("SELECT * FROM settings WHERE id=1").fetchone()
    conn.close()
    return s

@app.before_request
def check_maintenance():
    settings = get_settings()
    if settings and settings['maintenance_mode'] == 1:
        if request.endpoint and 'static' not in request.endpoint:
            if not current_user.is_authenticated or current_user.role!= 'admin':
                return render_template('maintenance.html'), 503

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_settings():
    conn = get_db()
    settings = conn.execute("SELECT * FROM settings WHERE id=1").fetchone()
    admin = conn.execute("SELECT * FROM users WHERE id =?", (current_user.id,)).fetchone()

    if request.method == 'POST':
        if 'change_password' in request.form:
            old_pass = request.form['old_password']
            new_pass = request.form['new_password']
            if check_password_hash(admin['password'], old_pass):
                hashed = generate_password_hash(new_pass)
                conn.execute("UPDATE users SET password =? WHERE id =?", (hashed, current_user.id))
                conn.commit()
                flash('Password updated successfully', 'success')
            else:
                flash('Old password is wrong', 'danger')

        elif 'save_settings' in request.form:
            ai_model = request.form['ai_model']
            maintenance_mode = 1 if request.form.get('maintenance_mode') else 0
            registration_open = 1 if request.form.get('registration_open') else 0
            max_daily = int(request.form['max_daily_complaints'])

            conn.execute("""UPDATE settings SET
                            ai_model=?, maintenance_mode=?, registration_open=?, max_daily_complaints=?
                            WHERE id=1""",
                         (ai_model, maintenance_mode, registration_open, max_daily))
            conn.commit()
            flash('Settings updated successfully!', 'success')

    conn.close()
    return render_template('admin_settings.html', admin=admin, settings=settings)

@app.route('/admin/export_csv')
@login_required
@admin_required
def export_csv():
    conn = get_db()
    data = conn.execute("SELECT e.*, u.name, u.username FROM entries e JOIN users u ON e.user_id = u.id").fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Student Name', 'Username', 'Exam', 'College', 'Status', 'Category', 'Urgency', 'Date'])
    for row in data:
        cw.writerow([row['id'], row['name'], row['username'], row['exam_name'], row['college_name'], row['status'], row['category'], row['urgency_score'], row['created_at']])

    output = si.getvalue()
    return Response(output, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=complaints.csv"})

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return render_template('home.html')

@app.route('/')
@login_required
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/form')
@login_required
def form():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('form.html', today=today)

@app.route('/ai_improve', methods=['POST'])
@login_required
def ai_improve():
    text = request.json['text']
    result = professional_report(text)
    return jsonify({"result": result})

@app.route('/ai_category', methods=['POST'])
@login_required
def ai_category():
    text = request.json['text']
    ai_data = analyze_complaint_with_groq(text)
    return jsonify({"category": ai_data.get('category', 'Other')})

@app.route('/ai_grammar', methods=['POST'])
@login_required
def ai_grammar():
    text = request.json['text']
    prompt = f"Convert this text to professional formal English: '{text}'"
    chat = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return jsonify({"result": chat.choices[0].message.content})

@app.route('/submit', methods=['POST'])
@login_required
def submit_report():
    try:
        exam_name = request.form.get('exam_name', '').strip()
        subject_name = request.form.get('subject_name', '').strip()
        college_name = request.form.get('college_name', '').strip()
        report_date = request.form.get('report_date', '').strip()
        description = request.form.get('description', '').strip()
        incident_state = request.form.get('incident_state', '').strip()
        incident_district = request.form.get('incident_district', '').strip()
        incident_city = request.form.get('incident_city', '').strip()
        category = request.form.get('category', '').strip() # category form se lo

        if not exam_name or not subject_name or not college_name:
            flash('Exam Name, Subject Name and College Name are required!', 'error')
            return redirect(url_for('form'))

        # AI
        ai_data = analyze_complaint_with_groq(description)
        ai_summary = ai_data['summary']
        if not category: category = ai_data['category'] # agar blank hai to AI se lo
        urgency_map = {'High': 9, 'Medium': 5, 'Low': 2}
        urgency_score = urgency_map.get(ai_data['priority'], 5)
        sentiment = get_sentiment(description)

        # FILE UPLOAD
        evidence_files = request.files.getlist('evidence')
        photos, videos, audios = [], [], []
        os.makedirs(UPLOAD_FOLDER_EVIDENCE, exist_ok=True)

        for file in evidence_files:
            if file and file.filename!= '' and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER_EVIDENCE, filename)
                file.save(filepath)
                ext = filename.rsplit('.', 1)[1].lower()
                if ext in {'png', 'jpg', 'jpeg', 'gif'}: photos.append(filename)
                elif ext == 'mp4': videos.append(filename)
                elif ext in {'mp3', 'wav'}: audios.append(filename)
                elif ext == 'pdf': photos.append(filename)

        # DB SAVE
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO entries
           (user_id, exam_name, subject_name, college_name, report_date, description,
            incident_state, incident_district, incident_city,
            photos, videos, audios, category, ai_summary, urgency_score, sentiment, status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (current_user.id, exam_name, subject_name, college_name, report_date, description,
         incident_state, incident_district, incident_city,
         json.dumps(photos), json.dumps(videos), json.dumps(audios),
         category, ai_summary, urgency_score, sentiment, 'Pending', datetime.now()))

        entry_id = c.lastrowid
        for f in photos + videos + audios:
            ext = f.rsplit('.',1)[1].lower()
            if ext == 'pdf': file_type = 'pdf'
            elif ext in {'png', 'jpg', 'jpeg', 'gif'}: file_type = 'photo'
            elif ext == 'mp4': file_type = 'video'
            else: file_type = 'audio'
            c.execute("INSERT INTO entry_files (entry_id, filename, file_type) VALUES (?,?,?)", (entry_id, f, file_type))

        conn.commit()
        conn.close()

        flash('Report Submitted Successfully with AI Analysis!', 'success')
        return redirect(url_for('report_list'))

    except Exception as e:
        print("SUBMIT ERROR:", e)
        flash(f'Error: {e}', 'error')
        return redirect(url_for('form'))

@app.route('/search')
@login_required
def search_page():
    conn = get_db()
    colleges = [row[0] for row in conn.execute(
        'SELECT DISTINCT college_name FROM entries WHERE college_name IS NOT NULL AND college_name!= "" ORDER BY college_name'
    ).fetchall()]
    exams = [row[0] for row in conn.execute(
        'SELECT DISTINCT exam_name FROM entries WHERE exam_name IS NOT NULL AND exam_name!= "" ORDER BY exam_name'
    ).fetchall()]
    conn.close()
    return render_template('search.html', colleges=colleges, exams=exams)

@app.route('/report/<int:id>')
@login_required
def view_report(id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    report = conn.execute('SELECT e.*, u.name, u.email FROM entries e JOIN users u ON e.user_id=u.id WHERE e.id =?', (id,)).fetchone()

    if report is None:
        conn.close()
        flash('Report not found!', 'error')
        return redirect(url_for('report_list'))

    if current_user.role!= 'admin' and report['user_id']!= current_user.id:
        conn.close()
        flash('You do not have permission to view this report.', 'error')
        return redirect(url_for('report_list'))

    report_dict = dict(report)
    for key in ['photos', 'videos', 'audios']:
        try:
            report_dict[key] = json.loads(report_dict[key]) if report_dict[key] else []
        except:
            report_dict[key] = []
    conn.close()

    report_dict['display_id'] = f"ELD-{report_dict['id']:03d}"

    if report_dict['report_date']:
        try:
            date_obj = datetime.strptime(report_dict['report_date'], '%Y-%m-%d')
            report_dict['report_date'] = date_obj.strftime('%d-%m-%Y')
        except:
            pass

    # Role nusar template
    if current_user.role == 'admin':
        return render_template('admin_detail.html', report=report_dict)
    else:
        return render_template('student_detail.html', report=report_dict)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_report(id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    report = conn.execute("SELECT * FROM entries WHERE id =?", (id,)).fetchone()

    if not report:
        conn.close()
        flash('Report not found', 'error')
        return redirect(url_for('report_list'))

    if current_user.role!= 'admin' and report['user_id']!= current_user.id:
        conn.close()
        flash('You do not have permission to delete this report.', 'error')
        return redirect(url_for('report_list'))

    for f in json.loads(report['photos'] or '[]') + json.loads(report['videos'] or '[]') + json.loads(report['audios'] or '[]'):
        try: os.remove(os.path.join(UPLOAD_FOLDER_EVIDENCE, f))
        except: pass

    conn.execute("DELETE FROM entries WHERE id =?", (id,))
    conn.commit()
    conn.close()
    flash('Report deleted Successfully!', 'success')
    return redirect(url_for('report_list'))

@app.route('/report')
@login_required
def report_list():
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'id')
    order = request.args.get('order', 'desc')
    exam_filter = request.args.get('exam', '').strip()
    college_filter = request.args.get('college', '').strip()

    all_reports = []
    conn = get_db()
    conn.row_factory = sqlite3.Row

    base_query = 'SELECT * FROM entries WHERE 1=1'
    params = []

    if current_user.role!= 'admin':
        base_query += ' AND user_id =?'
        params.append(current_user.id)

    if search:
        base_query += ' AND (exam_name LIKE? OR subject_name LIKE? OR college_name LIKE? OR description LIKE?)'
        search_term = f'%{search}%'
        params.extend([search_term] * 4)

    if exam_filter:
        base_query += ' AND exam_name LIKE?'
        params.append(f'%{exam_filter}%')
    if college_filter:
        base_query += ' AND college_name LIKE?'
        params.append(f'%{college_filter}%')

    valid_sorts = ['id', 'exam_name', 'subject_name', 'college_name', 'report_date']
    sort_column = 'id' if sort_by == 'display_id' else sort_by
    if sort_column not in valid_sorts: sort_column = 'id'
    sort_order = 'DESC' if order == 'desc' else 'ASC'
    base_query += f' ORDER BY {sort_column} {sort_order}'

    db_reports = conn.execute(base_query, params).fetchall()
    conn.close()

    for row in db_reports:
        report_dict = dict(row)
        report_dict['display_id'] = f"ELD-{report_dict['id']:03d}"
        report_dict['is_dummy'] = False
        report_dict['view_url'] = url_for('view_report', id=report_dict['id'])
        report_dict['delete_url'] = url_for('delete_report', id=report_dict['id'])

        report_dict['report_date_display'] = report_dict['report_date']
        if report_dict['report_date']:
            try:
                date_obj = datetime.strptime(report_dict['report_date'], '%Y-%m-%d')
                report_dict['report_date_display'] = date_obj.strftime('%d-%m-%Y')
            except: pass
        all_reports.append(report_dict)
         # HE 2 LINES ADD KAR - HACH RETURN AAHE
    dummy_reports = DUMMY_REPORTS if current_user.role == 'admin' else []
    return render_template('reports.html', reports=all_reports + dummy_reports, 
                           search=search, sort_by=sort_by, order=order,
                           exam_filter=exam_filter, college_filter=college_filter)


def get_db():
    db = sqlite3.connect(DB_PATH, timeout=20.0)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout = 20000")
    return db
@app.context_processor
def inject_notifications():
    # Sirf student ke liye count
    if current_user.is_authenticated and current_user.role == 'student':
        db = get_db()
        count = db.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (current_user.id,)).fetchone()[0]
        db.close()
        return dict(unread_count=count)
    return dict(unread_count=0)

@app.route('/student/notifications')
@login_required
def student_notifications():
    if current_user.role!= 'student':
        flash('Access Denied', 'error')
        return redirect(url_for('dashboard'))

    user_id = current_user.id
    filter_type = request.args.get('filter', 'all')
    db = get_db()
    query = "SELECT * FROM notifications WHERE user_id =?"
    if filter_type == 'unread':
        query += " AND is_read = 0"
    elif filter_type == 'read':
        query += " AND is_read = 1"
    query += " ORDER BY created_at DESC"

    notifications = db.execute(query, (user_id,)).fetchall()
    total = db.execute("SELECT COUNT(*) FROM notifications WHERE user_id =?", (user_id,)).fetchone()[0]
    unread_count = db.execute("SELECT COUNT(*) FROM notifications WHERE user_id =? AND is_read = 0", (user_id,)).fetchone()[0]
    db.close()
    return render_template('student_notifications.html', notifications=notifications, unread_count=unread_count, total=total, filter_type=filter_type)


@app.route('/student/notifications/<int:notif_id>/read')
@login_required
def mark_student_notification_read(notif_id):
    db = get_db()
    # FIX: current.id -> current_user.id
    db.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, current_user.id))
    db.commit()
    db.close()
    return redirect(url_for('student_notifications', filter=request.args.get('filter','all')))

@app.route('/student/notifications/mark-all-read')
@login_required
def mark_all_read():
    db = get_db()
    # FIX: current.id -> current_user.id
    db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (current_user.id,))
    db.commit()
    db.close()
    flash('All notifications marked as read', 'success')
    return redirect(url_for('student_notifications'))

@app.route('/student/notifications/<int:notif_id>/delete')
@login_required
def delete_notification(notif_id):
    db = get_db()
    db.execute("DELETE FROM notifications WHERE id = ? AND user_id = ?", (notif_id, current_user.id))
    db.commit()
    db.close()
    flash('Notification deleted', 'info')
    return redirect(url_for('student_notifications'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == '__main__':
    print("STARTING FLASK APP...")
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)