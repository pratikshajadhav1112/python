from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'Linkkiwi2026'

if not os.path.exists('myproject.db'):
    init_db()

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
DUMMY_COUNT = len(DUMMY_REPORTS)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit_report():
    exam_name = request.form.get('exam_name','').strip()
    subject_name = request.form.get('subject_name','').strip()
    college_name = request.form.get('college_name','').strip()
    status = request.form.get('status','').strip()
    report_date = request.form.get('report_date','').strip()
    description = request.form.get('description','').strip()

    print("=== FORM DATA ===")  # 👈 Debug line
    print(f"Exam: {exam_name}, Subject: {subject_name}")
    print(f"College: {college_name}, Date: {report_date}")
    print(f"Status: {status}, Desc Length: {len(description)}")


    
    if not exam_name or not subject_name or not college_name:
        flash('Exam Name, Subject Name and College Name are required!', 'error')
        return redirect(url_for('form'))
    
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
    return redirect(url_for('report_list'))

@app.route('/report/<int:id>')
def view_report(id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    report = conn.execute('SELECT * FROM entries WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if report is None:
        flash('Report not found!', 'error')
        return redirect(url_for('report_list'))
    
    report_dict = dict(report)
    report_dict['display_id'] = f"ELD-{report_dict['id'] + DUMMY_COUNT:03d}"
    report_dict['is_dummy'] = False
    
    if report_dict['report_date']:
        try:
            date_obj = datetime.strptime(report_dict['report_date'], '%Y-%m-%d')
            report_dict['report_date'] = date_obj.strftime('%d-%m-%Y')
        except:
            pass
    
    return render_template('detail.html', report=report_dict)

@app.route('/report/dummy/<int:id>') 
def view_dummy_report(id):
    dummy = next((r for r in DUMMY_REPORTS if r['id'] == id), None)
    
    if dummy is None:
        flash('Dummy report not found!', 'error')
        return redirect(url_for('report_list'))
    
    report_dict = dummy.copy()
    report_dict['display_id'] = f"ELD-{report_dict['id']:03d}"
    report_dict['is_dummy'] = True
    
    return render_template('detail.html', report=report_dict)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_report(id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    report = conn.execute('SELECT * FROM entries WHERE id = ?', (id,)).fetchone()
    
    if report is None:
        flash('Report not found!', 'error')
        conn.close()
        return redirect(url_for('report_list'))
    
    conn.execute("DELETE FROM entries WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash('Report deleted Successfully!', 'success')
    return redirect(url_for('report_list'))

@app.route('/report')
def report_list():
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'display_id')
    order = request.args.get('order', 'asc')
    
    all_reports = []

    # 1. Dummy Reports Filter
    filtered_dummy = []
    for dummy in DUMMY_REPORTS:
        if search:
            search_lower = search.lower()
            if any(search_lower in str(dummy.get(field, '')).lower() 
                   for field in ['exam_name', 'subject_name', 'college_name', 'status', 'description']):
                filtered_dummy.append(dummy)
        else:
            filtered_dummy.append(dummy)
    
    for dummy in filtered_dummy:
        dummy_copy = dummy.copy()
        dummy_copy['display_id'] = f"ELD-{dummy['id']:03d}"
        dummy_copy['view_url'] = url_for('view_dummy_report', id=dummy['id'])
        dummy_copy['delete_url'] = None
        dummy_copy['is_dummy'] = True
        all_reports.append(dummy_copy)
    
    # 2. Database Query
    conn = get_db()
    conn.row_factory = sqlite3.Row
    
    valid_sorts = ['id', 'exam_name', 'subject_name', 'college_name', 'status', 'report_date']
    sort_column = 'id' if sort_by == 'display_id' else sort_by
    if sort_column not in valid_sorts:
        sort_column = 'id'
    
    sort_order = 'DESC' if order == 'desc' else 'ASC'
    
    if search:
        query = f'''
            SELECT * FROM entries 
            WHERE exam_name LIKE ? OR subject_name LIKE ? OR college_name LIKE ? 
               OR status LIKE ? OR description LIKE ?
            ORDER BY {sort_column} {sort_order}
        '''
        db_reports = conn.execute(query, (f'%{search}%',) * 5).fetchall()
    else:
        query = f'SELECT * FROM entries ORDER BY {sort_column} {sort_order}'
        db_reports = conn.execute(query).fetchall()
    
    conn.close()
    
    # DB reports Process
    db_index = 1
    for row in db_reports:
        report_dict = dict(row)
        report_dict['display_id'] = f"ELD-{db_index+ DUMMY_COUNT:03d}"
        db_index +=1
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
    
    # Final Sort by display_id
    if sort_by == 'display_id':
        reverse = True if order == 'desc' else False
        all_reports.sort(key=lambda x: x['display_id'], reverse=reverse)
    
    return render_template("reports.html", 
                         reports=all_reports, 
                         search=search, 
                         sort_by=sort_by, 
                         order=order)

if __name__ == '__main__':
    print("STARTING FLASK APP...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)