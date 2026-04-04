# new update
from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "cms_secret_key"

# ---------------- DATABASE CONNECTION ----------------
def connect_db():
    conn = sqlite3.connect("new_database.db", timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- CREATE TABLES ----------------
def create_tables():
    with sqlite3.connect("new_database.db", timeout=30) as con:
        cur = con.cursor()

        # USERS TABLE
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

        # DEFAULT ADMIN
        cur.execute("SELECT * FROM users WHERE username=?", ("admin",))
        if not cur.fetchone():
            cur.execute("INSERT INTO users (username,password) VALUES (?,?)",
                        ("admin", "admin123"))

        # ENQUIRY TABLE
        cur.execute("""
        CREATE TABLE IF NOT EXISTS enquiry(
            sl_no INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            mother TEXT,
            father TEXT,
            address TEXT,
            branch TEXT,
            year TEXT,
            academic_type TEXT,
            gender TEXT,
            fees_status TEXT,
            bus_service TEXT,
            bus_route TEXT,
            email TEXT,
            phone TEXT,
            dob TEXT
        )
        """)

        # ADMISSION TABLE
        cur.execute("""
        CREATE TABLE IF NOT EXISTS admission(
            sl_no INTEGER PRIMARY KEY AUTOINCREMENT,
            enquiry_sl_no INTEGER,
            student_name TEXT,
            mother_name TEXT,
            father_name TEXT,
            phone TEXT,
            branch TEXT,
            email TEXT,
            dob TEXT,
            address TEXT,
            emis_no TEXT,
            caste TEXT,
            community TEXT,
            religion TEXT,
            fees_status TEXT,
            gender TEXT,
            year TEXT,
            academic_type TEXT
        )
        """)

        # FEES TABLE
        cur.execute("""
        CREATE TABLE IF NOT EXISTS fees(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            branch TEXT,
            year TEXT,
            semester TEXT,
            status TEXT,
            amount INTEGER,
            sl_no INTEGER
        )
        """)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        con = connect_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",
                    (request.form.get("username",""), request.form.get("password","")))
        user = cur.fetchone()
        con.close()
        if user:
            session["user"] = request.form.get("username","")
            return redirect("/home")
        else:
            return "Invalid Username or Password"
    return render_template("login.html")
#-------------------------------- FORGOT----------------------
@app.route("/forgot", methods=["GET","POST"])
def forgot():

    if request.method == "POST":
        username = request.form["username"]
        new_password = request.form["password"]

        con = connect_db()
        cur = con.cursor()

        # ✅ Check user exists
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()

        if user:
            cur.execute("UPDATE users SET password=? WHERE username=?",
                        (new_password, username))
            con.commit()
            msg = "Password Updated Successfully ✅"
        else:
            msg = "Username not found ❌"

        con.close()
        return msg

    return render_template("forgot.html")

#---------------------------REGISTER---------------------
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = connect_db()
        cur = con.cursor()

        # ✅ Check if user already exists
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()

        if user:
            con.close()
            return "Username already exists ❌"

        # ✅ Insert new user
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password))
        con.commit()
        con.close()

        return "Registration Successful ✅ <br><a href='/'>Login Now</a>"

    return render_template("register.html")

# ---------------- HOME ----------------
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")
    return render_template("home.html")

#--------------------------- ENQUIRY ----------------------------------
@app.route("/enquiry", methods=["GET", "POST"])
def enquiry():
    if "user" not in session:
        return redirect("/")

    con = connect_db()
    cur = con.cursor()

    cur.execute("SELECT MAX(sl_no) FROM enquiry")
    last = cur.fetchone()[0]
    next_sl = 1 if last is None else last + 1

    # POST → INSERT + STORE MESSAGE
    if request.method == "POST":
        cur.execute("""
        INSERT INTO enquiry (
            name, mother, father, dob, email, phone,
            address, branch, year, academic_type,
            gender, fees_status, bus_service, bus_route
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("name",""),
            request.form.get("mother",""),
            request.form.get("father",""),
            request.form.get("dob",""),
            request.form.get("email",""),
            request.form.get("phone",""),
            request.form.get("address",""),
            request.form.get("branch",""),
            request.form.get("year",""),
            request.form.get("academic_type",""),
            request.form.get("gender",""),
            request.form.get("fees_status",""),
            request.form.get("bus_service","No"),
            request.form.get("bus_route","")
        ))

        con.commit()
        con.close()

        # ✅ store message
        session["msg"] = "Enquiry submitted successfully"
        return redirect("/enquiry")

    # ✅ GET → show message once
    msg = session.pop("msg", None)

    con.close()
    return render_template("enquiry.html", next_sl=next_sl, msg=msg)
# ---------------- ADMISSION ----------------
@app.route('/admission', methods=['GET', 'POST'])
def admission():
    if "user" not in session:
        return redirect("/")

    conn = connect_db()
    cursor = conn.cursor()
    student = None

    # 🔍 SEARCH ENQUIRY
    if request.method == "GET" and request.args.get("sl_no"):
        cursor.execute("SELECT * FROM enquiry WHERE sl_no=?", (request.args.get("sl_no"),))
        student = cursor.fetchone()

    # 📥 INSERT ADMISSION
    if request.method == "POST":
        emis = request.form.get("emis_no","")

        if len(emis) != 16:
            conn.close()
            return "EMIS number must be exactly 16 digits"

        cursor.execute("""
        INSERT INTO admission
        (enquiry_sl_no, student_name, mother_name, father_name,
         phone, branch, email, dob, address,
         emis_no, caste, community, religion, fees_status, gender,
         year, academic_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("enquiry_sl_no",""),
            request.form.get("student_name",""),
            request.form.get("mother_name",""),
            request.form.get("father_name",""),
            request.form.get("phone",""),
            request.form.get("branch",""),
            request.form.get("email",""),
            request.form.get("dob",""),
            request.form.get("address",""),
            emis,
            request.form.get("caste",""),
            request.form.get("community",""),
            request.form.get("religion",""),
            request.form.get("fees_status",""),
            request.form.get("gender",""),
            request.form.get("year",""),
            request.form.get("academic_type","")
        ))

        conn.commit()
        conn.close()

        # ✅ STORE MESSAGE (only after submit)
        session["msg"] = "Admission submitted successfully"

        # 🔁 REDIRECT (important)
        return redirect("/admission")

    # ✅ SHOW MESSAGE ONLY ONCE
    msg = session.pop("msg", None)

    conn.close()

    # ✅ PASS msg (NOT hardcoded)
    return render_template("admission.html", student=student, msg=msg)
#---------------------FEES----------------------------
@app.route("/fees", methods=["GET","POST"])
def fees():
    if "user" not in session:
        return redirect("/")

    con = connect_db()
    cur = con.cursor()
    student = None
    result = None

    if request.method == "POST":
        sl_no = request.form.get("sl_no")

        if sl_no and sl_no.isdigit():
            # Get student details
            cur.execute("SELECT name, branch, phone, fees_status, year FROM enquiry WHERE sl_no=?", (int(sl_no),))
            student = cur.fetchone()

            if student:
                # 🔴 CHECK if already exists
                cur.execute("SELECT * FROM fees WHERE sl_no=?", (int(sl_no),))
                existing = cur.fetchone()

                if not existing:
                    # INSERT only if not exists
                    cur.execute("""
                        INSERT INTO fees (student_name, branch, year, status, amount, sl_no)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        student["name"],
                        student["branch"],
                        student["year"],
                        student["fees_status"],
                        50000 if student["fees_status"] in ["Full Paid","Full Fees Paid"] else 0,
                        int(sl_no)
                    ))
                    con.commit()

                # Fetch for display
                cur.execute("SELECT * FROM fees WHERE sl_no=?", (int(sl_no),))
                result = cur.fetchall()

    con.close()
    return render_template("fees.html", student=student, result=result)       
# ---------------- TC ----------------
@app.route("/tc", methods=["GET","POST"])
def tc():
    if "user" not in session:
        return redirect("/")
    data = None
    if request.method == "POST":
        con = connect_db()
        cur = con.cursor()
        cur.execute("""
SELECT enquiry_sl_no, student_name, father_name, mother_name,
       emis_no, gender, branch, dob, community
FROM admission WHERE enquiry_sl_no=?
""", (request.form.get("sl_no",""),))
        data = cur.fetchone()
        con.close()
    return render_template("tc.html", data=data)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    create_tables()
    app.run(debug=True, use_reloader=False)