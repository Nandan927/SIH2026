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
# __file__ = database/db.py
# First dirname = database folder
# Second dirname = main project folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Store database in the main project folder
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

    # Allows accessing columns by their names
    # Example: row["name"]
    connection.row_factory = sqlite3.Row

    # Enable foreign-key checking in SQLite
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

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

            admin_id INTEGER NOT NULL,

            FOREIGN KEY (admin_id)
                REFERENCES admins(id)

        )
    """)

    connection.commit()

    connection.close()

    print(
        "Database initialized at:",
        DATABASE_PATH
    )


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

        # Hash admin password before storing
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

        print(
            "CREATE ADMIN ERROR:",
            error
        )

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

    # Admin does not exist
    if admin is None:

        return None

    # Check entered password against stored hash
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
            "Trainee inserted successfully:",
            trainee_id,
            "| Admin ID:",
            admin_id
        )

        return True

    except sqlite3.IntegrityError as error:

        print(
            "TRAINEE INSERT INTEGRITY ERROR:",
            trainee_id,
            "|",
            error
        )

        return False

    except Exception as error:

        print(
            "GENERAL TRAINEE INSERT ERROR:",
            trainee_id,
            "|",
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
        SELECT
            id,
            trainee_id,
            name,
            email,
            branch,
            batch,
            training_status,
            outcome_status,
            skills,
            admin_id
        FROM trainees
        WHERE admin_id = ?
        ORDER BY id DESC
    """, (
        admin_id,
    ))

    rows = cursor.fetchall()

    # Convert sqlite3.Row into normal dictionaries
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
        SELECT
            id,
            trainee_id,
            name,
            email,
            branch,
            batch,
            training_status,
            outcome_status,
            skills,
            admin_id
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
# GET SINGLE TRAINEE BY TRAINEE ID
# =========================================================

def get_trainee_by_trainee_id(trainee_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM trainees
        WHERE trainee_id = ?
    """, (
        trainee_id,
    ))

    row = cursor.fetchone()

    connection.close()

    if row is None:

        return None

    return dict(row)


# =========================================================
# DELETE ALL TRAINEES OF AN ADMIN
# Useful for testing
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