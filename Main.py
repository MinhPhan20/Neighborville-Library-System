import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from mysql.connector import pooling
from dotenv import load_dotenv

checkoutBooks = [] #global array to hold books being checked out until checkout is processed

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

#=================================================book checkout functions=================================================

def create_checkout(member_id: int = Form(...), employee_id: int = Form(...)):
    connection = get_database_connection
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO CHECKOUTS (CHECKOUT_DATE, MEMBER_ID, EMPLOYEE_EMP_ID) VALUES (NOW(), %s, %s)", (member_id, employee_id))
    except Exception as e:
        cursor.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

def process_checkouts():
    connection = get_database_connection()
    cursor = connection.cursor()
    try:
        #add all checkout items to the checkout_items table in the DB
        pass

    except Exception as e:
        cursor.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()
    pass

def add_to_checkout(book_id: int = Form(...), checkout_id: int = Form(...)):
    connection = get_database_connection()
    cursor = connection.cursor()
    try:
        #add checkout_item to array of checkout items for the checkout
        pass
    except Exception as e:
        cursor.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

def return_book(book_id: int = Form(...), user_id: int = Form(...)):
    connection = get_database_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("UPDATE CHECKOUTS SET RETURN_DATE = NOW() WHERE MEMBER_ID = %s AND CHECKOUT_ID IN (SELECT CHECKOUT_ID FROM CHECKOUT_ITEMS WHERE COPY_ID = %s AND RETURN_DATE IS NULL)", (user_id, book_id))
    except Exception as e:
        cursor.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()
    pass
#================================================================checkout functions end=================================================

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
