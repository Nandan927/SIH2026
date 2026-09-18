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
    get_trainees_by_admin,
    get_all_trainees
)


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = "horizon-secret-key"


# =========================================================
# INITIALIZE DATABASE
# =========================================================

init_db()


# =========================================================
# COMMON PAGES
# =========================================================

@app.route("/")
def loading():

    return render_template(
        "common/loading.html"
    )


@app.route("/roles")
def role_selection():

    return render_template(
        "common/role_selection.html"
    )


# =========================================================
# ADMIN SIGN IN
# =========================================================

@app.route("/admin/signin", methods=["GET", "POST"])
def admin_signin():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            flash(
                "Email and password are required.",
                "error"
            )

            return redirect(
                url_for("admin_signin")
            )

        # Check credentials from database
        admin = check_admin(
            email,
            password
        )

        if admin:

            session["admin_id"] = admin["id"]

            session["admin_name"] = admin["full_name"]

            session["admin_email"] = admin["email"]

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("admin_upload")
            )

        else:

            flash(
                "Invalid email or password.",
                "error"
            )

            return redirect(
                url_for("admin_signin")
            )

    return render_template(
        "admin/signin.html"
    )


# =========================================================
# ADMIN SIGN UP
# =========================================================

@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not full_name or not email or not password:

            flash(
                "Full name, email and password are required.",
                "error"
            )

            return redirect(
                url_for("admin_signup")
            )

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

            return redirect(
                url_for("admin_signin")
            )

        else:

            flash(
                result["message"],
                "error"
            )

            return redirect(
                url_for("admin_signup")
            )

    return render_template(
        "admin/signup.html"
    )


# =========================================================
# GENERATE TRAINEE PASSWORD
# =========================================================

def generate_trainee_password(length=12):

    characters = (
        string.ascii_letters
        + string.digits
        + "@#$%&*!?"
    )

    return "".join(
        secrets.choice(characters)
        for _ in range(length)
    )


# =========================================================
# CONVERT EXCEL VALUE SAFELY TO STRING
# =========================================================

def clean_excel_value(value):

    """
    Converts Excel/Pandas values safely into strings.

    NaN, None and empty values become empty strings.
    """

    if pd.isna(value):

        return ""

    return str(value).strip()


# =========================================================
# ADMIN UPLOAD PAGE
# =========================================================

@app.route("/admin/upload", methods=["GET", "POST"])
def admin_upload():

    # Only logged-in admins can upload data
    if "admin_id" not in session:

        return redirect(
            url_for("admin_signin")
        )

    # -----------------------------------------------------
    # GET REQUEST
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(
            "admin/upload.html"
        )

    # -----------------------------------------------------
    # GET UPLOADED FILE
    # -----------------------------------------------------

    uploaded_file = request.files.get(
        "excel_file"
    )

    if (
        uploaded_file is None
        or uploaded_file.filename == ""
    ):

        flash(
            "Please select an Excel file.",
            "error"
        )

        return redirect(
            url_for("admin_upload")
        )

    # -----------------------------------------------------
    # CHECK FILE EXTENSION
    # -----------------------------------------------------

    if not uploaded_file.filename.lower().endswith(
        (".xlsx", ".xls")
    ):

        flash(
            "Only Excel files are allowed.",
            "error"
        )

        return redirect(
            url_for("admin_upload")
        )

    try:

        # -------------------------------------------------
        # READ EXCEL FILE
        # -------------------------------------------------

        dataframe = pd.read_excel(
            uploaded_file
        )

        print("\n")
        print("=" * 70)
        print("EXCEL UPLOAD DEBUG")
        print("=" * 70)

        print(
            "Logged-in admin ID:",
            session["admin_id"]
        )

        print(
            "Excel columns:",
            list(dataframe.columns)
        )

        print(
            "Total Excel rows:",
            len(dataframe)
        )

        print(
            "Excel preview:"
        )

        print(
            dataframe.head()
        )

        # -------------------------------------------------
        # REQUIRED COLUMNS
        # -------------------------------------------------

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

        missing_columns = [

            column

            for column in required_columns

            if column not in dataframe.columns

        ]

        if missing_columns:

            print(
                "Missing columns:",
                missing_columns
            )

            flash(
                "Missing columns: "
                + ", ".join(missing_columns),
                "error"
            )

            return redirect(
                url_for("admin_upload")
            )

        # -------------------------------------------------
        # STORAGE FOR GENERATED CREDENTIALS
        # -------------------------------------------------

        credentials = []

        inserted_count = 0

        skipped_count = 0

        # -------------------------------------------------
        # PROCESS EACH EXCEL ROW
        # -------------------------------------------------

        for index, row in dataframe.iterrows():

            excel_row_number = index + 2

            try:

                # -----------------------------------------
                # READ AND CLEAN VALUES
                # -----------------------------------------

                trainee_id = clean_excel_value(
                    row["Trainee ID"]
                )

                name = clean_excel_value(
                    row["Name"]
                )

                email = clean_excel_value(
                    row["Email"]
                )

                branch = clean_excel_value(
                    row["Branch"]
                )

                batch = clean_excel_value(
                    row["Batch"]
                )

                training_status = clean_excel_value(
                    row["Training Status"]
                )

                outcome_status = clean_excel_value(
                    row["Outcome Status"]
                )

                skills = clean_excel_value(
                    row["Skills"]
                )

                print(
                    f"\nProcessing Excel row {excel_row_number}"
                )

                print(
                    "Trainee ID:",
                    trainee_id
                )

                print(
                    "Name:",
                    name
                )

                print(
                    "Email:",
                    email
                )

                # -----------------------------------------
                # VALIDATE IMPORTANT FIELDS
                # -----------------------------------------

                if not trainee_id:

                    print(
                        f"Skipping row {excel_row_number}: "
                        "Trainee ID is empty"
                    )

                    skipped_count += 1

                    continue

                if not name:

                    print(
                        f"Skipping row {excel_row_number}: "
                        "Name is empty"
                    )

                    skipped_count += 1

                    continue

                if not email:

                    print(
                        f"Skipping row {excel_row_number}: "
                        "Email is empty"
                    )

                    skipped_count += 1

                    continue

                # -----------------------------------------
                # GENERATE PLAIN PASSWORD
                # -----------------------------------------

                plain_password = generate_trainee_password()

                # -----------------------------------------
                # HASH PASSWORD BEFORE DATABASE STORAGE
                # -----------------------------------------

                hashed_password = generate_password_hash(
                    plain_password
                )

                # -----------------------------------------
                # INSERT TRAINEE INTO DATABASE
                # -----------------------------------------

                print(
                    "Attempting database insertion for:",
                    trainee_id
                )

                insert_result = insert_trainee(

                    trainee_id=trainee_id,

                    name=name,

                    email=email,

                    branch=branch,

                    batch=batch,

                    training_status=training_status,

                    outcome_status=outcome_status,

                    skills=skills,

                    hashed_password=hashed_password,

                    admin_id=session["admin_id"]

                )

                print(
                    "Database insertion result:",
                    insert_result
                )

                # -------------------------------------------------
                # IMPORTANT:
                # Some insert_trainee functions return True.
                # Some correctly insert but return None.
                #
                # We treat None as success only if no exception
                # occurred, because the insertion function may
                # not explicitly return True.
                # -------------------------------------------------

                if insert_result is False:

                    print(
                        f"Database rejected trainee: {trainee_id}"
                    )

                    skipped_count += 1

                    continue

                # -----------------------------------------
                # SAVE CREDENTIALS FOR EXCEL
                # -----------------------------------------

                credentials.append({

                    "Trainee ID": trainee_id,

                    "Name": name,

                    "Email": email,

                    "Password": plain_password

                })

                inserted_count += 1

                print(
                    f"Successfully inserted trainee: {trainee_id}"
                )

            except Exception as row_error:

                print(
                    f"ERROR PROCESSING EXCEL ROW "
                    f"{excel_row_number}:",
                    repr(row_error)
                )

                skipped_count += 1

        # -----------------------------------------------------
        # VERIFY DATABASE AFTER INSERTION
        # -----------------------------------------------------

        all_database_trainees = get_all_trainees()

        admin_database_trainees = get_trainees_by_admin(
            session["admin_id"]
        )

        print("\n")
        print("=" * 70)
        print("UPLOAD FINAL DEBUG")
        print("=" * 70)

        print(
            "Inserted count:",
            inserted_count
        )

        print(
            "Skipped count:",
            skipped_count
        )

        print(
            "Total trainees in entire database:",
            len(all_database_trainees)
        )

        print(
            "Total trainees belonging to current admin:",
            len(admin_database_trainees)
        )

        print(
            "Current admin ID:",
            session["admin_id"]
        )

        print(
            "Current admin trainees:",
            admin_database_trainees
        )

        print(
            "=" * 70
        )
        print("\n")

        # -----------------------------------------------------
        # NO RECORD INSERTED
        # -----------------------------------------------------

        if inserted_count == 0:

            flash(
                "No trainee records were inserted. "
                "Check the Flask terminal for details.",
                "error"
            )

            return redirect(
                url_for("admin_upload")
            )

        # -----------------------------------------------------
        # CREATE CREDENTIAL EXCEL
        # -----------------------------------------------------

        credential_dataframe = pd.DataFrame(
            credentials
        )

        output = io.BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            credential_dataframe.to_excel(

                writer,

                index=False,

                sheet_name="Credentials"

            )

        output.seek(0)

        flash(
            f"{inserted_count} trainee records uploaded successfully.",
            "success"
        )

        # -----------------------------------------------------
        # SEND GENERATED CREDENTIAL FILE
        # -----------------------------------------------------

        return send_file(
        output,
        as_attachment=True,
        download_name="trainee_credentials.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    except Exception as error:

        print("\n")
        print("=" * 70)
        print("COMPLETE UPLOAD ERROR")
        print("=" * 70)

        print(
            "Error type:",
            type(error).__name__
        )

        print(
            "Error message:",
            repr(error)
        )

        print(
            "=" * 70
        )
        print("\n")

        flash(
            "Something went wrong while processing the Excel file. "
            "Check the terminal.",
            "error"
        )

        return redirect(
            url_for("admin_upload")
        )


# =========================================================
# DASHBOARD DATA CALCULATOR
# =========================================================

def calculate_dashboard_data(trainees):

    """
    Calculates statistics from trainees belonging
    to the currently logged-in admin.
    """

    if trainees is None:

        trainees = []

    total_trainees = len(
        trainees
    )

    training_status_counts = {}

    outcome_status_counts = {}

    branch_counts = {}

    batch_counts = {}

    active_trainees = 0

    completed_trainees = 0

    # -----------------------------------------------------
    # PROCESS EVERY TRAINEE
    # -----------------------------------------------------

    for trainee in trainees:

        if trainee is None:

            continue

        training_status = str(
            trainee.get(
                "training_status",
                ""
            )
        ).strip()

        outcome_status = str(
            trainee.get(
                "outcome_status",
                ""
            )
        ).strip()

        branch = str(
            trainee.get(
                "branch",
                ""
            )
        ).strip()

        batch = str(
            trainee.get(
                "batch",
                ""
            )
        ).strip()

        # Replace empty values
        if not training_status:

            training_status = "Unknown"

        if not outcome_status:

            outcome_status = "Unknown"

        if not branch:

            branch = "Unknown"

        if not batch:

            batch = "Unknown"

        # -------------------------------------------------
        # TRAINING STATUS COUNT
        # -------------------------------------------------

        training_status_counts[training_status] = (

            training_status_counts.get(
                training_status,
                0
            ) + 1

        )

        # -------------------------------------------------
        # OUTCOME STATUS COUNT
        # -------------------------------------------------

        outcome_status_counts[outcome_status] = (

            outcome_status_counts.get(
                outcome_status,
                0
            ) + 1

        )

        # -------------------------------------------------
        # BRANCH COUNT
        # -------------------------------------------------

        branch_counts[branch] = (

            branch_counts.get(
                branch,
                0
            ) + 1

        )

        # -------------------------------------------------
        # BATCH COUNT
        # -------------------------------------------------

        batch_counts[batch] = (

            batch_counts.get(
                batch,
                0
            ) + 1

        )

        # -------------------------------------------------
        # COMPLETED / ACTIVE CALCULATION
        # -------------------------------------------------

        training_lower = training_status.lower()

        outcome_lower = outcome_status.lower()

        is_completed = (

            outcome_lower == "employed"

            or outcome_lower == "placed"

            or outcome_lower == "working"

            or "currently employed" in outcome_lower

            or "placed" in outcome_lower

            or "employed" in outcome_lower

            or "completed" in training_lower

        )

        if is_completed:

            completed_trainees += 1

        else:

            active_trainees += 1

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    dashboard_result = {

        "total_trainees": total_trainees,

        "active_trainees": active_trainees,

        "completed_trainees": completed_trainees,

        "training_status_counts": training_status_counts,

        "outcome_status_counts": outcome_status_counts,

        "branch_counts": branch_counts,

        "batch_counts": batch_counts

    }

    # -----------------------------------------------------
    # DEBUG
    # -----------------------------------------------------

    print("\n")
    print("=" * 70)
    print("DASHBOARD DATA DEBUG")
    print("=" * 70)

    print(
        "Fetched trainees:",
        trainees
    )

    print(
        "Total trainees:",
        total_trainees
    )

    print(
        "Active trainees:",
        active_trainees
    )

    print(
        "Completed trainees:",
        completed_trainees
    )

    print(
        "Training status counts:",
        training_status_counts
    )

    print(
        "Outcome status counts:",
        outcome_status_counts
    )

    print(
        "Branch counts:",
        branch_counts
    )

    print(
        "Batch counts:",
        batch_counts
    )

    print(
        "Final dashboard result:",
        dashboard_result
    )

    print(
        "=" * 70
    )
    print("\n")

    return dashboard_result


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    # -----------------------------------------------------
    # AUTHENTICATION CHECK
    # -----------------------------------------------------

    if "admin_id" not in session:

        return redirect(
            url_for("admin_signin")
        )

    current_admin_id = session["admin_id"]

    # -----------------------------------------------------
    # FETCH ONLY CURRENT ADMIN'S TRAINEES
    # -----------------------------------------------------

    trainees = get_trainees_by_admin(
        current_admin_id
    )

    if trainees is None:

        trainees = []

    print("\n")
    print("=" * 70)
    print("ADMIN DASHBOARD ROUTE DEBUG")
    print("=" * 70)

    print(
        "Logged-in admin ID:",
        current_admin_id
    )

    print(
        "Fetched trainees:",
        trainees
    )

    print(
        "Number of trainees:",
        len(trainees)
    )

    print(
        "=" * 70
    )
    print("\n")

    # -----------------------------------------------------
    # CALCULATE DASHBOARD STATISTICS
    # -----------------------------------------------------

    dashboard_data = calculate_dashboard_data(
        trainees
    )

    # -----------------------------------------------------
    # SEND BOTH DATA OBJECTS TO HTML
    # -----------------------------------------------------

    return render_template(

        "admin/dashboard.html",

        dashboard_data=dashboard_data,

        trainees=trainees

    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_signin")
    )


# =========================================================
# APPLICATION START
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )