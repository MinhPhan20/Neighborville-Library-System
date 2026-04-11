import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

application = FastAPI(title = "Neightborville Public Library")
J2Templates = Jinja2Templates(directory = "templates")
application.mount("/static", StaticFiles(directory="static"), name="static")

#connection pool initialization
database_pool = pooling.MySQLConnectionPool(
   pool_name = "NLibraryPool",
    pool_size = 10,
    host = os.getenv('DB_HOST'),
    user = os.getenv('DB_USER'),
    password = os.getenv('DB_PASSWORD'),
    database = os.getenv('DB_NAME')
)

def get_database_connection():
    return database_pool.get_connection()

def checkout_book(book_id: int = Form(...), user_id: int = Form(...), employee_id: int = Form(...)):
    connection = get_database_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO CHECKOUTS (CHECKOUT_DATE, MEMBER_ID, EMPLOYEE_EMP_ID) VALUES (NOW(), %s, %s)", (user_id, employee_id))

    except Exception as e:
        cursor.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

#CHECKOUT_ID, CHECKOUT_DATE, MEMBER_ID, EMPLOYEE_EMP_ID

#CHECKOUT_ID, COPY_ID, CHECKOUT_ITEM_DUEDATE
def return_book(book_id: int = Form(...), user_id: int = Form(...)):
    
    pass

def search_books(title: str = Form(...)):
    connection = get_database_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT * FROM BOOKS WHERE TITLE LIKE %s", (f"%{title}%",))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

def place_hold(title_id: int = Form(...), user_id: int = Form(...)):
    connection = get_database_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("INSERT INTO HOLDS (TITLE_ID, MEMBER_ID, HOLD_DATE) VALUES (%s, %s, NOW())", (title_id, user_id))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()
    pass
