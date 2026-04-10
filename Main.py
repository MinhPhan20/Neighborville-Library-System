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

def checkout_book(book_id: int, user_id: int):
    pass

def return_book(book_id: int, user_id: int):
    pass

def search_books(query: str):
    pass

def place_hold(book_id: int, user_id: int):
    pass

