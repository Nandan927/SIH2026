import sqlite3
import os

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# DATABASE PATH
# =========================================================

# __file__ points to:
# C:/SIH2026/SIH2026/database/db.py
#
# First dirname:
# C:/SIH2026/SIH2026/database
#
# Second dirname:
# C:/SIH2026/SIH2026
#
# Therefore database will be stored at:
# C:/SIH2026/SIH2026/horizon.db

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

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

    # Allows this:
    # row["name"]
    #
    # Instead of:
    # row[2]

    connection.row_factory = sqlite3.Row

    # Enable foreign-key validation
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

    try:

        # -------------------------------------------------
        # ADMINS TABLE
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                full_name TEXT NOT NULL,

                email TEXT UNIQUE NOT NULL,

                phone TEXT,

                password TEXT NOT NULL

            )
        """)

        # -------------------------------------------------
        # TRAINEES TABLE
        # -------------------------------------------------

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

        print(
            "DATABASE INITIALIZED SUCCESSFULLY"
        )

        print(
            "Database path:",
            DATABASE_PATH
        )

    except Exception as error:

        print(
            "DATABASE INITIALIZATION ERROR:",
            repr(error)
        )

        connection.rollback()

    finally:

        connection.close()


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

        # Hash password before storing it
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

        print(
            "ADMIN CREATED:",
            email
        )

        return {

            "success": True,

            "message": "Account created successfully."

        }

    except sqlite3.IntegrityError as error:

        print(
            "ADMIN CREATION INTEGRITY ERROR:",
            repr(error)
        )

        return {

            "success": False,

            "message": "An account with this email already exists."

        }

    except Exception as error:

        print(
            "CREATE ADMIN ERROR:",
            repr(error)
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

    try:

        cursor.execute("""
            SELECT *
            FROM admins
            WHERE email = ?
        """, (

            email,

        ))

        admin = cursor.fetchone()

    except Exception as error:

        print(
            "CHECK ADMIN QUERY ERROR:",
            repr(error)
        )

        connection.close()

        return None

    connection.close()

    # No admin found
    if admin is None:

        print(
            "LOGIN FAILED: Admin email not found:",
            email
        )

        return None

    # Verify password
    try:

        password_correct = check_password_hash(

            admin["password"],

            password

        )

    except Exception as error:

        print(
            "PASSWORD CHECK ERROR:",
            repr(error)
        )

        return None

    if password_correct:

        print(
            "LOGIN SUCCESSFUL:",
            email,
            "| Admin ID:",
            admin["id"]
        )

        return admin

    print(
        "LOGIN FAILED: Incorrect password:",
        email
    )

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

        # -------------------------------------------------
        # Verify admin exists before inserting trainee
        # -------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM admins
            WHERE id = ?
        """, (

            admin_id,

        ))

        admin_exists = cursor.fetchone()

        if admin_exists is None:

            print(
                "INSERT FAILED: Admin does not exist.",
                "| Admin ID:",
                admin_id
            )

            return False

        # -------------------------------------------------
        # Insert trainee
        # -------------------------------------------------

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
            "TRAINEE INSERTED SUCCESSFULLY"
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
            "Admin ID:",
            admin_id
        )

        return True

    except sqlite3.IntegrityError as error:

        print(
            "TRAINEE INSERT INTEGRITY ERROR"
        )

        print(
            "Trainee ID:",
            trainee_id
        )

        print(
            "Error:",
            repr(error)
        )

        connection.rollback()

        return False

    except Exception as error:

        print(
            "TRAINEE INSERT GENERAL ERROR"
        )

        print(
            "Trainee ID:",
            trainee_id
        )

        print(
            "Error:",
            repr(error)
        )

        connection.rollback()

        return False

    finally:

        connection.close()


# =========================================================
# GET TRAINEES OF CURRENT ADMIN
# =========================================================

def get_trainees_by_admin(admin_id):

    connection = get_connection()

    cursor = connection.cursor()

    try:

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

        trainees = [

            dict(row)

            for row in rows

        ]

        print(
            "GET TRAINEES BY ADMIN"
        )

        print(
            "Admin ID:",
            admin_id
        )

        print(
            "Fetched count:",
            len(trainees)
        )

        print(
            "Fetched trainees:",
            trainees
        )

        return trainees

    except Exception as error:

        print(
            "GET TRAINEES BY ADMIN ERROR:",
            repr(error)
        )

        return []

    finally:

        connection.close()


# =========================================================
# GET ALL TRAINEES
# =========================================================

def get_all_trainees():

    connection = get_connection()

    cursor = connection.cursor()

    try:

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

        print(
            "TOTAL TRAINEES IN DATABASE:",
            len(trainees)
        )

        return trainees

    except Exception as error:

        print(
            "GET ALL TRAINEES ERROR:",
            repr(error)
        )

        return []

    finally:

        connection.close()


# =========================================================
# GET SINGLE TRAINEE BY TRAINEE ID
# =========================================================

def get_trainee_by_trainee_id(
    trainee_id
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

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

            WHERE trainee_id = ?

        """, (

            trainee_id,

        ))

        row = cursor.fetchone()

        if row is None:

            return None

        return dict(row)

    except Exception as error:

        print(
            "GET SINGLE TRAINEE ERROR:",
            repr(error)
        )

        return None

    finally:

        connection.close()


# =========================================================
# DELETE ALL TRAINEES OF ONE ADMIN
# Mainly useful for testing
# =========================================================

def delete_trainees_by_admin(
    admin_id
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute("""
            DELETE FROM trainees
            WHERE admin_id = ?
        """, (

            admin_id,

        ))

        connection.commit()

        deleted_count = cursor.rowcount

        print(
            "DELETED TRAINEES:",
            deleted_count
        )

        print(
            "Admin ID:",
            admin_id
        )

        return deleted_count

    except Exception as error:

        print(
            "DELETE TRAINEES ERROR:",
            repr(error)
        )

        connection.rollback()

        return 0

    finally:

        connection.close()


# =========================================================
# DEBUG DATABASE CONTENTS
# =========================================================

def debug_database():

    connection = get_connection()

    cursor = connection.cursor()

    try:

        print("\n")
        print("=" * 70)
        print("DATABASE DEBUG INFORMATION")
        print("=" * 70)

        # Show admins
        cursor.execute("""
            SELECT
                id,
                full_name,
                email
            FROM admins
        """)

        admins = cursor.fetchall()

        print(
            "ADMINS:"
        )

        for admin in admins:

            print(
                dict(admin)
            )

        # Show trainees
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
                admin_id
            FROM trainees
            ORDER BY id DESC
        """)

        trainees = cursor.fetchall()

        print(
            "\nTRAINEES:"
        )

        for trainee in trainees:

            print(
                dict(trainee)
            )

        print(
            "\nTotal admins:",
            len(admins)
        )

        print(
            "Total trainees:",
            len(trainees)
        )

        print(
            "=" * 70
        )
        print("\n")

    except Exception as error:

        print(
            "DEBUG DATABASE ERROR:",
            repr(error)
        )

    finally:

        connection.close()

# =========================================================
# GET BRANCH ANALYSIS TRAINEES OF CURRENT ADMIN
# =========================================================

def get_branch_analysis_trainees(admin_id):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT

                trainee_id,
                name,
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

        trainees = [

            dict(row)

            for row in rows

        ]

        print(
            "GET BRANCH ANALYSIS TRAINEES"
        )

        print(
            "Admin ID:",
            admin_id
        )

        print(
            "Fetched count:",
            len(trainees)
        )

        return trainees

    except Exception as error:

        print(
            "GET BRANCH ANALYSIS TRAINEES ERROR:",
            repr(error)
        )

        return []

    finally:

        connection.close()