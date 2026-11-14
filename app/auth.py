import string
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, request
bp = Blueprint("auth", __name__)
from .db import get_db
from app.utils import code_generator

@bp.route("/register", methods=["GET", "POST"])
def register():
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
        doesusernamealreadyexist = db.execute(
			'''SELECT account_id 
			FROM account
			WHERE username = ?''',
			(username,)
			).fetchone()
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