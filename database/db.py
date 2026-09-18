import sqlite3
import os

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# DATABASE PATH
# =========================================================

# Get the main project folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# One fixed database file for the complete application
DATABASE_PATH = os.path.join(
    BASE_DIR,
    "horizon.db"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    # Allows us to access columns using column names
    # Example: row["name"]
    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    connection = get_connection()
    cursor = connection.cursor()

    # -----------------------------------------------------
    # ADMINS TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            phone TEXT,

            password TEXT NOT NULL

        )
    """)

    # -----------------------------------------------------
    # TRAINEES TABLE
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trainees (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            trainee_id TEXT NOT NULL UNIQUE,

            name TEXT NOT NULL,

            email TEXT NOT NULL,

            branch TEXT,

            batch TEXT,

            training_status TEXT,

            outcome_status TEXT,

            skills TEXT,

            password TEXT NOT NULL,

            admin_id INTEGER,

            FOREIGN KEY (admin_id)
                REFERENCES admins(id)

        )
    """)

    connection.commit()
    connection.close()

    print("Database initialized at:", DATABASE_PATH)


# =========================================================
# CREATE ADMIN
# =========================================================

def create_admin(
    full_name,
    email,
    phone,
    password
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Convert plain admin password into hash
        hashed_password = generate_password_hash(
            password
        )

        cursor.execute("""
            INSERT INTO admins (
                full_name,
                email,
                phone,
                password
            )
            VALUES (?, ?, ?, ?)
        """, (
            full_name,
            email,
            phone,
            hashed_password
        ))

        connection.commit()

        return {
            "success": True,
            "message": "Account created successfully."
        }

    except sqlite3.IntegrityError:

        return {
            "success": False,
            "message": "An account with this email already exists."
        }

    except Exception as error:

        print("CREATE ADMIN ERROR:", error)

        return {
            "success": False,
            "message": "Unable to create admin account."
        }

    finally:

        connection.close()


# =========================================================
# CHECK ADMIN LOGIN
# =========================================================

def check_admin(
    email,
    password
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM admins
        WHERE email = ?
    """, (
        email,
    ))

    admin = cursor.fetchone()

    connection.close()

    # No admin found
    if admin is None:
        return None

    # Compare entered password with stored hash
    if check_password_hash(
        admin["password"],
        password
    ):

        return admin

    return None


# =========================================================
# INSERT TRAINEE
# =========================================================

def insert_trainee(
    trainee_id,
    name,
    email,
    branch,
    batch,
    training_status,
    outcome_status,
    skills,
    hashed_password,
    admin_id
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO trainees (

                trainee_id,
                name,
                email,
                branch,
                batch,
                training_status,
                outcome_status,
                skills,
                password,
                admin_id

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trainee_id,
            name,
            email,
            branch,
            batch,
            training_status,
            outcome_status,
            skills,
            hashed_password,
            admin_id
        ))

        connection.commit()

        print(
            f"Trainee inserted successfully: "
            f"{trainee_id} | Admin ID: {admin_id}"
        )

        return True

    except sqlite3.IntegrityError as error:

        print(
            f"TRAINEE INSERT ERROR for {trainee_id}:",
            error
        )

        return False

    except Exception as error:

        print(
            f"GENERAL INSERT ERROR for {trainee_id}:",
            error
        )

        return False

    finally:

        connection.close()


# =========================================================
# GET TRAINEES OF LOGGED-IN ADMIN
# =========================================================

def get_trainees_by_admin(admin_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM trainees
        WHERE admin_id = ?
        ORDER BY id DESC
    """, (
        admin_id,
    ))

    rows = cursor.fetchall()

    # Convert sqlite3.Row objects into normal dictionaries
    trainees = [
        dict(row)
        for row in rows
    ]

    connection.close()

    print(
        f"Fetched {len(trainees)} trainees "
        f"for Admin ID: {admin_id}"
    )

    return trainees


# =========================================================
# GET ALL TRAINEES
# =========================================================

def get_all_trainees():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM trainees
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    trainees = [
        dict(row)
        for row in rows
    ]

    connection.close()

    return trainees


# =========================================================
# DELETE ALL TRAINEES OF AN ADMIN
# Optional helper for testing
# =========================================================

def delete_trainees_by_admin(admin_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM trainees
        WHERE admin_id = ?
    """, (
        admin_id,
    ))

    connection.commit()

    deleted_count = cursor.rowcount

    connection.close()

    print(
        f"Deleted {deleted_count} trainees "
        f"for Admin ID: {admin_id}"
    )

    return deleted_count