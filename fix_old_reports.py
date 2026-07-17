import sqlite3
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_complaint_with_groq(text):
    if not os.getenv("GROQ_API_KEY"): return {"category": "Other", "priority": "Medium", "summary": text[:100]}
    
    prompt = f"""You are an exam complaint classifier.
    Complaint: "{text}"
    
    Rules:
    1. If text has "leak, paper leak" -> category = "Paper Leak"
    2. If text has "cheating, mobile, copy" -> category = "Cheating"
    3. If text has "invigilator, teacher, staff" -> category = "Invigilator Issue"
    4. If text has "server, website, technical, login" -> category = "Technical Issue"
    5. If text has "harassment, rude, abuse" -> category = "Harassment"
    6. Else -> category = "Other"
    
    Also give priority: High/Medium/Low and 1 line summary.
    
    Return ONLY JSON: {{"category": "...", "priority": "...", "summary": "..."}}"""
    
    try:
        chat = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(chat.choices[0].message.content)
    except Exception as e:
        print("GROQ ERROR:", e)
        return {"category": "Other", "priority": "Medium", "summary": text[:100]}

def get_sentiment(text):
    prompt = f"What is sentiment of: '{text}'. Reply only: Angry, Normal, Urgent"
    chat = groq_client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
    return chat.choices[0].message.content

conn = sqlite3.connect('myproject.db')
c = conn.cursor()

# Sirf wo report uthao jisme AI data None hai
reports = c.execute("SELECT id, description FROM entries WHERE ai_summary IS NULL OR ai_summary = 'None'").fetchall()

print(f"Found {len(reports)} old reports to fix")

for report_id, description in reports:
    print(f"Processing Report ID: {report_id}")
    ai_data = analyze_complaint_with_groq(description)
    sentiment = get_sentiment(description)
    urgency_map = {'High': 9, 'Medium': 5, 'Low': 2}
    urgency_score = urgency_map.get(ai_data['priority'], 5)

    c.execute("""UPDATE entries SET 
        category=?, ai_summary=?, urgency_score=?, sentiment=? 
        WHERE id=?""",
        (ai_data['category'], ai_data['summary'], urgency_score, sentiment, report_id))

conn.commit()
conn.close()
print("All old reports updated with AI!")