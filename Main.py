import os
from typing import Optional
from datetime import date, timedelta

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from mysql.connector import pooling, Error
from passlib.context import CryptContext
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

application = FastAPI(title="Neighborville Public Library")
templates = Jinja2Templates(directory="templates")
application.mount("/static", StaticFiles(directory="static"), name="static")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# =================================================
# Constants / business rules
# =================================================

MAX_BOOKS_PER_MEMBER = 20
FEE_BLOCK_THRESHOLD = 500.00
INITIAL_LOAN_DAYS = 14
MAX_RENEWALS = 2
RENEWAL_DAYS = 14
ABSOLUTE_MAX_LOAN_DAYS = 49
LATE_FEE_PER_DAY = 0.50


# =================================================
# Database setup
# =================================================

def create_database_pool():
    try:
        pool = pooling.MySQLConnectionPool(
            pool_name="NLibraryPool",
            pool_size=5,
            host="localhost",
            user="root",
            password=os.getenv("DB_PASSWORD", "password"),
            database="Neighborville"
        )
        return pool
    except Error as e:
        print(f"Database pool creation failed: {e}")
        return None


database_pool = create_database_pool()


def get_database_connection():
    if database_pool is None:
        raise RuntimeError("Database is not configured.")
    return database_pool.get_connection()


def initialize_database():
    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS MEMBER (
            MEMBER_ID INT AUTO_INCREMENT PRIMARY KEY,
            MEMBER_NAME VARCHAR(100) NOT NULL,
            MEMBER_USERNAME VARCHAR(100) NOT NULL UNIQUE,
            PASSWORD_HASH VARCHAR(255) NOT NULL,
            MEMBER_PHONE VARCHAR(20),
            AGE INT,
            ACCOUNT_STATUS VARCHAR(45) DEFAULT 'Active'
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS EMP_RANK (
            RANK_ID INT AUTO_INCREMENT PRIMARY KEY,
            RANK_NAME VARCHAR(45) NOT NULL UNIQUE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS EMPLOYEE (
            EMP_ID INT AUTO_INCREMENT PRIMARY KEY,
            EMP_NAME VARCHAR(100) NOT NULL,
            EMP_USERNAME VARCHAR(100) NOT NULL UNIQUE,
            PASSWORD_HASH VARCHAR(255) NOT NULL,
            RANK_ID INT NOT NULL,
            FOREIGN KEY (RANK_ID) REFERENCES EMP_RANK(RANK_ID)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS AUTHOR (
            AUTHOR_ID INT AUTO_INCREMENT PRIMARY KEY,
            AUTHOR_NAME VARCHAR(100) NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS PUBLISHER (
            PUBLISHER_ID INT AUTO_INCREMENT PRIMARY KEY,
            PUBLISHER_NAME VARCHAR(100) NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS BOOK_TITLE (
            TITLE_ID INT AUTO_INCREMENT PRIMARY KEY,
            TITLE_NAME VARCHAR(255) NOT NULL,
            PUBLISHER_ID INT NOT NULL,
            GENRE VARCHAR(100),
            SUBJECT_AREA VARCHAR(100),
            EDITION VARCHAR(50),
            PUBLICATION_YEAR INT,
            AGE_RESTRICTION INT DEFAULT 0,
            FOREIGN KEY (PUBLISHER_ID) REFERENCES PUBLISHER(PUBLISHER_ID)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS BOOK_COPY (
            COPY_ID INT AUTO_INCREMENT PRIMARY KEY,
            COPY_ISBN BIGINT NOT NULL UNIQUE,
            TITLE_ID INT NOT NULL,
            SHELF_LOCATION VARCHAR(100),
            STATUS VARCHAR(45) NOT NULL DEFAULT 'Available',
            FOREIGN KEY (TITLE_ID) REFERENCES BOOK_TITLE(TITLE_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS TITLE_AUTHOR (
            TITLE_ID INT NOT NULL,
            AUTHOR_ID INT NOT NULL,
            TITLE_AUTHOR_ROLE VARCHAR(45),
            PRIMARY KEY (TITLE_ID, AUTHOR_ID),
            FOREIGN KEY (TITLE_ID) REFERENCES BOOK_TITLE(TITLE_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            FOREIGN KEY (AUTHOR_ID) REFERENCES AUTHOR(AUTHOR_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS FEE (
            FEE_ID INT AUTO_INCREMENT PRIMARY KEY,
            FEE_AMOUNT DECIMAL(6,2) NOT NULL DEFAULT 0.00,
            FEE_STATUS VARCHAR(45) NOT NULL DEFAULT 'Outstanding',
            MEMBER_ID INT NOT NULL,
            FOREIGN KEY (MEMBER_ID) REFERENCES MEMBER(MEMBER_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS HOLD (
            MEMBER_ID INT NOT NULL,
            TITLE_ID INT NOT NULL,
            HOLD_DATE DATE NOT NULL,
            PRIMARY KEY (MEMBER_ID, TITLE_ID),
            FOREIGN KEY (MEMBER_ID) REFERENCES MEMBER(MEMBER_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            FOREIGN KEY (TITLE_ID) REFERENCES BOOK_TITLE(TITLE_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS CHECKOUT (
            CHECKOUT_ID INT AUTO_INCREMENT PRIMARY KEY,
            CHECKOUT_DATE DATE NOT NULL,
            MEMBER_ID INT NOT NULL,
            EMP_ID INT NOT NULL,
            FOREIGN KEY (MEMBER_ID) REFERENCES MEMBER(MEMBER_ID)
                ON DELETE RESTRICT
                ON UPDATE CASCADE,
            FOREIGN KEY (EMP_ID) REFERENCES EMPLOYEE(EMP_ID)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS CHECKOUT_ITEM (
            CHECKOUT_ID INT NOT NULL,
            COPY_ID INT NOT NULL,
            CHECKOUT_ITEM_DUEDATE DATE NOT NULL,
            RETURN_DATE DATE NULL,
            RENEW_COUNT INT NOT NULL DEFAULT 0,
            STATUS VARCHAR(45) NOT NULL DEFAULT 'Checked Out',
            PRIMARY KEY (CHECKOUT_ID, COPY_ID),
            FOREIGN KEY (CHECKOUT_ID) REFERENCES CHECKOUT(CHECKOUT_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            FOREIGN KEY (COPY_ID) REFERENCES BOOK_COPY(COPY_ID)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        )
        """)

        # Ensure Manager rank exists
        cursor.execute("SELECT RANK_ID FROM EMP_RANK WHERE RANK_NAME = 'Manager'")
        rank_row = cursor.fetchone()
        if rank_row:
            rank_id = rank_row[0]
        else:
            cursor.execute("INSERT INTO EMP_RANK (RANK_NAME) VALUES ('Manager')")
            rank_id = cursor.lastrowid

        # Optional default publisher
        cursor.execute("SELECT PUBLISHER_ID FROM PUBLISHER WHERE PUBLISHER_NAME = 'Default Publisher'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO PUBLISHER (PUBLISHER_NAME) VALUES ('Default Publisher')")

        # Optional default manager from .env
        manager_name = os.getenv("DEFAULT_MANAGER_NAME")
        manager_username = os.getenv("DEFAULT_MANAGER_USERNAME")
        manager_password = os.getenv("DEFAULT_MANAGER_PASSWORD")

        if manager_name and manager_username and manager_password:
            cursor.execute(
                "SELECT EMP_ID FROM EMPLOYEE WHERE EMP_USERNAME = %s",
                (manager_username,)
            )
            existing_manager = cursor.fetchone()

            if not existing_manager:
                hashed_password = get_password_hash(manager_password)
                cursor.execute(
                    """
                    INSERT INTO EMPLOYEE (EMP_NAME, EMP_USERNAME, PASSWORD_HASH, RANK_ID)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (manager_name, manager_username, hashed_password, rank_id)
                )

        connection.commit()
        print("Database initialized successfully.")

    except Exception as e:
        import traceback
        print(f"Error initializing DB: {e}")
        traceback.print_exc()
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass

initialize_database()


# =================================================
# Helper functions for business logic
# =================================================

def get_member_outstanding_fees(member_id: int) -> float:
    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT COALESCE(SUM(FEE_AMOUNT), 0) AS TOTAL
            FROM FEE
            WHERE MEMBER_ID = %s AND FEE_STATUS = 'Outstanding'
            """,
            (member_id,)
        )
        row = cursor.fetchone()
        return float(row["TOTAL"]) if row else 0.0
    finally:
        cursor.close()
        connection.close()


def get_member_active_checkout_count(member_id: int) -> int:
    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS TOTAL
            FROM CHECKOUT_ITEM ci
            JOIN CHECKOUT c ON ci.CHECKOUT_ID = c.CHECKOUT_ID
            WHERE c.MEMBER_ID = %s
              AND ci.STATUS IN ('Checked Out', 'Overdue')
            """,
            (member_id,)
        )
        row = cursor.fetchone()
        return int(row["TOTAL"]) if row else 0
    finally:
        cursor.close()
        connection.close()


def refresh_overdue_items() -> None:
    connection = get_database_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE CHECKOUT_ITEM
            SET STATUS = 'Overdue'
            WHERE RETURN_DATE IS NULL
              AND CHECKOUT_ITEM_DUEDATE < CURDATE()
              AND STATUS = 'Checked Out'
            """
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


# =================================================
# Auth & Page routes
# =================================================

@application.get("/")
def home(request: Request, error: Optional[str] = None):
    if not error:
        session = request.cookies.get("library_session")
        if session:
            connection = None
            cursor = None
            try:
                connection = get_database_connection()
                cursor = connection.cursor()
                role, user_id = session.split("_", 1)

                if role == "staff":
                    cursor.execute("SELECT EMP_ID FROM EMPLOYEE WHERE EMP_ID = %s", (user_id,))
                    if cursor.fetchone():
                        return RedirectResponse(url=f"/staff?id={user_id}", status_code=303)
            except Exception:
                pass
            finally:
                try:
                    if cursor:
                        cursor.close()
                    if connection:
                        connection.close()
                except Exception:
                    pass

            response = templates.TemplateResponse(request, "index.html", {"error": None})
            response.delete_cookie(key="library_session", path="/")
            response.delete_cookie(key="library_session")
            return response

    return templates.TemplateResponse(request, "index.html", {"error": error})


@application.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT EMP_ID, PASSWORD_HASH FROM EMPLOYEE WHERE EMP_USERNAME = %s",
            (username,)
        )
        user = cursor.fetchone()

        if user and verify_password(password, user["PASSWORD_HASH"]):
            response = RedirectResponse(url=f"/staff?id={user['EMP_ID']}", status_code=303)
            response.set_cookie(
                key="library_session",
                value=f"staff_{user['EMP_ID']}",
                max_age=2592000,
                path="/"
            )
            return response

        return RedirectResponse(url="/?error=invalid", status_code=303)
    finally:
        cursor.close()
        connection.close()


@application.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="library_session", path="/")
    response.delete_cookie(key="library_session")
    return response


@application.get("/member")
def member_page(request: Request, id: Optional[str] = None):
    user_id = id
    if not user_id:
        session = request.cookies.get("library_session")
        if session and session.startswith("member_"):
            user_id = session.split("_", 1)[1]

    if not user_id:
        return RedirectResponse(url="/")

    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT MEMBER_ID FROM MEMBER WHERE MEMBER_ID = %s", (user_id,))
        if not cursor.fetchone():
            response = RedirectResponse(url="/", status_code=303)
            response.delete_cookie(key="library_session", path="/")
            response.delete_cookie(key="library_session")
            return response
    except Exception:
        pass
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass

    response = templates.TemplateResponse(request, "member.html", {"user_id": user_id})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@application.get("/staff")
def staff_page(request: Request, id: Optional[str] = None):
    user_id = id
    if not user_id:
        session = request.cookies.get("library_session")
        if session and session.startswith("staff_"):
            user_id = session.split("_", 1)[1]

    if not user_id:
        return RedirectResponse(url="/")

    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT EMP_ID FROM EMPLOYEE WHERE EMP_ID = %s", (user_id,))
        if not cursor.fetchone():
            response = RedirectResponse(url="/", status_code=303)
            response.delete_cookie(key="library_session", path="/")
            response.delete_cookie(key="library_session")
            return response
    except Exception:
        pass
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass

    response = templates.TemplateResponse(request, "staff.html", {"user_id": user_id})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# =================================================
# CRUD & API Endpoints
# =================================================

@application.post("/api/create-member")
def create_member(
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    phone: str = Form(""),
    age: int = Form(0)
):
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        hashed_pw = get_password_hash(password)
        cursor.execute(
            """
            INSERT INTO MEMBER (MEMBER_NAME, MEMBER_USERNAME, PASSWORD_HASH, MEMBER_PHONE, AGE)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, username, hashed_pw, phone or None, age)
        )
        connection.commit()
        return {"message": "Account created successfully!", "member_id": cursor.lastrowid}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.post("/api/create-publisher")
def create_publisher(publisher_name: str = Form(...)):
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO PUBLISHER (PUBLISHER_NAME) VALUES (%s)",
            (publisher_name,)
        )
        connection.commit()
        return {"message": "Publisher created", "publisher_id": cursor.lastrowid}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.post("/api/create-author")
def create_author(author_name: str = Form(...)):
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO AUTHOR (AUTHOR_NAME) VALUES (%s)",
            (author_name,)
        )
        connection.commit()
        return {"message": "Author created", "author_id": cursor.lastrowid}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.post("/api/create-book-title")
def create_book_title(
    title_name: str = Form(...),
    publisher_id: int = Form(...),
    genre: str = Form(""),
    subject_area: str = Form(""),
    edition: str = Form(""),
    publication_year: int = Form(0),
    age_restriction: int = Form(0)
):
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO BOOK_TITLE
            (TITLE_NAME, PUBLISHER_ID, GENRE, SUBJECT_AREA, EDITION, PUBLICATION_YEAR, AGE_RESTRICTION)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                title_name,
                publisher_id,
                genre or None,
                subject_area or None,
                edition or None,
                publication_year or None,
                age_restriction
            )
        )
        connection.commit()
        return {"message": "Book title created", "title_id": cursor.lastrowid}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.post("/api/create-book-copy")
def create_book_copy(
    copy_isbn: int = Form(...),
    title_id: int = Form(...),
    shelf_location: str = Form(""),
    status: str = Form("Available")
):
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO BOOK_COPY (COPY_ISBN, TITLE_ID, SHELF_LOCATION, STATUS)
            VALUES (%s, %s, %s, %s)
            """,
            (copy_isbn, title_id, shelf_location or None, status)
        )
        connection.commit()
        return {"message": "Book copy created", "copy_id": cursor.lastrowid}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.post("/api/create-checkout")
def create_checkout(member_id: int = Form(...), emp_id: int = Form(...)):
    connection = None
    cursor = None
    try:
        outstanding = get_member_outstanding_fees(member_id)
        if outstanding >= FEE_BLOCK_THRESHOLD:
            return {"error": f"Member cannot check out books. Outstanding fees: ${outstanding:.2f}"}

        active_count = get_member_active_checkout_count(member_id)
        if active_count >= MAX_BOOKS_PER_MEMBER:
            return {"error": f"Member already has {active_count} active books. Limit is {MAX_BOOKS_PER_MEMBER}."}

        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO CHECKOUT (CHECKOUT_DATE, MEMBER_ID, EMP_ID) VALUES (CURDATE(), %s, %s)",
            (member_id, emp_id)
        )
        connection.commit()
        return {"message": "Checkout created", "checkout_id": cursor.lastrowid}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.post("/api/create-checkout-item")
def create_checkout_item(
    checkout_id: int = Form(...),
    copy_id: int = Form(...),
    due_date: str = Form("")
):
    connection = None
    cursor = None
    cursor2 = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT STATUS FROM BOOK_COPY WHERE COPY_ID = %s", (copy_id,))
        copy = cursor.fetchone()
        if not copy:
            return {"error": "Book copy not found."}
        if copy["STATUS"] != "Available":
            return {"error": f"Book copy is not available. Current status: {copy['STATUS']}"}

        cursor.execute(
            "SELECT MEMBER_ID, CHECKOUT_DATE FROM CHECKOUT WHERE CHECKOUT_ID = %s",
            (checkout_id,)
        )
        checkout = cursor.fetchone()
        if not checkout:
            return {"error": "Checkout not found."}

        member_id = checkout["MEMBER_ID"]
        outstanding = get_member_outstanding_fees(member_id)
        if outstanding >= FEE_BLOCK_THRESHOLD:
            return {"error": f"Member cannot check out books. Outstanding fees: ${outstanding:.2f}"}

        active_count = get_member_active_checkout_count(member_id)
        if active_count >= MAX_BOOKS_PER_MEMBER:
            return {"error": f"Member already has {active_count} active books. Limit is {MAX_BOOKS_PER_MEMBER}."}

        checkout_date = checkout["CHECKOUT_DATE"]
        final_due_date = due_date or (checkout_date + timedelta(days=INITIAL_LOAN_DAYS)).isoformat()

        cursor2 = connection.cursor()
        cursor2.execute(
            """
            INSERT INTO CHECKOUT_ITEM
            (CHECKOUT_ID, COPY_ID, CHECKOUT_ITEM_DUEDATE, RETURN_DATE, RENEW_COUNT, STATUS)
            VALUES (%s, %s, %s, NULL, 0, 'Checked Out')
            """,
            (checkout_id, copy_id, final_due_date)
        )
        cursor2.execute(
            "UPDATE BOOK_COPY SET STATUS = 'Checked Out' WHERE COPY_ID = %s",
            (copy_id,)
        )
        connection.commit()
        return {"message": "Checkout item created"}

    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if cursor2:
                cursor2.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.post("/api/return-checkout-item")
def return_checkout_item(checkout_id: int = Form(...), copy_id: int = Form(...)):
    connection = None
    cursor = None
    cursor2 = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ci.CHECKOUT_ITEM_DUEDATE, ci.RETURN_DATE, c.MEMBER_ID
            FROM CHECKOUT_ITEM ci
            JOIN CHECKOUT c ON ci.CHECKOUT_ID = c.CHECKOUT_ID
            WHERE ci.CHECKOUT_ID = %s AND ci.COPY_ID = %s
            """,
            (checkout_id, copy_id)
        )
        row = cursor.fetchone()
        if not row:
            return {"error": "Checkout item not found."}
        if row["RETURN_DATE"] is not None:
            return {"error": "Book already returned."}

        due_date = row["CHECKOUT_ITEM_DUEDATE"]
        member_id = row["MEMBER_ID"]
        today = date.today()
        late_days = max((today - due_date).days, 0)
        fee_amount = round(late_days * LATE_FEE_PER_DAY, 2)

        cursor2 = connection.cursor()
        cursor2.execute(
            "UPDATE CHECKOUT_ITEM SET RETURN_DATE = CURDATE(), STATUS = 'Returned' WHERE CHECKOUT_ID = %s AND COPY_ID = %s",
            (checkout_id, copy_id)
        )
        cursor2.execute(
            "UPDATE BOOK_COPY SET STATUS = 'Available' WHERE COPY_ID = %s",
            (copy_id,)
        )

        if fee_amount > 0:
            cursor2.execute(
                "INSERT INTO FEE (FEE_AMOUNT, FEE_STATUS, MEMBER_ID) VALUES (%s, 'Outstanding', %s)",
                (fee_amount, member_id)
            )

        connection.commit()

        if fee_amount > 0:
            return {"message": f"Book returned. Late fee added: ${fee_amount:.2f}"}
        return {"message": "Book returned successfully"}

    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if cursor2:
                cursor2.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.post("/api/renew-checkout-item")
def renew_checkout_item(checkout_id: int = Form(...), copy_id: int = Form(...)):
    connection = None
    cursor = None
    cursor2 = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ci.CHECKOUT_ITEM_DUEDATE, ci.RENEW_COUNT, ci.RETURN_DATE, ci.STATUS, c.CHECKOUT_DATE
            FROM CHECKOUT_ITEM ci
            JOIN CHECKOUT c ON ci.CHECKOUT_ID = c.CHECKOUT_ID
            WHERE ci.CHECKOUT_ID = %s AND ci.COPY_ID = %s
            """,
            (checkout_id, copy_id)
        )
        row = cursor.fetchone()
        if not row:
            return {"error": "Checkout item not found."}
        if row["RETURN_DATE"] is not None:
            return {"error": "Returned items cannot be renewed."}
        if row["RENEW_COUNT"] >= MAX_RENEWALS:
            return {"error": "Maximum renewals reached."}

        checkout_date = row["CHECKOUT_DATE"]
        current_due = row["CHECKOUT_ITEM_DUEDATE"]
        proposed_due = current_due + timedelta(days=RENEWAL_DAYS)
        max_due = checkout_date + timedelta(days=ABSOLUTE_MAX_LOAN_DAYS)
        if proposed_due > max_due:
            proposed_due = max_due

        cursor2 = connection.cursor()
        cursor2.execute(
            """
            UPDATE CHECKOUT_ITEM
            SET CHECKOUT_ITEM_DUEDATE = %s,
                RENEW_COUNT = RENEW_COUNT + 1,
                STATUS = 'Checked Out'
            WHERE CHECKOUT_ID = %s AND COPY_ID = %s
            """,
            (proposed_due, checkout_id, copy_id)
        )
        connection.commit()
        return {"message": "Checkout item renewed", "new_due_date": str(proposed_due)}

    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if cursor2:
                cursor2.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.post("/api/search-books")
def search_books(title: str = Form(...)):
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM BOOK_TITLE WHERE TITLE_NAME LIKE %s",
            (f"%{title}%",)
        )
        return {"results": cursor.fetchall()}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.get("/api/report/most-borrowed-titles")
def report_most_borrowed_titles():
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT bt.TITLE_ID, bt.TITLE_NAME, COUNT(*) AS BORROW_COUNT
            FROM CHECKOUT_ITEM ci
            JOIN BOOK_COPY bc ON ci.COPY_ID = bc.COPY_ID
            JOIN BOOK_TITLE bt ON bc.TITLE_ID = bt.TITLE_ID
            GROUP BY bt.TITLE_ID, bt.TITLE_NAME
            ORDER BY BORROW_COUNT DESC, bt.TITLE_NAME ASC
            """
        )
        return {"results": cursor.fetchall()}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.get("/api/report/overdue-items")
def report_overdue_items():
    connection = None
    cursor = None
    try:
        refresh_overdue_items()
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ci.CHECKOUT_ID, ci.COPY_ID, ci.CHECKOUT_ITEM_DUEDATE, c.MEMBER_ID
            FROM CHECKOUT_ITEM ci
            JOIN CHECKOUT c ON ci.CHECKOUT_ID = c.CHECKOUT_ID
            WHERE ci.STATUS = 'Overdue'
            ORDER BY ci.CHECKOUT_ITEM_DUEDATE ASC
            """
        )
        return {"results": cursor.fetchall()}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass


@application.get("/api/member/{member_id}/checkouts")
def get_member_checkouts(member_id: int):
    connection = None
    cursor = None
    try:
        refresh_overdue_items()
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT bt.TITLE_NAME, ci.CHECKOUT_ITEM_DUEDATE, ci.STATUS
            FROM CHECKOUT_ITEM ci
            JOIN BOOK_COPY bc ON ci.COPY_ID = bc.COPY_ID
            JOIN BOOK_TITLE bt ON bc.TITLE_ID = bt.TITLE_ID
            JOIN CHECKOUT c ON ci.CHECKOUT_ID = c.CHECKOUT_ID
            WHERE c.MEMBER_ID = %s
              AND ci.STATUS IN ('Checked Out', 'Overdue')
            ORDER BY ci.CHECKOUT_ITEM_DUEDATE ASC
            """,
            (member_id,)
        )
        return {"checkouts": cursor.fetchall()}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception:
            pass
        
        
        
