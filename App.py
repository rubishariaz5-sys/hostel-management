from flask import Flask, render_template, request, jsonify, send_file
import mysql.connector
import threading
import time
import io
import webbrowser
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = Flask(__name__)

# IN-MEMORY GLOBAL LEDGER ENGINE
COMPLAINTS_GLOBAL_DB = [
    {"id": 1, "user": "admin", "title": "Electrical Leakage Block A", "description": "Short circuit issues in Room 105 lights.", "status": "Pending"},
    {"id": 2, "user": "areen_zahra", "title": "Water Pump Pipeline", "description": "No water pressure in second-floor washrooms.", "status": "Solved"}
]

VOUCHERS_GLOBAL_DB = [
    {"id": 1, "user": "admin", "amount": "45000", "channel": "JazzCash", "tx_id": "TXN991827361", "status": "Pending"}
]

MESS_GLOBAL_PLAN = [
    {"day": "Monday", "breakfast": "Omelette Paratha + Chai 🍳", "lunch": "Daal Chawal + Aloo Bhujia 🍛", "dinner": "Chicken Karahi + Roti 🍗"},
    {"day": "Tuesday", "breakfast": "Chana Puri Special 🥞", "lunch": "Sabzi Pulao + Raita 🍚", "dinner": "Aloo Qeema + Naan 🥩"},
    {"day": "Wednesday", "breakfast": "Fried Egg + Toast 🍞", "lunch": "Kadhi Pakora + White Rice 🥣", "dinner": "Mix Sabzi + Tandoori Roti 🥕"},
    {"day": "Thursday", "breakfast": "Allo Paratha Premium 🥞", "lunch": "Chicken Biryani Double Shahi 👑", "dinner": "Daal Makhni + Chapati 🍛"},
    {"day": "Friday", "breakfast": "Boiled Egg + Tea ☕", "lunch": "Seasonal Veg + Plain Rice 🍚", "dinner": "Chicken Korma + Naan 🍗"},
    {"day": "Saturday", "breakfast": "Halwa Puri Delight 🥞", "lunch": "Lobiya Salan + Roti 🍛", "dinner": "Beef Haleem + Tarka Rice 🥣"},
    {"day": "Sunday", "breakfast": "Special Omelette Toast 🍳", "lunch": "Chicken Pulao Classic 🍚", "dinner": "Daal Mash + Salad 🍛"}
]

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",       
        password="",       
        database="hostaldb"
    )

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/metrics', methods=['GET'])
def dynamic_system_metrics_api():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM students WHERE status='Paid'")
        paid_students = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        revenue = paid_students * 45000
        arrears = (total_students - paid_students) * 45000
        return jsonify({
            "total_students": f"{total_students} Students",
            "revenue": f"Rs. {revenue:,}",
            "arrears": f"Rs. {arrears:,}"
        })
    except:
        return jsonify({"total_students": "1 Student", "revenue": "Rs. 45,000", "arrears": "Rs. 0"})

@app.route('/api/students', methods=['GET', 'POST', 'DELETE', 'PUT'])
def manage_students():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute("SELECT student_id AS id, name, roll_number AS roll, room_number AS room, gmail, status FROM students")
            students = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify(students)

        elif request.method == 'POST':
            data = request.json
            cursor.execute(
                "INSERT INTO students (student_id, name, roll_number, room_number, gmail, status) VALUES (%s, %s, %s, %s, %s, %s)",
                (data['id'], data['name'], data['roll'], data['room'], data['gmail'].lower(), data['status'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True})

        elif request.method == 'PUT':
            data = request.json
            cursor.execute(
                "UPDATE students SET name=%s, roll_number=%s, room_number=%s, gmail=%s, status=%s WHERE student_id=%s",
                (data['name'], data['roll'], data['room'], data['gmail'].lower(), data['status'], data['id'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True})

        elif request.method == 'DELETE':
            data = request.json
            cursor.execute("DELETE FROM students WHERE student_id = %s", (data['id'],))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"success": True})
    except:
        return jsonify([{"id": "STU-001", "name": "Areen Zahra", "roll": "2026-IT-09", "room": "204", "gmail": "admin@gmail.com", "status": "Paid"}])

@app.route('/api/visitors', methods=['GET'])
def manage_visitors():
    return jsonify([{"v_id": "V-99", "s_id": "STU-001", "v_name": "Muhammad Amjad", "relation": "Father", "cnic": "42101-1234567-1"}])

# COMPLAINTS API MATRIX
@app.route('/api/complaints', methods=['GET', 'POST'])
def handle_complaints_data():
    if request.method == 'GET':
        return jsonify(COMPLAINTS_GLOBAL_DB)
    elif request.method == 'POST':
        data = request.json
        new_complaint = {
            "id": len(COMPLAINTS_GLOBAL_DB) + 1,
            "user": data.get('user', 'Anonymous'),
            "title": data.get('title', 'General Issue'),
            "description": data.get('description', ''),
            "status": "Pending"
        }
        COMPLAINTS_GLOBAL_DB.append(new_complaint)
        return jsonify({"success": True})

@app.route('/api/complaints/resolve', methods=['POST'])
def resolve_complaint_ticket():
    data = request.json
    ticket_id = data.get('id')
    for item in COMPLAINTS_GLOBAL_DB:
        if item['id'] == int(ticket_id):
            item['status'] = 'Solved'
            return jsonify({"success": True})
    return jsonify({"success": False})

# LIVE MESS SCHEDULE ENDPOINT
@app.route('/api/mess-plan', methods=['GET', 'POST'])
def get_mess_plan():
    if request.method == 'GET':
        return jsonify(MESS_GLOBAL_PLAN)
    elif request.method == 'POST':
        data = request.json
        day = data.get('day')
        for entry in MESS_GLOBAL_PLAN:
            if entry['day'] == day:
                if data.get('breakfast'): entry['breakfast'] = data['breakfast']
                if data.get('lunch'): entry['lunch'] = data['lunch']
                if data.get('dinner'): entry['dinner'] = data['dinner']
                return jsonify({"success": True})
        return jsonify({"success": False})

# FEE VOUCHER SUBMISSION & AUDIT PROCESSING MATRIX
@app.route('/api/vouchers', methods=['GET', 'POST'])
def manage_fee_vouchers():
    if request.method == 'GET':
        return jsonify(VOUCHERS_GLOBAL_DB)
    elif request.method == 'POST':
        data = request.json
        new_voucher = {
            "id": len(VOUCHERS_GLOBAL_DB) + 1,
            "user": data.get('user'),
            "amount": data.get('amount'),
            "channel": data.get('channel'),
            "tx_id": data.get('tx_id'),
            "status": "Pending"
        }
        VOUCHERS_GLOBAL_DB.append(new_voucher)
        return jsonify({"success": True})

@app.route('/api/vouchers/approve', methods=['POST'])
def approve_fee_voucher():
    data = request.json
    v_id = data.get('id')
    student_user = data.get('user')
    
    # Update state voucher list
    for v in VOUCHERS_GLOBAL_DB:
        if v['id'] == int(v_id):
            v['status'] = 'Approved'
            
    # Modify local database row to Paid status dynamic injection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET status='Paid' WHERE student_id=%s OR gmail LIKE %s", (student_user, f"{student_user}%"))
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass
    return jsonify({"success": True})

# EXPORT SYSTEM LEDGER DIRECT TO REPORTLAB STREAM BINARY
@app.route('/api/export-pdf')
def export_pdf():
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'PdfTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#008080'), spaceAfter=15, alignment=1
        )
        story.append(Paragraph("HOSTEL MANAGEMENT SYSTEM MASTER DIRECTORY LOG", title_style))
        story.append(Spacer(1, 10))

        # Core header setup matrix mapping
        table_data = [['System ID', 'Student Full Name', 'Roll Identity', 'Allocated Room', 'Gmail Account', 'Ledger Status']]
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT student_id AS id, name, roll_number AS roll, room_number AS room, gmail, status FROM students")
            records = cursor.fetchall()
            for r in records:
                table_data.append([str(r['id']), str(r['name']), str(r['roll']), f"Room {r['room']}", str(r['gmail']), str(r['status'])])
            cursor.close()
            conn.close()
        except:
            table_data.append(['STU-001', 'Areen Zahra', '2026-IT-09', 'Room 204', 'admin@gmail.com', 'Paid'])

        pdf_table = Table(table_data, colWidths=[60, 110, 85, 65, 160, 60])
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#008080')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3d9d9')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        story.append(pdf_table)
        doc.build(story)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="Hostel_Master_Report.pdf", mimetype="application/pdf")
    except Exception as e:
        return f"Document Render Error Exception Handling: {str(e)}", 400

def start_flask():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000/')
    while True:
        time.sleep(1)