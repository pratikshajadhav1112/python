from flask import Flask, render_template, request

app = Flask(__name__)


# Home page
@app.route('/')
def home():
    return render_template('home.html')


# About page
@app.route('/about')
def about():
    return render_template('about.html')


# Reports page
@app.route('/report')
def report():

    reports_list = [
        {
            "report_id": "ELD-001",
            "exam_name": "MSBTE Summer 2026",
            "subject_name": "MICROPROCESSOR PROGRAMMING",
            "college_name": "Government Polytechnic Hingoli",
            "status": "Pending",
            "report_date": "01-06-2026"
        },
        {
            "report_id": "ELD-002",
            "exam_name": "MSBTE Summer 2026",
            "subject_name": "Data Structure",
            "college_name": "Government Polytechnic Khamgaon",
            "status": "Resolved",
            "report_date": "02-06-2026"
        },
        {
            "report_id": "ELD-003",
            "exam_name": "MSBTE Summer 2026",
            "subject_name": "JAVA PROGRAMMING",
            "college_name": "Government Polytechnic Parbhani",
            "status": "Solved",
            "report_date": "04-06-2025"
        },
        {
            "report_id": "ELD-004",
            "exam_name": "MSBTE Summer 2024",
            "subject_name": "DATABASE MANAGEMENT SYSTEM",
            "college_name": "Government Polytechnic Nanded",
            "status": "Resolved",
            "report_date": "02-06-2024"
        }
    ]


    return render_template("reports.html", reports=reports_list)


# Form page
@app.route('/form')
def form():
    return render_template('form.html')


# Form submit handler
@app.route('/submit', methods=['POST'])
def submit():

    data = {
        "exam_name": request.form.get("exam_name"),
        "subject_name": request.form.get("subject_name"),
        "college_name": request.form.get("college_name"),
        "status": request.form.get("status"),
        "report_date": request.form.get("report_date"),
        "description": request.form.get("description")
    }

    print("FORM DATA RECEIVED:", data)

    return "Report Submitted Successfully!"


if __name__ == '__main__':
    print("STARTING FLASK APP...")
    app.run(debug=True)