import os
from typing import Optional
from datetime import date, timedelta
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from mysql.connector import pooling, Error
from passlib.context import CryptContext
from dotenv import load_dotenv

# =================================================
# Security & App setup
# =================================================

load_dotenv() 

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

application = FastAPI(title="Neighborville Public Library - Manager Portal")
templates = Jinja2Templates(directory="templates")
application.mount("/static", StaticFiles(directory="static"), name="static")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

"""Verify a plain password against its hashed version."""
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

"""Hash a plain password using bcrypt for secure storage."""
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

"""Create and return a MySQL connection pool for efficient database access."""
def create_database_pool():
    try:
        pool = pooling.MySQLConnectionPool(
            pool_name="NLibraryPool",
            pool_size=5,
            host="localhost",
            user="root",
            password=os.getenv("DB_PASSWORD", ""), 
            database="Neighborville"
        )
        return pool
    except Error as e:
        print(f"Database pool creation failed: {e}")
        return None

database_pool = create_database_pool()

"""Get a database connection from the pool, raising an error if pool is not initialized."""
def get_database_connection():
    if database_pool is None:
        raise RuntimeError("Database is not configured.")
    return database_pool.get_connection()

"""Initialize the database by creating all necessary tables and inserting default data."""
def initialize_database():
    try:
        connection = get_database_connection()
        cursor = connection.cursor()

        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # --- ACTIVE DB WIPE FOR SCHEMA UPDATE ---
        # (Comment these back out after running it once!)
        # cursor.execute("DROP TABLE IF EXISTS CHECKOUT_ITEM")
        # cursor.execute("DROP TABLE IF EXISTS HOLD")
        # cursor.execute("DROP TABLE IF EXISTS FEE")
        # cursor.execute("DROP TABLE IF EXISTS TITLE_AUTHOR")
        # cursor.execute("DROP TABLE IF EXISTS BOOK_COPY")
        # cursor.execute("DROP TABLE IF EXISTS CHECKOUT")
        # cursor.execute("DROP TABLE IF EXISTS BOOK_TITLE")
        # cursor.execute("DROP TABLE IF EXISTS AUTHOR")
        # cursor.execute("DROP TABLE IF EXISTS PUBLISHER")
        # cursor.execute("DROP TABLE IF EXISTS EMPLOYEE")
        # cursor.execute("DROP TABLE IF EXISTS RANK_TABLE")
        # cursor.execute("DROP TABLE IF EXISTS MEMBER")
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        #Member table to store library members' information
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS MEMBER (
            MEMBER_ID INT AUTO_INCREMENT PRIMARY KEY,
            MEMBER_NAME VARCHAR(100) NOT NULL,
            MEMBER_EMAIL VARCHAR(100) NOT NULL UNIQUE
        )
        """)

        #Rank table to define employee roles and permissions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RANK_TABLE (
            RANK_ID INT AUTO_INCREMENT PRIMARY KEY,
            RANK_NAME VARCHAR(45) NOT NULL
        )
        """)

    #Employee table to store staff information, linked to their rank for permissions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS EMPLOYEE (
            EMP_ID INT AUTO_INCREMENT PRIMARY KEY,
            EMP_NAME VARCHAR(100) NOT NULL,
            EMP_EMAIL VARCHAR(100) NOT NULL UNIQUE,
            PASSWORD_HASH VARCHAR(255) NOT NULL,
            RANK_ID INT NOT NULL,
            FOREIGN KEY (RANK_ID) REFERENCES RANK_TABLE(RANK_ID)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        )
        """)

        #Author table to store information about book authors
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS AUTHOR (
            AUTHOR_ID INT AUTO_INCREMENT PRIMARY KEY,
            AUTHOR_NAME VARCHAR(100) NOT NULL
        )
        """)

        #Publisher table to store information about book publishers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS PUBLISHER (
            PUBLISHER_ID INT AUTO_INCREMENT PRIMARY KEY,
            PUBLISHER_NAME VARCHAR(100) NOT NULL
        )
        """)

        #Book Title table to store information about book titles, linked to publishers
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

        #Book Copy table to track individual copies of books, their status, and location
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS BOOK_COPY (
            COPY_ID INT AUTO_INCREMENT PRIMARY KEY,
            COPY_ISBN BIGINT NOT NULL UNIQUE,
            TITLE_ID INT NOT NULL,
            SHELF_LOCATION VARCHAR(100),
            STATUS VARCHAR(45) NOT NULL DEFAULT 'Available',
            FOREIGN KEY (TITLE_ID) REFERENCES BOOK_TITLE(TITLE_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            CONSTRAINT chk_book_copy_status
                CHECK (STATUS IN ('Available', 'Checked Out', 'On Hold', 'Lost', 'Damaged'))
        )
        """)

        #Title-Author junction table to handle many-to-many relationships between books and authors, with role information
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

        #Fee table to track outstanding fees for members, linked to the member and with status and amount
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS FEE (
            FEE_ID INT AUTO_INCREMENT PRIMARY KEY,
            FEE_AMOUNT DECIMAL(6,2) NOT NULL DEFAULT 0.00,
            FEE_STATUS VARCHAR(45) NOT NULL DEFAULT 'Outstanding',
            MEMBER_ID INT NOT NULL,
            FOREIGN KEY (MEMBER_ID) REFERENCES MEMBER(MEMBER_ID)
                ON DELETE CASCADE
                ON UPDATE CASCADE,
            CONSTRAINT chk_fee_amount CHECK (FEE_AMOUNT >= 0),
            CONSTRAINT chk_fee_status
                CHECK (FEE_STATUS IN ('Outstanding', 'Paid', 'Waived'))
        )
        """)

        #Hold table to track which members have placed holds on which book titles, with the date of the hold
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

        #Checkout table to track each checkout transaction, linked to the member and employee who processed it, with the date of the checkout
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

        #Checkout Item table to track each individual book copy that is part of a checkout transaction, with due dates, return dates, renewal counts, and status
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
                ON UPDATE CASCADE,
            CONSTRAINT chk_renew_count CHECK (RENEW_COUNT BETWEEN 0 AND 2),
            CONSTRAINT chk_checkout_item_status
                CHECK (STATUS IN ('Checked Out', 'Returned', 'Overdue'))
        )
        """)
        
        # Insert default ranks and a default manager account if they don't already exist
        try:
            cursor.execute("INSERT INTO RANK_TABLE (RANK_NAME) VALUES ('Manager'), ('Librarian')")
            default_manager_pw = get_password_hash("password123")
            cursor.execute(
                """
                INSERT INTO EMPLOYEE (EMP_NAME, EMP_EMAIL, PASSWORD_HASH, RANK_ID)
                VALUES ('System Manager', 'manager', %s, 1)
                """, (default_manager_pw,)
            )
            cursor.execute("INSERT INTO PUBLISHER (PUBLISHER_NAME) VALUES ('Default Publisher')")
            connection.commit()
            print("Database rebuilt and initialized successfully!")
        except:
            pass 
            
    except Exception as e:
        print(f"Error initializing DB: {e}")
    finally:
        try: cursor.close(); connection.close()
        except: pass

initialize_database()

# =================================================
# Helper functions for business logic
# =================================================

"""Calculate the total outstanding fees for a given member."""
def get_member_outstanding_fees(member_id: int) -> float:
    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COALESCE(SUM(FEE_AMOUNT), 0) AS TOTAL FROM FEE WHERE MEMBER_ID = %s AND FEE_STATUS = 'Outstanding'",(member_id,))
        row = cursor.fetchone()
        return float(row["TOTAL"]) if row else 0.0
    finally:
        cursor.close(); connection.close()

"""Get the number of active (checked out or overdue) books for a member."""
def get_member_active_checkout_count(member_id: int) -> int:
    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS TOTAL FROM CHECKOUT_ITEM ci JOIN CHECKOUT c ON ci.CHECKOUT_ID = c.CHECKOUT_ID WHERE c.MEMBER_ID = %s AND ci.STATUS IN ('Checked Out', 'Overdue')", (member_id,))
        row = cursor.fetchone()
        return int(row["TOTAL"]) if row else 0
    finally:
        cursor.close(); connection.close()

"""Update the status of checkout items that are past their due date to 'Overdue'."""
def refresh_overdue_items() -> None:
    connection = get_database_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE CHECKOUT_ITEM SET STATUS = 'Overdue' WHERE RETURN_DATE IS NULL AND CHECKOUT_ITEM_DUEDATE < CURDATE() AND STATUS = 'Checked Out'")
        connection.commit()
    finally:
        cursor.close(); connection.close()

# =================================================
# Auth & Page routes (MANAGER ONLY)
# =================================================

"""Render the login page or redirect authenticated staff to their dashboard."""
@application.get("/")
def home(request: Request, error: Optional[str] = None):
    if not error:
        session = request.cookies.get("library_session")
        if session and session.startswith("staff_"):
            try:
                connection = get_database_connection()
                cursor = connection.cursor()
                user_id = session.split("_")[1]
                cursor.execute("SELECT EMP_ID FROM EMPLOYEE WHERE EMP_ID = %s", (user_id,))
                if cursor.fetchone():
                    return RedirectResponse(url=f"/staff?id={user_id}", status_code=303)
            except Exception:
                pass
            finally:
                try: cursor.close(); connection.close()
                except: pass
            
            response = templates.TemplateResponse(request, "index.html", {"error": None})
            response.delete_cookie(key="library_session", path="/")
            return response
            
    return templates.TemplateResponse(request, "index.html", {"error": error})


"""Authenticate staff login and set session cookie on success."""
@application.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT EMP_ID, PASSWORD_HASH FROM EMPLOYEE WHERE EMP_EMAIL = %s", (username,))
        staff = cursor.fetchone()
        if staff and verify_password(password, staff["PASSWORD_HASH"]):
            response = RedirectResponse(url=f"/staff?id={staff['EMP_ID']}", status_code=303)
            response.set_cookie(key="library_session", value=f"staff_{staff['EMP_ID']}", max_age=2592000, path="/")
            return response
            
        return RedirectResponse(url="/?error=invalid", status_code=303)
    finally:
        cursor.close(); connection.close()

"""Clear the session cookie and redirect to login page."""
@application.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="library_session", path="/")
    return response

"""Render the staff dashboard page for authenticated employees."""
@application.get("/staff")
def staff_page(request: Request, id: Optional[str] = None):
    # First check for user ID in query parameter, then fall back to session cookie if not provided
    user_id = id
    if not user_id:
        session = request.cookies.get("library_session")
        if session and session.startswith("staff_"):
            user_id = session.split("_")[1]

    # If we still don't have a user ID, redirect to login page      
    if not user_id:
        return RedirectResponse(url="/")

    # Verify that the user ID corresponds to a valid employee in the database   
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT EMP_ID FROM EMPLOYEE WHERE EMP_ID = %s", (user_id,))
        if not cursor.fetchone():
            response = RedirectResponse(url="/", status_code=303)
            response.delete_cookie(key="library_session", path="/")
            return response
    except Exception: pass
    finally:
        try: cursor.close(); connection.close()
        except: pass

    # Render the staff dashboard with no-cache headers to prevent caching of sensitive information
    response = templates.TemplateResponse(request, "staff.html", {"user_id": user_id})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# =================================================
# FULL CRUD API Endpoints
# =================================================

# --- CREATE OPERATIONS ---

"""Create a new book title in the database using the title name, publication year, and publisher ID provided in the form data."""
@application.post("/api/create-book-title")
def create_book_title(title_name: str = Form(...), publication_year: int = Form(0), publisher_id: int = Form(...)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO BOOK_TITLE (TITLE_NAME, PUBLISHER_ID, PUBLICATION_YEAR) VALUES (%s, %s, %s)",
            (title_name, publisher_id, publication_year or None)
        )
        connection.commit()
        return {"message": f"Book title created. ID: {cursor.lastrowid}"}
    
    except Exception as e: 
        return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Create one or more book copies for a given title using the starting ISBN, title ID, and amount of new copies"""
@application.post("/api/create-book-copy")
def create_book_copy(copy_isbn: int = Form(...), title_id: int = Form(...), amount: int = Form(1)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        if amount < 1:
            amount = 1
        created_ids = []

        for i in range(amount):
            current_isbn = copy_isbn + i 
            cursor.execute(
                "INSERT INTO BOOK_COPY (COPY_ISBN, TITLE_ID, STATUS) VALUES (%s, %s, 'Available')",
                (current_isbn, title_id)
            )
            created_ids.append(str(cursor.lastrowid))
        connection.commit()

        if amount == 1: 
            return {"message": f"Book copy created. ID: {created_ids[0]}"}
        else: 
            return {"message": f"Created {amount} copies. IDs: {', '.join(created_ids)}"}
    
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Create a new checkout transaction for a member, checking business rules."""
@application.post("/api/create-checkout")
def create_checkout(member_id: int = Form(...), emp_id: int = Form(...)):
    try:
        # Check if member has outstanding fees or too many active checkouts before allowing new checkout
        outstanding = get_member_outstanding_fees(member_id)
        if outstanding >= FEE_BLOCK_THRESHOLD: 
            return {"error": f"Member blocked. Outstanding fees: ${outstanding:.2f}"}
        active_count = get_member_active_checkout_count(member_id)
        if active_count >= MAX_BOOKS_PER_MEMBER: 
            return {"error": f"Member hit maximum active books limit."}
        
        # If all checks pass, create the checkout record
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO CHECKOUT (CHECKOUT_DATE, MEMBER_ID, EMP_ID) VALUES (CURDATE(), %s, %s)", (member_id, emp_id))
        connection.commit()
        return {"message": f"Checkout created. ID: {cursor.lastrowid}"}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Add a book copy to an existing checkout transaction."""
@application.post("/api/create-checkout-item")
def create_checkout_item(checkout_id: int = Form(...), copy_id: int = Form(...)):
    try:
        #First verify that the book copy is available and that the checkout transaction exists
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT STATUS FROM BOOK_COPY WHERE COPY_ID = %s", (copy_id,))
        copy = cursor.fetchone()
        if not copy: 
            return {"error": "Book copy not found."}
        if copy["STATUS"] != "Available": 
            return {"error": f"Book copy is {copy['STATUS']}"}
        
        #Next get the checkout date from the CHECKOUT record to calculate the due date for this item
        cursor.execute("SELECT MEMBER_ID, CHECKOUT_DATE FROM CHECKOUT WHERE CHECKOUT_ID = %s", (checkout_id,))
        checkout = cursor.fetchone()
        if not checkout:
            return {"error": "Checkout not found."}
        checkout_date = checkout["CHECKOUT_DATE"]
        final_due_date = (checkout_date + timedelta(days=INITIAL_LOAN_DAYS)).isoformat()
        
        #If all checks pass, create the CHECKOUT_ITEM record and update the BOOK_COPY status to 'Checked Out'
        cursor2 = connection.cursor()
        cursor2.execute(
            "INSERT INTO CHECKOUT_ITEM (CHECKOUT_ID, COPY_ID, CHECKOUT_ITEM_DUEDATE, RETURN_DATE, RENEW_COUNT, STATUS) VALUES (%s, %s, %s, NULL, 0, 'Checked Out')",
            (checkout_id, copy_id, final_due_date)
        )
        cursor2.execute("UPDATE BOOK_COPY SET STATUS = 'Checked Out' WHERE COPY_ID = %s", (copy_id,))
        connection.commit()
        return {"message": "Item added to checkout."}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); cursor2.close(); connection.close()
        except: pass

"""Create a new library member with the provided name and email address."""
@application.post("/api/create-member")
def create_member(name: str = Form(...), email: str = Form(...)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO MEMBER (MEMBER_NAME, MEMBER_EMAIL) VALUES (%s, %s)",
            (name, email)
        )
        connection.commit()
        return {"message": f"Member was created. ID: {cursor.lastrowid}"}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Create a new employee with default password 'staff123'."""
@application.post("/api/create-employee")
def create_employee(emp_name: str = Form(...), emp_email: str = Form(...), rank_id: int = Form(...)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        hashed_pw = get_password_hash("staff123") 
        cursor.execute(
            "INSERT INTO EMPLOYEE (EMP_NAME, EMP_EMAIL, PASSWORD_HASH, RANK_ID) VALUES (%s, %s, %s, %s)", 
            (emp_name, emp_email, hashed_pw, rank_id)
        )
        connection.commit()
        return {"message": f"Employee hired. (Password: staff123) ID: {cursor.lastrowid}"}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass


# --- UPDATE OPERATIONS ---
"""Update member details or add a fee to their account."""
@application.post("/api/update-member")
def update_member(member_id: int = Form(...), name: str = Form(""), fee_amount: float = Form(0.0)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # Build the dynamic update query based on which fields were provided
        updates = []
        params = []
        if name:
            updates.append("MEMBER_NAME = %s")
            params.append(name)

        #Update member details if there are valid inputs, and track whether we actually updated anything to determine the response message later. 
        member_updated = False
        if updates:
            query = "UPDATE MEMBER SET " + ", ".join(updates) + " WHERE MEMBER_ID = %s"
            params.append(member_id)
            cursor.execute(query, tuple(params))
            if cursor.rowcount > 0:
                member_updated = True

        # If a fee amount was provided, attempt to add a new fee record for the member. We check if the member exists first to avoid adding fees to non-existent members.    
        fee_added = False
        if fee_amount > 0:
            cursor.execute("SELECT MEMBER_ID FROM MEMBER WHERE MEMBER_ID = %s", (member_id,))
            if cursor.fetchone():
                cursor.execute("INSERT INTO FEE (FEE_AMOUNT, FEE_STATUS, MEMBER_ID) VALUES (%s, 'Outstanding', %s)", (fee_amount, member_id))
                fee_added = True
            elif not member_updated:
                return {"error": "Member not found."}

        connection.commit()
        
        # If we didn't update member details or add a fee, return an error. Otherwise, build a success message indicating what was updated/added.
        if not member_updated and not fee_added:
            if updates: 
                return {"error": "Member not found."}
            return {"error": "No new data provided."}
        

        msg_parts = []
        if member_updated: 
            msg_parts.append("details updated")
        if fee_added: 
            msg_parts.append(f"fee of ${fee_amount:.2f} added")
        
        return {"message": f"Member {member_id}: " + " and ".join(msg_parts) + "."}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Update employee details."""
@application.post("/api/update-employee")
def update_employee(emp_id: int = Form(...), emp_name: str = Form(""), emp_email: str = Form(""), rank_id: int = Form(0)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # Build the dynamic update query based on which fields were provided
        updates = []
        params = []
        if emp_name:
            updates.append("EMP_NAME = %s")
            params.append(emp_name)
        if emp_email:
            updates.append("EMP_EMAIL = %s")
            params.append(emp_email)
        if rank_id > 0:
            updates.append("RANK_ID = %s")
            params.append(rank_id)
            
        if not updates:
            return {"error": "No new data provided."}

       # Construct the final update query and execute it     
        query = "UPDATE EMPLOYEE SET " + ", ".join(updates) + " WHERE EMP_ID = %s"
        params.append(emp_id)
        
        cursor.execute(query, tuple(params))
        connection.commit()
        
        if cursor.rowcount == 0:
            return {"error": "Employee not found."}
            
        return {"message": f"Employee {emp_id} was updated."}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Return a checked out book and calculate any late fees."""
@application.post("/api/return-checkout-item")
def return_checkout_item(checkout_id: int = Form(...), copy_id: int = Form(...)):
    try:
        # First verify that the checkout item exists and is currently checked out, and get the due date and member ID for fee calculation
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT ci.CHECKOUT_ITEM_DUEDATE, ci.RETURN_DATE, c.MEMBER_ID FROM CHECKOUT_ITEM ci JOIN CHECKOUT c ON ci.CHECKOUT_ID = c.CHECKOUT_ID WHERE ci.CHECKOUT_ID = %s AND ci.COPY_ID = %s",
            (checkout_id, copy_id)
        )
        row = cursor.fetchone()
        if not row: 
            return {"error": "Checkout item not found."}
        if row["RETURN_DATE"] is not None: 
            return {"error": "Book already returned."}
        
        #Calculate late fees based on how many days past the due date the book is being returned
        due_date = row["CHECKOUT_ITEM_DUEDATE"]
        member_id = row["MEMBER_ID"]
        today = date.today()
        late_days = max((today - due_date).days, 0)
        fee_amount = round(late_days * LATE_FEE_PER_DAY, 2)
        
        # If the book is late, add a fee record for the member. Then we update the CHECKOUT_ITEM record to set the return date and status, 
        # and update the BOOK_COPY status back to 'Available'.
        cursor2 = connection.cursor()
        cursor2.execute("UPDATE CHECKOUT_ITEM SET RETURN_DATE = CURDATE(), STATUS = 'Returned' WHERE CHECKOUT_ID = %s AND COPY_ID = %s", (checkout_id, copy_id))
        cursor2.execute("UPDATE BOOK_COPY SET STATUS = 'Available' WHERE COPY_ID = %s", (copy_id,))
        if fee_amount > 0: cursor2.execute("INSERT INTO FEE (FEE_AMOUNT, FEE_STATUS, MEMBER_ID) VALUES (%s, 'Outstanding', %s)", (fee_amount, member_id))
        connection.commit()
        
        if fee_amount > 0: return {"message": f"Book was returned. Late fee added: ${fee_amount:.2f}"}
        return {"message": "Book was returned."}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); cursor2.close(); connection.close()
        except: pass


# --- DELETE OPERATIONS ---

"""Remove an employee from the system."""
@application.post("/api/fire-employee")
def fire_employee(emp_id: int = Form(...)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM EMPLOYEE WHERE EMP_ID = %s", (emp_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return {"error": "Employee not found."}
        return {"message": f"Employee {emp_id} was terminated."}
    except Exception as e: return {"error": "Cannot delete employee."}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Remove a member from the system."""
@application.post("/api/remove-member")
def remove_member(member_id: int = Form(...)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM MEMBER WHERE MEMBER_ID = %s", (member_id,))
        connection.commit()
        if cursor.rowcount == 0: 
            return {"error": "Member not found."}
        return {"message": f"Member {member_id} was removed."}
    except Exception as e: return {"error": "Cannot delete active member."}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Remove a fee record from the system."""
@application.post("/api/remove-fee")
def remove_fee(fee_id: int = Form(...)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM FEE WHERE FEE_ID = %s", (fee_id,))
        connection.commit()
        if cursor.rowcount == 0: 
            return {"error": "Fee not found."}
        return {"message": f"Fee {fee_id} was removed."}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass


# --- READ & SEARCH OPERATIONS ---

"""Search the database for books, members, publishers, authors, or employees."""
@application.post("/api/search")
def search_database(search_type: str = Form(...), query: str = Form(...)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        search_term = f"%{query}%"

        #search database table based on selected option in staff.html dropdown menu
        if search_type == "books":
            cursor.execute("SELECT TITLE_ID, TITLE_NAME, PUBLICATION_YEAR FROM BOOK_TITLE WHERE TITLE_NAME LIKE %s", (search_term,))
        elif search_type == "members":
            cursor.execute("SELECT MEMBER_ID, MEMBER_NAME, MEMBER_EMAIL FROM MEMBER WHERE MEMBER_NAME LIKE %s OR MEMBER_EMAIL LIKE %s", (search_term, search_term))
        elif search_type == "publishers":
            cursor.execute("SELECT PUBLISHER_ID, PUBLISHER_NAME FROM PUBLISHER WHERE PUBLISHER_NAME LIKE %s", (search_term,))
        elif search_type == "authors":
            cursor.execute("SELECT AUTHOR_ID, AUTHOR_NAME FROM AUTHOR WHERE AUTHOR_NAME LIKE %s", (search_term,))
        elif search_type == "employees":
            cursor.execute("SELECT e.EMP_ID, e.EMP_NAME, e.EMP_EMAIL, r.RANK_NAME FROM EMPLOYEE e JOIN RANK_TABLE r ON e.RANK_ID = r.RANK_ID WHERE e.EMP_NAME LIKE %s OR e.EMP_EMAIL LIKE %s", (search_term, search_term))
        else:
            return {"error": "Invalid search type."}

        results = cursor.fetchall()
        return {"results": results, "type": search_type}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Retrieve the checkout history for a specific member."""
@application.post("/api/member-checkouts")
def get_member_checkouts(member_id: int = Form(...)):
    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        
        # First verify that the member exists and get their name for the report header
        cursor.execute("SELECT MEMBER_NAME FROM MEMBER WHERE MEMBER_ID = %s", (member_id,))
        member = cursor.fetchone()
        if not member:
            return {"error": "Member not found."}
        
        # Then retrieve the checkout history for that member, including book titles, due dates, return dates, and status.
        query = """
            SELECT c.CHECKOUT_ID, ci.COPY_ID, bt.TITLE_NAME, ci.CHECKOUT_ITEM_DUEDATE, ci.RETURN_DATE, ci.STATUS 
            FROM CHECKOUT c 
            JOIN CHECKOUT_ITEM ci ON c.CHECKOUT_ID = ci.CHECKOUT_ID 
            JOIN BOOK_COPY bc ON ci.COPY_ID = bc.COPY_ID 
            JOIN BOOK_TITLE bt ON bc.TITLE_ID = bt.TITLE_ID 
            WHERE c.MEMBER_ID = %s
            ORDER BY ci.CHECKOUT_ITEM_DUEDATE DESC
        """
        cursor.execute(query, (member_id,))
        results = cursor.fetchall()
        
        # Format the dates in the results to ISO format strings for JSON serialization, and handle null return dates by indicating "Not Returned"
        for row in results:
            if row['CHECKOUT_ITEM_DUEDATE']:
                row['CHECKOUT_ITEM_DUEDATE'] = row['CHECKOUT_ITEM_DUEDATE'].isoformat()
            if row['RETURN_DATE']:
                row['RETURN_DATE'] = row['RETURN_DATE'].isoformat()
            else:
                row['RETURN_DATE'] = "Not Returned"
                
        return {"results": results, "member_name": member["MEMBER_NAME"]}
    except Exception as e:
        return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass

"""Generate a report of all currently checked out books."""
@application.get("/api/report/all-current-checkouts")
def report_all_current_checkouts():
    try:
        refresh_overdue_items() 
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        # Retrieve all currently checked out books, including the checkout ID, book title, member name, due date, and status. 
        # We join across multiple tables to get all the relevant information in one query.
        query = """
            SELECT ci.CHECKOUT_ID, bt.TITLE_NAME, m.MEMBER_NAME, ci.CHECKOUT_ITEM_DUEDATE, ci.STATUS
            FROM CHECKOUT_ITEM ci 
            JOIN CHECKOUT c ON ci.CHECKOUT_ID = c.CHECKOUT_ID 
            JOIN BOOK_COPY bc ON ci.COPY_ID = bc.COPY_ID 
            JOIN BOOK_TITLE bt ON bc.TITLE_ID = bt.TITLE_ID 
            JOIN MEMBER m ON c.MEMBER_ID = m.MEMBER_ID
            WHERE ci.RETURN_DATE IS NULL
            ORDER BY ci.CHECKOUT_ITEM_DUEDATE ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Format the due dates in the results to ISO format strings for JSON serialization
        for row in results:
            if row['CHECKOUT_ITEM_DUEDATE']:
                row['CHECKOUT_ITEM_DUEDATE'] = row['CHECKOUT_ITEM_DUEDATE'].isoformat()
                
        return {"results": results}
    except Exception as e: return {"error": str(e)}
    finally:
        try: cursor.close(); connection.close()
        except: pass
