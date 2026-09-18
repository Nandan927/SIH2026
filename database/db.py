import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash


# Get the main project folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use ONE fixed database file for the entire application
DATABASE_PATH = os.path.join(BASE_DIR, "horizon.db")


# Connect to SQLite database
# Connect to SQLite database
def get_connection():

    connection = sqlite3.connect(DATABASE_PATH)

    # Allows us to access columns by name
    connection.row_factory = sqlite3.Row

    return connection


# Create required tables
def init_db():

    connection = get_connection()

    cursor = connection.cursor()

    # Create admins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL
        )
    """)

    # Create trainees table
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

            FOREIGN KEY (admin_id) REFERENCES admins(id)
        )
    """)

    connection.commit()
    connection.close()


# Create a new admin account
def create_admin(full_name, email, phone, password):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Hash password before storing it
        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO admins
            (full_name, email, phone, password)
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

    finally:
        connection.close()


# Check admin login credentials
def check_admin(email, password):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM admins
        WHERE email = ?
    """, (email,))

    admin = cursor.fetchone()

    connection.close()

    # No account found
    if admin is None:
        return None

    # Check entered password against hashed password
    if check_password_hash(admin["password"], password):
        return admin

    return None

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
    connection.close()


def get_trainees_by_admin(admin_id):

    # Use the same connection function used everywhere else
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM trainees
        WHERE admin_id = ?
        """,
        (admin_id,)
    )

    trainees = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return trainees