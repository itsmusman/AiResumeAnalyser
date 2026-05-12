import json

import docx
import PyPDF2
from flask import Flask, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import models
from ai import analyze_resume
from db import Base, SessionLocal, engine

app = Flask(__name__)
app.secret_key = "secret123"

Base.metadata.create_all(bind=engine)


def get_db():
    if "db" not in g:
        g.db = SessionLocal()
    return g.db


@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# Homepage
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    db = get_db()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.query(models.User).filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user"] = user.email
            session["user_id"] = user.id
            session["full_name"] = user.full_name
            return redirect(url_for("dashboard"))
        else:
            return render_template(
                "login.html", error="Invalid credentials. Please try again."
            )
    return render_template("login.html")


# SignUp
@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = get_db()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        full_name = request.form.get("full_name")

        existing_user = db.query(models.User).filter_by(email=email).first()
        if existing_user:
            return render_template(
                "signup.html", error="User already exists. Please log in."
            )

        hashed_password = generate_password_hash(password)
        user = models.User(email=email, password=hashed_password, full_name=full_name)
        db.add(user)
        db.commit()

        return redirect(url_for("login"))
    return render_template("signup.html")


# DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    result = None
    db = get_db()
    user = db.query(models.User).filter_by(id=session.get("user_id")).first()

    if request.method == "POST":
        user_goal = request.form.get("role")
        resume_text = request.form.get("resume")
        file = request.files.get("file")

        # file handling
        if file and file.filename != "":
            if file.filename.endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() or ""
                    resume_text = text
                except Exception as e:
                    result = {"error": f"Failed to read PDF file: {str(e)}"}
            elif file.filename.endswith(".docx"):
                try:
                    doc = docx.Document(file)
                    text = ""
                    for para in doc.paragraphs:
                        text += para.text + "\n"
                    resume_text = text
                except Exception as e:
                    result = {"error": f"Failed to read DOCX file: {str(e)}"}

        if resume_text and user_goal:
            try:
                result = analyze_resume(resume_text, user_goal)

                # save report to db
                if "error" not in result:
                    report = models.Report(
                        user_id=user.id,
                        resume_text=resume_text,
                        result=json.dumps(result),
                    )
                    db.add(report)
                    db.commit()
            except Exception as e:
                result = {"error": f"AI Error: {str(e)}"}

    return render_template("dashboard.html", user=user, result=result)


# History
@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    user = db.query(models.User).filter_by(id=session.get("user_id")).first()

    reports = (
        db.query(models.Report)
        .filter_by(user_id=user.id)
        .order_by(models.Report.id.desc())
        .all()
    )

    parsed_reports = []
    for r in reports:
        try:
            parsed_result = json.loads(r.result)
            parsed_reports.append(
                {
                    "id": r.id,
                    "resume": r.resume_text[:200] + "..." if r.resume_text else "",
                    "result": parsed_result,
                }
            )
        except:
            pass

    return render_template("history.html", reports=parsed_reports, user=user)


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# forgot password
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


if __name__ == "__main__":
    app.run(debug=True)
