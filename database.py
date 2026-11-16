
import os
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": os.getenv("BANK_DB_PASSWORD", ""),
    "database": "banking_system"
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def create_tables():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                phone VARCHAR(15) NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                account_number VARCHAR(20) UNIQUE NOT NULL,
                balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                account_type VARCHAR(30) DEFAULT 'Savings',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS beneficiaries (
                beneficiary_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                beneficiary_account VARCHAR(20) NOT NULL,
                nickname VARCHAR(60),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE KEY unique_beneficiary
                (user_id, beneficiary_account)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                reference_number VARCHAR(40) UNIQUE NOT NULL,
                sender_account VARCHAR(20) NOT NULL,
                receiver_account VARCHAR(20) NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                transaction_type VARCHAR(30) DEFAULT 'Transfer',
                description VARCHAR(255),
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'SUCCESS'
            )
        """)

        connection.commit()

        print("\n====================================")
        print("BANKING DATABASE READY")
        print("====================================")
        print("1. Users table")
        print("2. Accounts table")
        print("3. Beneficiaries table")
        print("4. Transactions table")

    except Error as error:
        if connection:
            connection.rollback()
        print("Database Error:", error)
        raise

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    create_tables()
