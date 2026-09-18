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
    insert_trainee,
    get_trainees_by_admin
)


app = Flask(__name__)

app.secret_key = "horizon-secret-key"


# Initialize database when application starts
init_db()


# =========================================================
# COMMON PAGES
# =========================================================

@app.route("/")
def loading():
    return render_template("common/loading.html")


@app.route("/roles")
def role_selection():
    return render_template("common/role_selection.html")


# =========================================================
# ADMIN SIGN IN
# =========================================================

@app.route("/admin/signin", methods=["GET", "POST"])
def admin_signin():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Check admin credentials from database
        admin = check_admin(email, password)

        if admin:

            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["full_name"]
            session["admin_email"] = admin["email"]

            flash("Login successful.", "success")

            # After login, go to upload page
            return redirect(url_for("admin_upload"))

        else:

            flash("Invalid email or password.", "error")

    return render_template("admin/signin.html")


# =========================================================
# ADMIN SIGN UP
# =========================================================

@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        # Basic validation
        if not full_name or not email or not password:

            flash(
                "Full name, email and password are required.",
                "error"
            )

            return redirect(url_for("admin_signup"))

        result = create_admin(
            full_name,
            email,
            phone,
            password
        )

        if result["success"]:

            flash(
                "Account created successfully. Please sign in.",
                "success"
            )

            return redirect(url_for("admin_signin"))

        else:

            flash(
                result["message"],
                "error"
            )

    return render_template("admin/signup.html")


# =========================================================
# GENERATE TRAINEE PASSWORD
# =========================================================

def generate_trainee_password(length=12):

    characters = (
        string.ascii_letters
        + string.digits
        + "@#$%&*!?"
    )

    password = "".join(
        secrets.choice(characters)
        for _ in range(length)
    )

    return password


# =========================================================
# ADMIN UPLOAD PAGE
# =========================================================

@app.route("/admin/upload", methods=["GET", "POST"])
def admin_upload():

    # Only logged-in admin can access upload page
    if "admin_id" not in session:

        return redirect(url_for("admin_signin"))

    # Display upload page for GET request
    if request.method == "GET":

        return render_template("admin/upload.html")

    # -----------------------------------------------------
    # POST REQUEST: EXCEL UPLOAD
    # -----------------------------------------------------

    uploaded_file = request.files.get("excel_file")

    # Check whether a file was selected
    if uploaded_file is None or uploaded_file.filename == "":

        flash(
            "Please select an Excel file.",
            "error"
        )

        return redirect(url_for("admin_upload"))

    # Check file extension
    if not uploaded_file.filename.lower().endswith(
        (".xlsx", ".xls")
    ):

        flash(
            "Only Excel files are allowed.",
            "error"
        )

        return redirect(url_for("admin_upload"))

    try:

        # Read Excel file using pandas
        dataframe = pd.read_excel(uploaded_file)

        print("\n========== EXCEL UPLOAD DEBUG ==========")
        print("Excel columns:", list(dataframe.columns))
        print("Total Excel rows:", len(dataframe))

        # Required Excel columns
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

        # Find missing columns
        missing_columns = [
            column
            for column in required_columns
            if column not in dataframe.columns
        ]

        if missing_columns:

            flash(
                "Missing columns: "
                + ", ".join(missing_columns),
                "error"
            )

            print("Missing columns:", missing_columns)

            return redirect(url_for("admin_upload"))

        # Store generated credentials here
        credentials = []

        # Count successfully inserted records
        inserted_count = 0

        # Count skipped records
        skipped_count = 0

        # -------------------------------------------------
        # PROCESS EACH EXCEL ROW
        # -------------------------------------------------

        for index, row in dataframe.iterrows():

            try:

                # Read values from Excel
                trainee_id = str(
                    row["Trainee ID"]
                ).strip()

                name = str(
                    row["Name"]
                ).strip()

                email = str(
                    row["Email"]
                ).strip()

                branch = str(
                    row["Branch"]
                ).strip()

                batch = str(
                    row["Batch"]
                ).strip()

                training_status = str(
                    row["Training Status"]
                ).strip()

                outcome_status = str(
                    row["Outcome Status"]
                ).strip()

                skills = str(
                    row["Skills"]
                ).strip()

                # Pandas converts empty Excel cells into "nan"
                # Convert those values into empty strings
                values = [
                    trainee_id,
                    name,
                    email,
                    branch,
                    batch,
                    training_status,
                    outcome_status,
                    skills
                ]

                values = [
                    "" if value.lower() == "nan" else value
                    for value in values
                ]

                (
                    trainee_id,
                    name,
                    email,
                    branch,
                    batch,
                    training_status,
                    outcome_status,
                    skills
                ) = values

                # Basic required-field validation
                if not trainee_id or not name or not email:

                    print(
                        f"Skipping row {index + 2}: "
                        "missing trainee ID, name or email"
                    )

                    skipped_count += 1

                    continue

                # Generate plain password
                plain_password = generate_trainee_password()

                # Hash password before storing in database
                hashed_password = generate_password_hash(
                    plain_password
                )

                # Insert trainee into SQLite
                insert_trainee(
                    trainee_id=trainee_id,
                    name=name,
                    email=email,
                    branch=branch,
                    batch=batch,
                    training_status=training_status,
                    outcome_status=outcome_status,
                    skills=skills,
                    password_hash=hashed_password,
                    admin_id=session["admin_id"]
                )

                # Store plain password only in downloadable file
                credentials.append({
                    "Trainee ID": trainee_id,
                    "Name": name,
                    "Email": email,
                    "Password": plain_password
                })

                inserted_count += 1

            except Exception as row_error:

                print(
                    f"Error processing Excel row {index + 2}:",
                    row_error
                )

                skipped_count += 1

        print("Inserted records:", inserted_count)
        print("Skipped records:", skipped_count)
        print("========================================\n")

        # If no records were inserted
        if inserted_count == 0:

            flash(
                "No trainee records were inserted. "
                "Please check your Excel data and database.",
                "error"
            )

            return redirect(url_for("admin_upload"))

        # -------------------------------------------------
        # CREATE CREDENTIAL EXCEL FILE
        # -------------------------------------------------

        credential_df = pd.DataFrame(credentials)

        output = io.BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            credential_df.to_excel(
                writer,
                index=False,
                sheet_name="Credentials"
            )

        # Move file pointer to beginning
        output.seek(0)

        flash(
            f"{inserted_count} trainee records uploaded successfully.",
            "success"
        )

        # Send credential Excel file to browser
        return send_file(
            output,
            as_attachment=True,
            download_name="trainee_credentials.xlsx",
            mimetype=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

    except Exception as error:

        print("\n========== UPLOAD ERROR ==========")
        print(error)
        print("==================================\n")

        flash(
            "Something went wrong while processing the Excel file.",
            "error"
        )

        return redirect(url_for("admin_upload"))


# =========================================================
# LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin_signin"))


# =========================================================
# DASHBOARD DATA CALCULATOR
# =========================================================

def calculate_dashboard_data(trainees):

    """
    Convert trainee database records into dashboard statistics.
    """

    # If database returns None, use empty list
    trainees = trainees or []

    total_trainees = len(trainees)

    training_status_counts = {}
    outcome_status_counts = {}
    branch_counts = {}
    batch_counts = {}

    active_trainees = 0
    completed_trainees = 0

    # Process every trainee
    for trainee in trainees:

        trainee = trainee or {}

        training_status = str(
            trainee.get("training_status", "")
        ).strip()

        outcome_status = str(
            trainee.get("outcome_status", "")
        ).strip()

        branch = str(
            trainee.get("branch", "")
        ).strip()

        batch = str(
            trainee.get("batch", "")
        ).strip()

        # Replace empty values
        training_status = training_status or "Unknown"
        outcome_status = outcome_status or "Unknown"
        branch = branch or "Unknown"
        batch = batch or "Unknown"

        # Count training statuses
        training_status_counts[training_status] = (
            training_status_counts.get(training_status, 0) + 1
        )

        # Count outcome statuses
        outcome_status_counts[outcome_status] = (
            outcome_status_counts.get(outcome_status, 0) + 1
        )

        # Count branches
        branch_counts[branch] = (
            branch_counts.get(branch, 0) + 1
        )

        # Count batches
        batch_counts[batch] = (
            batch_counts.get(batch, 0) + 1
        )

        # Calculate completed trainees
        if (
            "completed" in training_status.lower()
            or "placed" in training_status.lower()
            or "employed" in outcome_status.lower()
        ):

            completed_trainees += 1

        else:

            active_trainees += 1

    dashboard_result = {
        "total_trainees": total_trainees,
        "active_trainees": active_trainees,
        "completed_trainees": completed_trainees,
        "training_status_counts": training_status_counts,
        "outcome_status_counts": outcome_status_counts,
        "branch_counts": branch_counts,
        "batch_counts": batch_counts
    }

    print("\n========== DASHBOARD DEBUG ==========")
    print("Trainees fetched from database:", trainees)
    print("Total trainees:", total_trainees)
    print("Dashboard data:", dashboard_result)
    print("=====================================\n")

    return dashboard_result


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    # Only logged-in admin can access dashboard
    if "admin_id" not in session:

        return redirect(url_for("admin_signin"))

    # Fetch trainees belonging to logged-in admin
    trainees = get_trainees_by_admin(
        session["admin_id"]
    )

    print("\n========== DATABASE FETCH DEBUG ==========")
    print("Logged-in admin ID:", session["admin_id"])
    print("Fetched trainees:", trainees)
    print("Number of fetched trainees:", len(trainees or []))
    print("==========================================\n")

    # Convert database records into dashboard metrics
    dashboard_data = calculate_dashboard_data(
        trainees
    )

    # Send data to Jinja template
    return render_template(
        "admin/dashboard.html",
        dashboard_data=dashboard_data
    )


# =========================================================
# APPLICATION START
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )