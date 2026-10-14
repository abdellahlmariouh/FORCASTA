import sqlite3
import os
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DB_PATH = "database/sales_forecasting.db"


def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema for users and projects."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        conn.commit()

        # Ensure default Master Admin exists with valid password
        cursor.execute("SELECT id, password_hash FROM users WHERE username = 'admin'")
        admin_row = cursor.fetchone()
        if not admin_row:
            admin_hash = get_password_hash("admin123")
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES ('admin', ?, 'admin')",
                (admin_hash,)
            )
            conn.commit()
        else:
            if not verify_password("admin123", admin_row["password_hash"]):
                new_hash = get_password_hash("admin123")
                cursor.execute(
                    "UPDATE users SET password_hash = ?, role = 'admin' WHERE username = 'admin'",
                    (new_hash,)
                )
                conn.commit()

        # Ensure default User account exists with valid password
        cursor.execute("SELECT id, password_hash FROM users WHERE username = 'user'")
        user_row = cursor.fetchone()
        if not user_row:
            user_hash = get_password_hash("user123")
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES ('user', ?, 'user')",
                (user_hash,)
            )
            conn.commit()
        else:
            if not verify_password("user123", user_row["password_hash"]):
                new_user_hash = get_password_hash("user123")
                cursor.execute(
                    "UPDATE users SET password_hash = ?, role = 'user' WHERE username = 'user'",
                    (new_user_hash,)
                )
                conn.commit()


def verify_password(plain_password, hashed_password):
    # Truncate to 72 characters to prevent bcrypt ValueError
    return pwd_context.verify(plain_password[:72], hashed_password)


def get_password_hash(password):
    # Truncate to 72 characters to prevent bcrypt ValueError
    return pwd_context.hash(password[:72])


def create_user(username, password, role="user"):
    """Creates a new user. Returns user_id if successful, None if username exists."""
    password_hash = get_password_hash(password)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def verify_user(username, password):
    """Verifies user credentials. Returns user dict if valid, None otherwise."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,),
        )
        user = cursor.fetchone()

        if user and verify_password(password, user["password_hash"]):
            return dict(user)
    return None


def create_project(user_id, name, description=""):
    """Creates a new project for a specific user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (user_id, name, description) VALUES (?, ?, ?)",
            (user_id, name, description),
        )
        conn.commit()
        return cursor.lastrowid


def get_user_projects(user_id):
    """Retrieves all projects for a specific user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, created_at FROM projects WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def delete_project(project_id):
    """Deletes a project and its metadata from the DB."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()


def get_user_by_id(user_id: int):
    """Retrieves a user by their unique primary key ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role FROM users WHERE id = ?",
            (user_id,),
        )
        user = cursor.fetchone()
        return dict(user) if user else None


def get_project_by_id(project_id: int):
    """Retrieves a single project by its ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, name, description, created_at FROM projects WHERE id = ?",
            (project_id,),
        )
        proj = cursor.fetchone()
        return dict(proj) if proj else None


def get_all_users():
    """Retrieves all users with their project counts and creation dates."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.created_at, COUNT(p.id) as project_count
            FROM users u
            LEFT JOIN projects p ON u.id = p.user_id
            GROUP BY u.id
            ORDER BY u.id ASC
        """)
        return [dict(row) for row in cursor.fetchall()]


def update_user_role(user_id: int, role: str):
    """Updates user's authorization role ('admin' or 'user')."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()
        return cursor.rowcount > 0


def update_user_password(user_id: int, new_password: str):
    """Hashes and updates user's password."""
    password_hash = get_password_hash(new_password)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_user(user_id: int):
    """Deletes a user, all their projects, and associated data files."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM projects WHERE user_id = ?", (user_id,))
        pids = [row["id"] for row in cursor.fetchall()]
        for pid in pids:
            for suffix in ["_clean.csv", "_features.csv", "_report.xlsx"]:
                fpath = f"data_storage/project_{pid}{suffix}"
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass
        cursor.execute("DELETE FROM projects WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_all_projects_admin():
    """Retrieves all projects across all users for admin inspection."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.description, p.created_at, p.user_id, u.username as owner_username
            FROM projects p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_db_stats():
    """Returns database size, record counts, and storage metrics."""
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    storage_files = 0
    storage_size = 0
    if os.path.exists("data_storage"):
        for f in os.listdir("data_storage"):
            fp = os.path.join("data_storage", f)
            if os.path.isfile(fp):
                storage_files += 1
                storage_size += os.path.getsize(fp)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]

    return {
        "db_size_bytes": db_size,
        "db_size_formatted": f"{db_size / 1024:.1f} KB" if db_size < 1024*1024 else f"{db_size / (1024*1024):.2f} MB",
        "user_count": user_count,
        "project_count": project_count,
        "storage_files": storage_files,
        "storage_size_formatted": f"{storage_size / 1024:.1f} KB" if storage_size < 1024*1024 else f"{storage_size / (1024*1024):.2f} MB",
        "sqlite_pages": page_count,
        "sqlite_page_size": page_size,
    }


def vacuum_database():
    """Runs VACUUM and PRAGMA integrity_check on the SQLite DB."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        cursor.execute("VACUUM")
        conn.commit()
    return integrity


def reset_all_users_and_create_admin(admin_username="admin", admin_password="admin123"):
    """
    Supprime tous les utilisateurs et projets existants, et crée le compte administrateur maître.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects")
        cursor.execute("DELETE FROM users")
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'projects')")
        except Exception:
            pass
        conn.commit()

    if os.path.exists("data_storage"):
        for f in os.listdir("data_storage"):
            fp = os.path.join("data_storage", f)
            if os.path.isfile(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass

    admin_id = create_user(admin_username, admin_password, role="admin")
    return admin_id


# Initialize database on module load
init_db()

