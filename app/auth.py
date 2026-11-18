import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, request, session
bp = Blueprint("auth", __name__)
from .db import get_db
from app.utils import code_generator, link_student_to_instructor

@bp.route("/register", methods=["GET", "POST"])
def register():
    #password validation (includes a number, lowercase and uppercase letter)
    if request.method == "POST":
        oneupper = False
        onelower = False
        onenumber = False
        username = request.form["username"]
        password = request.form["password"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        account_type = request.form["account_type"]
        transmission_type = request.form.get("transmission_type")
        address = request.form.get("address")
        adi_number = request.form.get("adi_number")
        confirmed_password = request.form["confirm_password"]
        if password != confirmed_password:
            return render_template("register.html", error="Passwords do not match")
        lengthpass = len(password)
        if lengthpass < 8:
            return render_template("register.html", error="Password should be at least 8 characters")
        for i in range (lengthpass):
            if password[i] in string.ascii_uppercase:
                oneupper = True
            elif password[i] in string.ascii_lowercase:
                onelower = True
            elif password[i] in string.digits:
                onenumber = True
        if not (oneupper and onelower and onenumber):
            return render_template("register.html", error="Passwords should contain one lowercase, one uppercase and one number")
        hashedpassword = generate_password_hash(password)
        db = get_db()
        columns = db.execute("PRAGMA table_info(account)").fetchall()
        print("ACTUAL ACCOUNT COLUMNS:", [column["name"] for column in columns], flush=True)
        #check username is unique
        doesusernamealreadyexist = db.execute(
			'''SELECT account_id 
			FROM account
			WHERE username = ?''',
			(username,)
			).fetchone()
        print("DUPLICATE CHECK:", doesusernamealreadyexist, flush=True)
        if doesusernamealreadyexist is not None:
            return render_template("register.html", error="Username already exists")
        createaccount = db.execute(
        '''INSERT INTO account
        (first_name, last_name, account_type, username, password_hash)
        VALUES (?, ?, ?, ?, ?)''',
        (first_name, last_name, account_type, username, hashedpassword)
        )
        account_id = createaccount.lastrowid
        if account_type == "STUDENT":
            student_initialising = db.execute(
            '''INSERT INTO student
            (account_id, transmission_type, address, instructor_id)
            VALUES (?, ?, ?, ?)''',
            (account_id, transmission_type, address, None,)
            )
        elif account_type == "INSTRUCTOR":
            instructor_initialising = db.execute(
            '''INSERT INTO instructor
            (account_id, adi_number, linking_code)
            VALUES (?, ?, ?)''',
            (account_id, adi_number, None,)
            )
            instructor_id = instructor_initialising.lastrowid
            linking_code = code_generator(instructor_id)
        db.commit()
        return render_template(
        "register.html",
        success="Registration successful!",
        linking_code=linking_code if account_type == "INSTRUCTOR" else None
        )
    return render_template("register.html")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        
        #find the account using the submitted username
        account = db.execute( 
        '''SELECT account_id, password_hash, account_type
        FROM account
        WHERE username = ?''', (username,)
        ).fetchone()

        #Check whether the account exists and the password is correct
        if account is not None and check_password_hash(account["password_hash"],password):
            session["account_id"] = account["account_id"]
            session["account_type"] = account["account_type"]
            return render_template("login.html", success="Login successful!",)
        else:
            return render_template("login.html", error = "Invalid username or password")
    return render_template("login.html")

@bp.route("/link_instructor", methods=["GET", "POST"])
def link_instructor():
    #making sure account trying to link is a student account
    if "account_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("account_type") != "STUDENT":
        return render_template("link_instructor.html", error="Only students can link to an instructor.")
    db = get_db()
    student = db.execute( 
    '''SELECT student_id, instructor_id
    FROM student
    WHERE account_id = ?''', (session["account_id"],)
    ).fetchone()

    if student is None:
        return render_template("link_instructor.html", error="Student account could not be found")
    if request.method == "POST":
        linking_code = request.form.get("linking_code","").strip()
        if not linking_code:
            return render_template("link_instructor.html", error="Please enter an instructor linking code.")
        try:
            result = link_student_to_instructor(student["student_id"], linking_code)
            if result:
                return render_template("link_instructor.html", success="You have successfully linked to your instructor!")
            else:
                return render_template("link_instructor.html", error="Student account could not be linked.")
        except ValueError:
            return render_template("link_instructor.html", error="Invalid instructor linking code.")
    return render_template("link_instructor.html")

@bp.route("/instructor_timetabling", methods=["GET", "POST"])
def instructor_timetabling():
    db = get_db()
    instructor  = db.execute(
    '''SELECT instructor_id
    FROM instructor
    WHERE account_id = ?''',
    (session["account_id"],)
    ).fetchone()
    if instructor is None:
        return render_template("instructor_timetable.html", error="Instructor account could not be found.")
    instructor_id = instructor["instructor_id"]
    if "account_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("account_type") != "INSTRUCTOR":
        return render_template("instructor_timetable.html", error="Only instructors can manage timetables.")
    db.execute(
        '''INSERT INTO, timetable (instructor_id, timetable_status)
        VALUES (?, ?)''', (instructor_id, "DRAFT")
    )
    db.commit()
    return "Timetable created successfully!"