from flask import Flask, render_template, redirect, request, url_for, session
import PyPDF2
import docx
from db import SessionLocal, Base, engine
import json
import models
from ai import analyze_resume

app = Flask(__name__)
app.secret_key = "secret123"

Base.metadata.create_all(bind=engine)


# Homepage
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    db = SessionLocal()
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.query(models.User).filter_by(email=email, password=password).first()
        if user:
            session["user"] = user.email
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials. Please try again."
    return render_template("login.html")


# SignUp
@app.route("/signup", methods=["GET", "POST"])
def signup():
    db = SessionLocal()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = db.query(models.User).filter_by(email=email).first()
        if existing_user:
            return "User already exists. Please log in."
        user = models.User(email=email, password=password)
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
                    result = {"error": f"Failed to read PDF file. as {str(e)}"}
            elif file.filename.endswith(".docx"):
                try:
                    doc = docx.Document(file)
                    text = ""
                    for para in doc.paragraphs:
                        text += para.text + "\n"
                    resume_text = text
                except Exception as e:
                    result = {"error": f"Failed to read DOCX file. as {str(e)}"}
        if resume_text and user_goal:
            try:
                result = analyze_resume(resume_text, user_goal)

                # save report to db
                db = SessionLocal()
                user = db.query(models.User).filter_by(email=session["user"]).first()
                report = models.Report(
                    user_id=user.id, resume_text=resume_text, result=json.dumps(result)
                )

                db.add(report)
                db.commit()
            except Exception as e:
                result = {"error": f"AI Error: {str(e)}"}
    return render_template("dashboard.html", user=session["user"], result=result)


# History
@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login"))
    db = SessionLocal()
    user = db.query(models.User).filter_by(email=session["user"]).first()
    reports = (
        db.query(models.Report)
        .filter_by(user_id=user.id)
        .order_by(models.Report.id.desc())
        .all()
    )

    # Convert result from JSON string to dict
    parsed_reports = []
    for r in reports:
        try:
            parsed_result = json.loads(r.result)
        except:
            parsed_reports = []
        parsed_reports.append(
            {
                "resume": r.resume_text,
                "result": parsed_result,
            }
        )
    return render_template("history.html", reports=parsed_reports)


# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# forgot password
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


if __name__ == "__main__":
    app.run(debug=True)
