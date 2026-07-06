from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import get_db, init_db
import os
import sqlite3
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'Linkkiwi2026'
csrf = CSRFProtect(app)

# Email Config - TUZE DETAILS ITHE BADAL
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'pratikshaj@gmail.com' # TUZHA GMAIL
app.config['MAIL_PASSWORD'] = 'pratiksha@11' 

mail = Mail(app)

# Upload folders
UPLOAD_FOLDER_PROFILE = 'static/uploads/profile_photos'
UPLOAD_FOLDER_ID = 'static/uploads/id_proofs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER_PROFILE, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_ID, exist_ok=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page'

# DB initialize
if not os.path.exists('myproject.db'):
    init_db()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, role='student', is_mobile_verified=0, is_blocked=0):
        self.id = id
        self.username = username
        self.role = role
        self.is_mobile_verified = is_mobile_verified
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
            role=user.get('role', 'student'),
            is_mobile_verified=user.get('is_mobile_verified', 0),
            is_blocked=user.get('is_blocked', 0)
        )
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    """Email var OTP pathvato"""
    try:
        msg = Message(
            subject="LinkKiwi OTP Verification",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )

        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">LinkKiwi</h1>
                </div>
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333; margin-top: 0;">Email Verification</h2>
                    <p style="color: #666; font-size: 16px;">Your verification code is:</p>
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 8px; margin: 25px 0;">
                        <h1 style="margin: 0; letter-spacing: 8px; font-size: 32px;">{otp}</h1>
                    </div>
                    <p style="color: #666; font-size: 14px;">This OTP is valid for 5 minutes.</p>
                    <p style="color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        If you didn't request this, please ignore this email. Do not share this OTP.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        mail.send(msg)
        print(f"OTP {otp} sent to {email}")
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

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

        if not all([name, username, email, mobile, password]):
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return redirect(url_for('register'))

        if len(mobile)!= 10 or not mobile.isdigit():
            flash('Mobile number must be 10 digits!', 'error')
            return redirect(url_for('register'))

        conn = get_db()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ? OR mobile = ?',
                                     (username, email, mobile)).fetchone()

        if existing_user:
            flash('Username, Email or Mobile already exists!', 'error')
            conn.close()
            return redirect(url_for('register'))

        # Profile photo optional
        profile_photo = request.files.get('profile_photo')
        profile_path = ''

        if profile_photo and profile_photo.filename!= '' and allowed_file(profile_photo.filename):
            profile_filename = secure_filename(f"{datetime.now().timestamp()}_{profile_photo.filename}")
            profile_path = os.path.join(UPLOAD_FOLDER_PROFILE, profile_filename)
            profile_photo.save(profile_path)

        hashed_pw = generate_password_hash(password)
        otp = generate_otp()

        conn.execute('''INSERT INTO users
                     (name, username, email, mobile, password, profile_photo,
                      signup_ip, signup_user_agent, mobile_otp, otp_generated_at, role, is_mobile_verified)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                     (name, username, email, mobile, hashed_pw, profile_path,
                      request.remote_addr, request.headers.get('User-Agent'),
                      otp, datetime.now(), 'student', 0))

        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.commit()
        conn.close()

        # FIXED: send_otp_email - small letters
        if send_otp_email(email, otp):
            flash(f'Registration successful! OTP sent to {email}. Check inbox & spam.', 'success')
        else:
            flash('Registration successful but failed to send OTP. Contact admin.', 'warning')

        return redirect(url_for('verify_otp', user_id=user_id))

    return render_template('register.html')

@app.route('/verify_otp/<int:user_id>', methods=['GET', 'POST'])
def verify_otp(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id =?', (user_id,)).fetchone()
    if not user:
        conn.close()
        flash('User not found!', 'error')
        return redirect(url_for('register'))

    if request.method == 'POST':
        entered_otp = request.form['otp']
        if user['mobile_otp'] == entered_otp:
            conn.execute('UPDATE users SET is_mobile_verified = 1, mobile_otp = NULL WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            flash('Email verified! Now you can login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Try again.', 'danger')

    conn.close()
    return render_template('verify_otp.html', email=user['email'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        user_row = conn.execute('SELECT * FROM users WHERE username =?', (username,)).fetchone()
        conn.close()

        if user_row:
            user = dict(user_row)
            if user.get('is_blocked', 0):
                flash('Your account has been blocked. Contact admin.', 'danger')
                return redirect(url_for('login'))
            if not user['is_mobile_verified']:
                flash('Please verify your email first.', 'warning')
                return redirect(url_for('verify_otp', user_id=user['id']))
            if check_password_hash(user['password'], password):
                user_obj = User(
                    id=user['id'],
                    username=user['username'],
                    role=user.get('role', 'student'),
                    is_mobile_verified=user.get('is_mobile_verified', 0),
                    is_blocked=user.get('is_blocked', 0)
                )
                login_user(user_obj)
                session['username'] = username
                session['role'] = user.get('role', 'student')
                flash(f'Welcome back, {username}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))

        flash('Invalid username or password!', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    session.pop('role', None)
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# ============ PROTECTED ROUTES ============
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

        conn = get_db()
        conn.execute(
            '''INSERT INTO entries
               (user_id, exam_name, subject_name, college_name, report_date, description)
               VALUES (?,?,?,?,?,?)''',
            (current_user.id, exam_name, subject_name, college_name, report_date, description)
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
    if current_user.role!= 'admin':
        flash('You do not have permission to view this report.', 'error')
        return redirect(url_for('report_list'))

    conn = get_db()
    conn.row_factory = sqlite3.Row
    report = conn.execute('SELECT * FROM entries WHERE id =?', (id,)).fetchone()
    files = conn.execute('SELECT * FROM entry_files WHERE entry_id =?', (id,)).fetchall()

    if report is None:
        conn.close()
        flash('Report not found!', 'error')
        return redirect(url_for('report_list'))

    report_dict = dict(report)
    report_dict['files'] = [dict(f) for f in files]
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
    if current_user.role!= 'admin':
        flash('You do not have permission to delete reports.', 'error')
        return redirect(url_for('report_list'))

    conn = get_db()
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
    order = request.args.get('order', 'asc')
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

    count_query = base_query.replace('SELECT *', 'SELECT COUNT(*)')
    db_count = conn.execute(count_query, params).fetchone()[0]

    # Dummy Reports - Sirf DB empty asel tar
    if db_count == 0:
        for dummy in DUMMY_REPORTS:
            if not search or any(search.lower() in str(dummy.get(field, '')).lower()
                   for field in ['exam_name', 'subject_name', 'college_name', 'description']):
                dummy_copy = dummy.copy()
                dummy_copy['display_id'] = f"ELD-{dummy['id']:03d}"
                dummy_copy['view_url'] = '#'
                dummy_copy['delete_url'] = None
                dummy_copy['is_dummy'] = True
                all_reports.append(dummy_copy)

    # Sorting
    valid_sorts = ['id', 'exam_name', 'subject_name', 'college_name', 'report_date']
    sort_column = 'id' if sort_by == 'display_id' else sort_by
    if sort_column not in valid_sorts:
        sort_column = 'id'
    sort_order = 'DESC' if order == 'desc' else 'ASC'

    if search:
        base_query += ' AND (exam_name LIKE? OR subject_name LIKE? OR college_name LIKE? OR description LIKE?)'
        search_term = f'%{search}%'
        params.extend([search_term] * 4)

    if exam_filter:
        base_query += ' AND exam_name =?'
        params.append(exam_filter)
    if college_filter:
        base_query += ' AND college_name =?'
        params.append(college_filter)

    base_query += f' ORDER BY {sort_column} {sort_order}'

    db_reports = conn.execute(base_query, params).fetchall()
    conn.close()

    for row in db_reports:
        report_dict = dict(row)
        report_dict['display_id'] = f"ELD-{report_dict['id']:03d}"
        report_dict['is_dummy'] = False
        report_dict['view_url'] = url_for('view_report', id=report_dict['id'])
        report_dict['delete_url'] = url_for('delete_report', id=report_dict['id'])
        if report_dict['report_date']:
            try:
                date_obj = datetime.strptime(report_dict['report_date'], '%Y-%m-%d')
                report_dict['report_date'] = date_obj.strftime('%d-%m-%Y')
            except:
                pass
        all_reports.append(report_dict)

    return render_template("reports.html",
                         reports=all_reports,
                         search=search,
                         sort_by=sort_by,
                         order=order)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == '__main__':
    print("STARTING FLASK APP...")
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
