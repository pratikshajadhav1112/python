from flask import Flask, render_template,requst,redirect, url_for,flash
app = Flask(__name__)
app.secret_key = 'linkwivi2026'






_reports = [
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
    