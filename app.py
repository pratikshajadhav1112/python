from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify,abort
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import get_db, init_db
import os
import sqlite3
import json
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'Linkkiwi2026'
csrf = CSRFProtect(app)

# Upload folders
UPLOAD_FOLDER_PROFILE = 'static/uploads/profile_photos'
UPLOAD_FOLDER_EVIDENCE = 'static/uploads/evidence'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER_PROFILE, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_EVIDENCE, exist_ok=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page'

# DB initialize
if not os.path.exists('myproject.db'):
    init_db()

# User class for Flask-Login
# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, name, role='student', is_mobile_verified=0, is_email_verified=0, is_blocked=0):
        self.id = id
        self.username = username
        self.name = name  # HE NAVIN LINE
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
            name=user.get('name', 'User'), # HE ADD KAR
            role=user.get('role', 'student'),
            is_mobile_verified=user.get('is_mobile_verified', 0),
            is_email_verified=user.get('is_email_verified', 0),
            is_blocked=user.get('is_blocked', 0)
        )
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'wav'}

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
        
        # EmailJS ne verify zalela asel
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

        conn.execute('''INSERT INTO users
                     (name, username, email, mobile, password,
                      signup_ip, signup_user_agent, role, is_email_verified, is_mobile_verified)
                     VALUES (?,?,?,?,?,?,?,?,?,?)''',
                     (name, username, email, mobile, hashed_pw,
                      request.remote_addr, request.headers.get('User-Agent'),
                      'student', 1, 0)) # Email verified=1, Mobile=0 skip

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
        
        # FIX 1: Password SQL me mat check karo. Sirf user nikalo
        user_row = c.execute("SELECT * FROM users WHERE username = ? OR email = ?", 
                             (username_or_email, username_or_email)).fetchone()
        conn.close()

        if not user_row:
            flash('Invalid username or email', 'error')
            return render_template('login.html')

        user = dict(user_row)

        # FIX 2: Hash check yahi ek baar karo
        if not check_password_hash(user['password'], password):
            flash('Invalid password', 'error')
            return render_template('login.html')
        
        if user.get('is_email_verified', 0) == 0:
            flash('Please verify your email first', 'error')
            return render_template('login.html')
        
        if user.get('is_blocked', 0) == 1:
            flash('Your account is blocked. Contact admin.', 'error')
            return render_template('login.html')

        # Login success
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

        # Role nusar redirect
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))

    return render_template('login.html')
@app.route('/logout')
@login_required
def logout():
    logout_user() # session pop chi garaj nahi, Flask-Login swata handle karel
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        
        if current_user.role != 'admin':
            flash('You do not have admin permission', 'error')
            return redirect(url_for('dashboard')) # student dashboard la pathav
        
        return f(*args, **kwargs)
    return decorated_function
@app.route('/admin/dashboard')
@admin_required # session check kadhun takla
def admin_dashboard():
    conn = get_db()
    c = conn.cursor()

    # Stats kadhayche
    stats = {
        'total_users': c.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
        'total_reports': c.execute("SELECT COUNT(*) FROM entries").fetchone()[0],
        'pending': c.execute("SELECT COUNT(*) FROM entries WHERE status='Pending' OR status IS NULL").fetchone()[0],
        'resolved': c.execute("SELECT COUNT(*) FROM entries WHERE status='Resolved'").fetchone()[0],
    }
    conn.close()

    return render_template('admin_dashboard.html', user=current_user, stats=stats) # current_user pathavla

@app.route('/admin/users')
@admin_required # @login_required chya jagah @admin_required
def admin_users():
    conn = get_db()
    users = conn.execute("SELECT * FROM users WHERE role='student' ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin_users.html', user=current_user, users=[dict(u) for u in users])

@app.route('/admin/user/block/<int:user_id>')
@admin_required # @login_required chya jagah @admin_required
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
@admin_required # @login_required chya jagah @admin_required
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

# HA PAN ADD KAR - mhanunach admin_reports cha error yet hota
@app.route('/admin/reports')
@admin_required
def admin_reports():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    reports = conn.execute("SELECT e.*, u.name FROM entries e JOIN users u ON e.user_id=u.id ORDER BY e.id DESC").fetchall()
    conn.close()
    return render_template('admin_reports.html', user=current_user, reports=[dict(r) for r in reports])


@app.route('/admin/evidence', methods=['GET', 'POST'])
@admin_required
def admin_evidence():
    conn = get_db()
    query = '''SELECT e.id, e.exam, e.college, e.evidence_file, e.created_at, u.name, u.email 
               FROM entries e JOIN users u ON e.user_id = u.id 
               WHERE e.evidence_file IS NOT NULL'''
    params = []

    # Filter logic
    exam = request.args.get('exam')
    file_type = request.args.get('file_type')
    if exam:
        query += ' AND e.exam LIKE ?'
        params.append(f'%{exam}%')
    if file_type == 'image':
        query += ' AND e.evidence_file LIKE ?'
        params.append('%.jpg%')
    elif file_type == 'pdf':
        query += ' AND e.evidence_file LIKE ?'
        params.append('%.pdf%')
        
    query += ' ORDER BY e.created_at DESC'
    files = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('admin_evidence.html', files=files)

@app.route('/admin/evidence/bulk_download', methods=['POST'])
@admin_required
def bulk_download():
    file_ids = request.form.getlist('file_ids')
    conn = get_db()
    files = conn.execute(f"SELECT evidence_file FROM entries WHERE id IN ({','.join('?'*len(file_ids))})", file_ids).fetchall()
    
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for f in files:
            filepath = os.path.join('static/uploads', f['evidence_file'])
            if os.path.exists(filepath):
                zf.write(filepath, f['evidence_file'])
    memory_file.seek(0)
    return send_file(memory_file, download_name='evidence_files.zip', as_attachment=True)
    
        #stdudent login dashboard
@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    conn = get_db()
    
    # 1. Pie chart sathi: Pending vs Resolved vs In Progress
    status_data = conn.execute("SELECT status, COUNT(*) as count FROM entries GROUP BY status").fetchall()
    status_labels = [s['status'] for s in status_data]
    status_counts = [s['count'] for s in status_data]
    
    # 2. Bar chart: Reports per Month
    monthly_reports = conn.execute("""
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
        FROM entries GROUP BY month ORDER BY month LIMIT 6
    """).fetchall()
    report_months = [m['month'] for m in monthly_reports]
    report_counts = [m['count'] for m in monthly_reports]
    
    # 3. Line chart: Users per Month
    monthly_users = conn.execute("""
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
        FROM users WHERE role='user' GROUP BY month ORDER BY month LIMIT 6
    """).fetchall()
    user_months = [m['month'] for m in monthly_users]
    user_counts = [m['count'] for m in monthly_users]
    
    conn.close()
    return render_template('admin_analytics.html', 
                           status_labels=status_labels, status_counts=status_counts,
                           report_months=report_months, report_counts=report_counts,
                           user_months=user_months, user_counts=user_counts)
@app.route('/admin/notifications')
@admin_required
def admin_notifications():
    conn = get_db()
    notes = conn.execute("SELECT * FROM notifications ORDER BY created_at DESC").fetchall()
    # Saari read kar do
    conn.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()
    return render_template('admin_notifications.html', notes=notes)

# Sidebar me badge ke liye
@app.context_processor
def inject_notifications():
    if 'user_id' in session:
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0").fetchone()[0]
        return dict(unread_count=count)
    return dict(unread_count=0)

from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    conn = get_db()
    admin = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()

    if request.method == 'POST':
        # 1. Password Change
        old_pass = request.form['old_password']
        new_pass = request.form['new_password']
        
        if check_password_hash(admin['password'], old_pass):
            hashed = generate_password_hash(new_pass)
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, session['user_id']))
            conn.commit()
            flash('Password updated successfully', 'success')
        else:
            flash('Old password is wrong', 'danger')
    
    conn.close()
    return render_template('admin_settings.html', admin=admin)
@app.route('/dashboard')
@login_required
def dashboard():
    # Admin asel tar admin panel
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    # Student asel tar home.html
    return render_template('home.html') # user_dashboard.html nahi
    
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

@app.route('/submit', methods=['POST'])
@login_required
def submit_report():
    try:
        exam_name = request.form.get('exam_name', '').strip()
        subject_name = request.form.get('subject_name', '').strip()
        college_name = request.form.get('college_name', '').strip()
        report_date = request.form.get('report_date', '').strip()
        description = request.form.get('description', '').strip()

        if not exam_name or not subject_name or not college_name:
            flash('Exam Name, Subject Name and College Name are required!', 'error')
            return redirect(url_for('form'))

        incident_state = request.form.get('incident_state', '').strip()
        incident_district = request.form.get('incident_district', '').strip()
        incident_city = request.form.get('incident_city', '').strip()

        # Evidence files handle kar
        evidence_files = request.files.getlist('evidence')
        photos, videos, audios = [], [], []

        for file in evidence_files:
            if file and file.filename!= '' and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER_EVIDENCE, filename)
                file.save(filepath)

                ext = filename.rsplit('.', 1)[1].lower()
                if ext in {'png', 'jpg', 'jpeg', 'gif'}:
                    photos.append(filename)
                elif ext == 'mp4':
                    videos.append(filename)
                elif ext in {'mp3', 'wav'}:
                    audios.append(filename)

        conn = get_db()
        conn.execute(
            '''INSERT INTO entries
               (user_id, exam_name, subject_name, college_name, report_date, description,
                incident_state, incident_district, incident_city,
                photos, videos, audios)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (current_user.id, exam_name, subject_name, college_name, report_date, description,
             incident_state, incident_district, incident_city,
             json.dumps(photos), json.dumps(videos), json.dumps(audios))
        )
        conn.commit()
        conn.close()

        flash('Report Submitted Successfully!', 'success')
        return redirect(url_for('report_list'))
    except Exception as e:
        print("ERROR:", e)
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
    report = conn.execute('SELECT * FROM entries WHERE id =?', (id,)).fetchone()

    if report is None:
        conn.close()
        flash('Report not found!', 'error')
        return redirect(url_for('report_list'))

    # FIX: Admin OR Owner can view
    if current_user.role != 'admin' and report['user_id'] != current_user.id:
        conn.close()
        flash('You do not have permission to view this report.', 'error')
        return redirect(url_for('report_list'))

    report_dict = dict(report)
    report_dict['photos'] = json.loads(report_dict['photos']) if report_dict['photos'] else []
    report_dict['videos'] = json.loads(report_dict['videos']) if report_dict['videos'] else []
    report_dict['audios'] = json.loads(report_dict['audios']) if report_dict['audios'] else []
    conn.close()

    report_dict['display_id'] = f"ELD-{report_dict['id']:03d}"
    report_dict['is_dummy'] = False

    if report_dict['report_date']:
        try:
            date_obj = datetime.strptime(report_dict['report_date'], '%Y-%m-%d')
            report_dict['report_date'] = date_obj.strftime('%d-%m-%Y')
        except:
            pass

    return render_template('detail.html', report=report_dict)
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

    # FIX: Admin OR Owner can delete
    if current_user.role != 'admin' and report['user_id'] != current_user.id:
        conn.close()
        flash('You do not have permission to delete this report.', 'error')
        return redirect(url_for('report_list'))

    # Files bhi delete karo
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
        
        # FIX HERE: 'id' use karo 'report_id' ki jagah
        report_dict['view_url'] = url_for('view_report', id=report_dict['id'])
        report_dict['delete_url'] = url_for('delete_report', id=report_dict['id'])

        report_dict['report_date_display'] = report_dict['report_date']
        if report_dict['report_date']:
            try:
                date_obj = datetime.strptime(report_dict['report_date'], '%Y-%m-%d')
                report_dict['report_date_display'] = date_obj.strftime('%d-%m-%Y')
            except: pass
        all_reports.append(report_dict)

    return render_template("reports.html", reports=all_reports, search=search, sort_by=sort_by, order=order, exam_filter=exam_filter, college_filter=college_filter)
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == '__main__':
    print("STARTING FLASK APP...")
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)