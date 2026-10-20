import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date

# ----------------- CONFIGURATION -----------------
LIBRARY_NAME = "Sainik Library"
TOTAL_SEATS = 65
OWNER_PIN = "1234"  # CHANGE THIS to your secret Owner PIN

st.set_page_config(page_title=LIBRARY_NAME, page_icon="📚", layout="wide")

# ----------------- DATABASE SETUP -----------------
def get_db():
    conn = sqlite3.connect("sainik_library.db", check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Student table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        mobile TEXT UNIQUE NOT NULL,
        home_mobile TEXT,
        address TEXT,
        nok_name TEXT,
        nok_relation TEXT,
        nok_mobile TEXT,
        seat_no INTEGER,
        shift TEXT,
        joining_date TEXT,
        fee_due_date TEXT,
        monthly_fee REAL,
        status TEXT DEFAULT 'Active'
    )''')
    # Attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        student_name TEXT,
        seat_no INTEGER,
        date TEXT,
        check_in_time TEXT,
        check_out_time TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )''')
    # Fees history table
    c.execute('''CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount REAL,
        payment_date TEXT,
        valid_until TEXT,
        payment_mode TEXT
    )''')
    conn.commit()

init_db()

# ----------------- SIDEBAR NAVIGATION -----------------
st.sidebar.title(f"🏛️ {LIBRARY_NAME}")
st.sidebar.caption("24x7 Self Study Library | Total Capacity: 65 Seats")
mode = st.sidebar.radio("Navigate", ["Student Kiosk (Attendance & Registration)", "Owner Dashboard (Locked)"])

# ==============================================================================
# SECTION 1: STUDENT KIOSK (Public / Front Desk)
# ==============================================================================
if mode == "Student Kiosk (Attendance & Registration)":
    st.title(f"📖 Welcome to {LIBRARY_NAME}")
    
    kiosk_tab1, kiosk_tab2 = st.tabs(["🕒 Mark Daily Attendance", "📝 New Student Registration & NOK"])
    
    # --- Tab 1: Attendance ---
    with kiosk_tab1:
        st.subheader("Daily Attendance Check-In / Check-Out")
        mobile_input = st.text_input("Enter Registered Mobile Number to Mark Attendance:", max_chars=10)
        
        col_act1, col_act2 = st.columns(2)
        today_str = date.today().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%I:%M %p")

        conn = get_db()
        c = conn.cursor()

        if col_act1.button("Check IN 🟢", use_container_width=True):
            if mobile_input:
                c.execute("SELECT id, name, seat_no FROM students WHERE mobile = ? AND status = 'Active'", (mobile_input.strip(),))
                student = c.fetchone()
                if student:
                    s_id, s_name, s_seat = student
                    # Check if already checked in today
                    c.execute("SELECT id FROM attendance WHERE student_id = ? AND date = ? AND check_out_time IS NULL", (s_id, today_str))
                    existing = c.fetchone()
                    if existing:
                        st.warning(f"⚠️ {s_name}, you have already checked in today!")
                    else:
                        c.execute("INSERT INTO attendance (student_id, student_name, seat_no, date, check_in_time) VALUES (?, ?, ?, ?, ?)",
                                  (s_id, s_name, s_seat, today_str, now_time))
                        conn.commit()
                        st.success(f"✅ Welcome {s_name}! Checked in at {now_time}. Assigned Seat: {s_seat}")
                else:
                    st.error("Mobile number not found or inactive. Please register first.")
            else:
                st.warning("Please enter your mobile number.")

        if col_act2.button("Check OUT 🔴", use_container_width=True):
            if mobile_input:
                c.execute("SELECT id, name FROM students WHERE mobile = ?", (mobile_input.strip(),))
                student = c.fetchone()
                if student:
                    s_id, s_name = student
                    c.execute("SELECT id FROM attendance WHERE student_id = ? AND date = ? AND check_out_time IS NULL ORDER BY id DESC LIMIT 1", (s_id, today_str))
                    open_session = c.fetchone()
                    if open_session:
                        c.execute("UPDATE attendance SET check_out_time = ? WHERE id = ?", (now_time, open_session[0]))
                        conn.commit()
                        st.info(f"👋 Goodbye {s_name}! Checked out at {now_time}.")
                    else:
                        st.warning("No active check-in found for today.")
                else:
                    st.error("Student not found.")
            else:
                st.warning("Please enter your mobile number.")

    # --- Tab 2: Self Registration & NOK ---
    with kiosk_tab2:
        st.subheader("Student Admission & Next-of-Kin (NOK) Form")
        st.caption("All information is stored securely and accessible only by the Library Owner.")
        
        with st.form("reg_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("Student Full Name *")
                mobile = st.text_input("Student Personal Mobile *", max_chars=10)
                home_mobile = st.text_input("Home / Landline / Alternate Mobile *", max_chars=10)
                shift = st.selectbox("Preferred Shift", ["Full Day (24x7)", "Morning Shift", "Evening Shift", "Night Shift"])
            with col_b:
                nok_name = st.text_input("Next of Kin (NOK / Parent / Guardian) Name *")
                nok_relation = st.selectbox("Relationship with NOK", ["Father", "Mother", "Guardian", "Spouse", "Sibling"])
                nok_mobile = st.text_input("NOK Emergency Contact Number *", max_chars=10)
                seat_pref = st.number_input(f"Preferred Seat (1 to {TOTAL_SEATS})", min_value=1, max_value=TOTAL_SEATS, value=1)
                
            address = st.text_area("Permanent / Local Residential Address *")
            
            submitted = st.form_submit_button("Submit Admission Form")
            if submitted:
                if not name or not mobile or not home_mobile or not nok_mobile or not address:
                    st.error("Please fill in all mandatory fields (*)")
                else:
                    try:
                        join_date = date.today().strftime("%Y-%m-%d")
                        c.execute('''INSERT INTO students 
                            (name, mobile, home_mobile, address, nok_name, nok_relation, nok_mobile, seat_no, shift, joining_date, status) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active')''',
                            (name, mobile, home_mobile, address, nok_name, nok_relation, nok_mobile, seat_pref, shift, join_date))
                        conn.commit()
                        st.success(f"🎉 Admission submitted successfully for {name}! Please contact the owner to confirm seat allocation & fee deposit.")
                    except sqlite3.IntegrityError:
                        st.error("A student with this mobile number is already registered.")

# ==============================================================================
# SECTION 2: OWNER DASHBOARD (Password Protected)
# ==============================================================================
else:
    st.sidebar.markdown("---")
    pin = st.sidebar.text_input("Enter Owner PIN", type="password")
    
    if pin != OWNER_PIN:
        st.warning("🔒 Access Restricted: Please enter the valid Owner PIN in the left sidebar to view confidential records.")
    else:
        st.title("🛡️ Sainik Library - Owner Management Panel")
        conn = get_db()
        today_str = date.today().strftime("%Y-%m-%d")

        # Top Level Metrics
        total_registered = pd.read_sql("SELECT COUNT(*) as count FROM students WHERE status='Active'", conn)['count'][0]
        today_attendance = pd.read_sql("SELECT COUNT(DISTINCT student_id) as count FROM attendance WHERE date=?", conn, params=[today_str])['count'][0]
        currently_in = pd.read_sql("SELECT COUNT(*) as count FROM attendance WHERE date=? AND check_out_time IS NULL", conn, params=[today_str])['count'][0]
        vacant_seats = max(0, TOTAL_SEATS - currently_in)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Seats", TOTAL_SEATS)
        m2.metric("Seats Currently Occupied", f"{currently_in} / {TOTAL_SEATS}")
        m3.metric("Seats Available Right Now", vacant_seats)
        m4.metric("Total Footfall Today", today_attendance)

        st.markdown("---")
        
        tab_report, tab_students, tab_fees = st.tabs(["📊 Today's Attendance Log", "👥 Confidential Student & NOK Directory", "💳 Fee Records"])

        # Tab 1: Daily Attendance
        with tab_report:
            st.subheader(f"Attendance Log for Today ({today_str})")
            df_att = pd.read_sql('''
                SELECT attendance.id, attendance.student_name as 'Name', students.mobile as 'Mobile', 
                       attendance.seat_no as 'Seat No', attendance.check_in_time as 'Check In', 
                       attendance.check_out_time as 'Check Out'
                FROM attendance
                JOIN students ON attendance.student_id = students.id
                WHERE attendance.date = ?
                ORDER BY attendance.id DESC
            ''', conn, params=[today_str])
            
            if not df_att.empty:
                st.dataframe(df_att, use_container_width=True)
            else:
                st.info("No students have checked in today yet.")

        # Tab 2: Student Directory (Address & NOK info accessible only here)
        with tab_students:
            st.subheader("Confidential Student Records")
            df_stud = pd.read_sql('''
                SELECT id, name as 'Student Name', mobile as 'Mobile', home_mobile as 'Home Phone', 
                       address as 'Address', nok_name as 'NOK Name', nok_relation as 'NOK Relation', 
                       nok_mobile as 'NOK Emergency Phone', seat_no as 'Seat #', shift as 'Shift', 
                       joining_date as 'Join Date', status as 'Status'
                FROM students
            ''', conn)
            
            st.dataframe(df_stud, use_container_width=True)
            
            # Export option
            csv = df_stud.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Master Student List (CSV)", data=csv, file_name=f"sainik_library_students_{today_str}.csv", mime="text/csv")

        # Tab 3: Fee Management
        with tab_fees:
            st.subheader("Fee Records & Collections")
            
            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                st.markdown("### Record a Payment")
                student_list = pd.read_sql("SELECT id, name, mobile FROM students WHERE status='Active'", conn)
                if not student_list.empty:
                    student_map = {f"{row['name']} ({row['mobile']})": row['id'] for _, row in student_list.iterrows()}
                    selected_student = st.selectbox("Select Student", list(student_map.keys()))
                    fee_amount = st.number_input("Fee Paid (₹)", min_value=0.0, step=100.0, value=1000.0)
                    payment_date = st.date_input("Payment Date", value=date.today())
                    valid_upto = st.date_input("Valid Upto (Next Due Date)")
                    pay_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Bank Transfer"])
                    
                    if st.button("Save Fee Payment", use_container_width=True):
                        c = conn.cursor()
                        sid = student_map[selected_student]
                        c.execute("INSERT INTO fees (student_id, amount, payment_date, valid_until, payment_mode) VALUES (?, ?, ?, ?, ?)",
                                  (sid, fee_amount, payment_date.strftime("%Y-%m-%d"), valid_upto.strftime("%Y-%m-%d"), pay_mode))
                        c.execute("UPDATE students SET fee_due_date = ?, monthly_fee = ? WHERE id = ?", 
                                  (valid_upto.strftime("%Y-%m-%d"), fee_amount, sid))
                        conn.commit()
                        st.success("Fee record saved successfully!")
                else:
                    st.info("No active students found.")
            
            with col_f2:
                st.markdown("### Recent Payment Transactions")
                df_fees = pd.read_sql('''
                    SELECT fees.id, students.name as 'Student Name', students.seat_no as 'Seat #', 
                           fees.amount as 'Amount (₹)', fees.payment_date as 'Date Paid', 
                           fees.valid_until as 'Valid Until', fees.payment_mode as 'Mode'
                    FROM fees
                    JOIN students ON fees.student_id = students.id
                    ORDER BY fees.id DESC LIMIT 20
                ''', conn)
                st.dataframe(df_fees, use_container_width=True)
