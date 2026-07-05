from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'Linkkiwi2026'
csrf = CSRFProtect(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page'

# DB initialize karo agar exist nahi karti
if not os.path.exists('myproject.db'):
    init_db()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, role='student'):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user_row = conn.execute('SELECT * FROM users WHERE id =?', (user_id,)).fetchone()
    conn.close()
    if user_row:
        user = dict(user_row)
        return User(id=user['id'], username=user['username'], role=user.get('role', 'student'))
    return None

DUMMY_REPORTS = [
    {
        "id": 1,
        "exam_name": "MSBTE Summer 2026",
        "subject_name": "MICROPROCESSOR PROGRAMMING",
        "college_name": "Government Polytechnic Hingoli",
        "status": "Pending",
        "report_date": "01-06-2026",
        "description": "Sample leak report for testing. This is a dummy entry.",
        "is_dummy": True
    },
    {
        "id": 2,
        "exam_name": "MSBTE Summer 2026",
        "subject_name": "Data Structure",
        "college_name": "Government Polytechnic Khamgaon",
        "status": "Resolved",
        "report_date": "02-06-2026",
        "description": "Sample resolved case for testing. This is a dummy entry.",
        "is_dummy": True
    }
]

# ============ AUTH ROUTES ============
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Username and Password required!', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return redirect(url_for('register'))

        conn = get_db()
        existing = conn.execute('SELECT * FROM users WHERE username =?', (username,)).fetchone()

        if existing:
            flash('Username already exists!', 'error')
            conn.close()
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password, role) VALUES (?,?,?)',
                     (username, hashed_pw, 'student'))
        conn.commit()
        conn.close()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ✅ FIX 1: Function nav 'login' pahije, 'login_required' nahi
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
            if check_password_hash(user['password'], password):
                user_obj = User(id=user['id'], username=user['username'], role=user.get('role', 'student'))
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
    session.pop('username',None)
    session.pop('role',None)
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# ============ PROTECTED ROUTES ============
@app.route('/')
@login_required
def home():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM entries').fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM entries WHERE status = 'Pending'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM entries WHERE status = 'Resolved'").fetchone()[0]
    conn.close()
    return render_template('home.html', total=total, pending=pending, resolved=resolved)

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
        status = request.form.get('status', 'Pending').strip()
        report_date = request.form.get('report_date', '').strip()
        description = request.form.get('description', '').strip()

        if not exam_name or not subject_name or not college_name:
            flash('Exam Name, Subject Name and College Name are required!', 'error')
            return redirect(url_for('form'))

        conn = get_db()
        conn.execute(
            '''INSERT INTO entries
               (user_id, exam_name, subject_name, college_name, status, report_date, description)
               VALUES (?,?,?,?,?,?,?)''',
            (current_user.id, exam_name, subject_name, college_name, status, report_date, description)
        )
        conn.commit()
        conn.close()

        flash('Report Submitted Successfully!', 'success')
        return redirect(url_for('report_list'))
    except Exception as e:
        print("ERROR :", e)
        flash(f'Error: {e}', 'error')
        return redirect(url_for('form'))

@app.route('/search')
@login_required
def search_page():
    conn = get_db()
    statuses = [row[0] for row in conn.execute(
        'SELECT DISTINCT status FROM entries WHERE status IS NOT NULL AND status!= "" ORDER BY status'
    ).fetchall()]
    colleges = [row[0] for row in conn.execute(
        'SELECT DISTINCT college_name FROM entries WHERE college_name IS NOT NULL AND college_name!= "" ORDER BY college_name'
    ).fetchall()]
    exams = [row[0] for row in conn.execute(
        'SELECT DISTINCT exam_name FROM entries WHERE exam_name IS NOT NULL AND exam_name!= "" ORDER BY exam_name'
    ).fetchall()]
    conn.close()
    return render_template('search.html', statuses=statuses, colleges=colleges, exams=exams)

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
    status_filter = request.args.get('status', '').strip()
    exam_filter = request.args.get('exam', '').strip()
    college_filter = request.args.get('college', '').strip()

    all_reports = []
    conn = get_db()
    conn.row_factory = sqlite3.Row

    base_query = 'SELECT * FROM entries WHERE 1=1'
    params = []

    # ✅ FIX 2: AND chya adhi space pahije
    if current_user.role!= 'admin':
        base_query += ' AND user_id =?'
        params.append(current_user.id)

    # Count sathi same query vapra
    count_query = base_query.replace('SELECT *', 'SELECT COUNT(*)')
    db_count = conn.execute(count_query, params).fetchone()[0]

    # Dummy Reports - Sirf DB empty asel tar
    if db_count == 0:
        for dummy in DUMMY_REPORTS:
            if not search or any(search.lower() in str(dummy.get(field, '')).lower()
                   for field in ['exam_name', 'subject_name', 'college_name', 'status', 'description']):
                dummy_copy = dummy.copy()
                dummy_copy['display_id'] = f"ELD-{dummy['id']:03d}"
                dummy_copy['view_url'] = '#'
                dummy_copy['delete_url'] = None
                dummy_copy['is_dummy'] = True
                all_reports.append(dummy_copy)

    # Sorting
    valid_sorts = ['id', 'exam_name', 'subject_name', 'college_name', 'status', 'report_date']
    sort_column = 'id' if sort_by == 'display_id' else sort_by
    if sort_column not in valid_sorts:
        sort_column = 'id'
    sort_order = 'DESC' if order == 'desc' else 'ASC'

    # ✅ FIX 3: LIKE? aani =? madhe space pahije
    if search:
        base_query += ' AND (exam_name LIKE ? OR subject_name LIKE ? OR college_name LIKE ? OR status LIKE ? OR description LIKE ?)'
        search_term = f'%{search}%'
        params.extend([search_term] * 5)
    if status_filter:
        base_query += ' AND status = ?'
        params.append(status_filter)
    if exam_filter:
        base_query += ' AND exam_name = ?'
        params.append(exam_filter)
    if college_filter:
        base_query += ' AND college_name = ?'
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