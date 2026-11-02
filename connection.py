import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="Hospital_DB"
    )

    cursor = conn.cursor()

    print("================================")
    print(" HOSPITAL MANAGEMENT SYSTEM")
    print("================================")
    print("MySQL Database Connected Successfully!")

except mysql.connector.Error as e:
    print("Database Connection Failed:", e)