import secrets
import string
import io
import pandas as pd

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file
)

from werkzeug.security import generate_password_hash

from database.db import (
    init_db,
    create_admin,
    check_admin,
    insert_trainee
)
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import init_db, create_admin, check_admin

app = Flask(__name__)

app.secret_key = "horizon-secret-key"


init_db()


# ---------------- COMMON PAGES ---------------- #

@app.route("/")
def loading():
    return render_template("common/loading.html")


@app.route("/roles")
def role_selection():
    return render_template("common/role_selection.html")


# ---------------- ADMIN SIGN IN ---------------- #

@app.route("/admin/signin", methods=["GET", "POST"])
def admin_signin():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        admin = check_admin(email, password)

        if admin:
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["full_name"]
            session["admin_email"] = admin["email"]

            flash("Login successful.", "success")

            return redirect(url_for("admin_upload"))

        else:
            flash("Invalid email or password.", "error")

    return render_template("admin/signin.html")


# ---------------- ADMIN SIGN UP ---------------- #

@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():

    if request.method == "POST":

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

        result = create_admin(
            full_name,
            email,
            phone,
            password
        )

        if result["success"]:
            flash("Account created successfully. Please sign in.", "success")
            return redirect(url_for("admin_signin"))

        else:
            flash(result["message"], "error")

    return render_template("admin/signup.html")


# ---------------- ADMIN UPLOAD PAGE ---------------- #

@app.route("/admin/upload", methods=["GET", "POST"])
def admin_upload():

    # Only logged-in admin can access this page
    if "admin_id" not in session:
        return redirect(url_for("admin_signin"))

    # When admin submits an Excel file
    if request.method == "POST":

        uploaded_file = request.files.get("excel_file")

        # Check whether file was selected
        if uploaded_file is None or uploaded_file.filename == "":
            flash("Please select an Excel file.", "error")
            return redirect(url_for("admin_upload"))

        # Check file extension
        if not uploaded_file.filename.lower().endswith((".xlsx", ".xls")):
            flash("Only Excel files are allowed.", "error")
            return redirect(url_for("admin_upload"))

        try:

            # Read uploaded Excel file using pandas
            dataframe = pd.read_excel(uploaded_file)

            # Required columns
            required_columns = [
                "Trainee ID",
                "Name",
                "Email",
                "Branch",
                "Batch",
                "Training Status",
                "Outcome Status",
                "Skills"
            ]

            # Check missing columns
            missing_columns = [
                column
                for column in required_columns
                if column not in dataframe.columns
            ]

            if missing_columns:

                flash(
                    "Missing columns: " + ", ".join(missing_columns),
                    "error"
                )

                return redirect(url_for("admin_upload"))

            # Store generated credentials temporarily
            credentials = []

            # Process every Excel row
            for _, row in dataframe.iterrows():

                trainee_id = str(row["Trainee ID"]).strip()
                name = str(row["Name"]).strip()
                email = str(row["Email"]).strip()

                branch = str(row["Branch"]).strip()
                batch = str(row["Batch"]).strip()
                training_status = str(row["Training Status"]).strip()
                outcome_status = str(row["Outcome Status"]).strip()
                skills = str(row["Skills"]).strip()

                # Basic validation
                if not trainee_id or not name or not email:
                    continue

                # Generate plain password
                plain_password = generate_trainee_password()

                # Hash password before database storage
                hashed_password = generate_password_hash(plain_password)

                # Save trainee in database
                insert_trainee(
                    trainee_id,
                    name,
                    email,
                    branch,
                    batch,
                    training_status,
                    outcome_status,
                    skills,
                    hashed_password,
                    session["admin_id"]
                )

                # Store plain password only for credential Excel
                credentials.append({
                    "Trainee ID": trainee_id,
                    "Name": name,
                    "Email": email,
                    "Password": plain_password
                })

            # Convert credentials list to DataFrame
            credential_df = pd.DataFrame(credentials)

            # Create Excel file in memory
            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                credential_df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Credentials"
                )

            output.seek(0)

            # Send generated credential Excel to browser
            return send_file(
                output,
                as_attachment=True,
                download_name="trainee_credentials.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as error:

            print("UPLOAD ERROR:", error)

            flash(
                "Something went wrong while processing the Excel file.",
                "error"
            )

            return redirect(url_for("admin_upload"))

    return render_template("admin/upload.html")


# ---------------- LOGOUT ---------------- #

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin_signin"))



def generate_trainee_password(length=12):

    characters = string.ascii_letters + string.digits + "@#$%&*!?"

    password = "".join(
        secrets.choice(characters)
        for _ in range(length)
    )

    return password


if __name__ == "__main__":
    app.run(debug=True)