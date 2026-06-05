import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="airport_project"
)

if connection.is_connected():
    print("Database Connected!")