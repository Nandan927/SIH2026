import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


DATABASE_NAME = "horizon.db"


# Connect to SQLite database
def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)

    # Allows us to access columns by name
    connection.row_factory = sqlite3.Row

    return connection


# Create required tables
def init_db():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL
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