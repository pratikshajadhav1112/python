from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db
import os

app = Flask(__name__)
app.secret_key = 'Linkkiwi2026'

if not os.path.exists('myproject.db'):
    init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Form page - sirf form dikhao, submit alag route pe hoga
@app.route('/form')
def form():
    return render_template('form.html')

# Form submit handler - yahan data DB me save hoga
@app.route('/submit', methods=['POST'])
def submit():
    exam_name = request.form.get('exam_name')
    subject_name = request.form.get('subject_name')
    college_name = request.form.get('college_name')
    status = request.form.get('status')
    report_date = request.form.get('report_date')
    description = request.form.get('description')
    
    if not exam_name or not subject_name or not college_name:
        flash('Exam Name, Subject Name and College Name are required!', 'error')
        return redirect(url_for('form'))
    
    # DB me save karo
    conn = get_db()
    conn.execute(
        '''INSERT INTO entries 
           (exam_name, subject_name, college_name, status, report_date, description) 
           VALUES (?, ?, ?, ?, ?, ?)''',
        (exam_name, subject_name, college_name, status, report_date, description)
    )
    conn.commit()
    conn.close()
    
    flash('Report Submitted Successfully!', 'success')
    return redirect(url_for('report'))

# Report page - Dummy data + DB ka real data dono
@app.route('/report')
def report():
    # 1. Tera purana dummy dictionary data
    dummy_reports = [
        {
            "id": "ELD-001",
            "exam_name": "MSBTE Summer 2026",
            "subject_name": "MICROPROCESSOR PROGRAMMING",
            "college_name": "Government Polytechnic Hingoli",
            "status": "Pending",
            "report_date": "01-06-2026",
            "description": "Sample leak report",
            "created_at": "2026-06-01 10:00:00"
        },
        {
            "id": "ELD-002",
            "exam_name": "MSBTE Summer 2026",
            "subject_name": "Data Structure",
            "college_name": "Government Polytechnic Khamgaon",
            "status": "Resolved",
            "report_date": "02-06-2026",
            "description": "Sample resolved case",
            "created_at": "2026-06-02 11:00:00"
        }
    ]
    
    # 2. Database se naye submitted reports
    conn = get_db()
    db_reports = conn.execute(
        'SELECT * FROM entries ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    
    # 3. Dono merge - pehle dummy, fir DB data
    all_reports = dummy_reports + list(db_reports)
    
    return render_template("reports.html", reports=all_reports)

if __name__ == '__main__':
    print("STARTING FLASK APP...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)