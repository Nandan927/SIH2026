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

@app.route("/admin/upload")
def admin_upload():

    # Only logged-in admin can access this page
    if "admin_id" not in session:
        return redirect(url_for("admin_signin"))

    return render_template("admin/upload.html")


# ---------------- LOGOUT ---------------- #

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin_signin"))


if __name__ == "__main__":
    app.run(debug=True)