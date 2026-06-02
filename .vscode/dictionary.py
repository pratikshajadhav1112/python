reports = [
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
        "college_name": "Government Polytechnic khamgaon",
        "status": "Resolved",
        "report_date": "02-06-2026"
    }
]

for report in reports:
    print("\nReport Details")
    print("-" * 30)

    for key, value in report.items():
        print(f"{key} : {value}")





 #second dictionary

        admin = {
    "admin_id": "ADM001",
    "name": "Pratiksha",
    "email": "pratiksha1113@gmail.com",
    "role": "Administrator",
    "total_reports": 120,
    "login_status": "Active"
}

for key, value in admin.items():
    print(key, ":", value)