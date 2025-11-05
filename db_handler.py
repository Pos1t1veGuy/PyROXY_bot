from typing import *
import sqlite3
import random
import string
from datetime import datetime, timedelta

from ..db_handlers import SQLite_Handler as default_sqlite_handler


class SQLite_Handler(default_sqlite_handler):
    def __init__(self, filepath: str = 'db.sqlite3'):
        super().__init__(filepath=filepath)
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    details TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            conn.commit()

    def list_pending_payments(self) -> list:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pending_payments")
            return cursor.fetchall()

    def confirm_payment(self, payment_id: int, amount: int) -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT username FROM pending_payments WHERE id = ?", (payment_id,))
            row = cursor.fetchone()
            if not row:
                return False
            username = row[0]

            if self.pay(username, amount):
                cursor.execute("DELETE FROM pending_payments WHERE id = ?", (payment_id,))
                conn.commit()
            else:
                return False

        return True

    def reject_payment(self, payment_id: int) -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM pending_payments WHERE id = ?", (payment_id,))
            if not cursor.fetchone():
                return False

            cursor.execute("DELETE FROM pending_payments WHERE id = ?", (payment_id,))
            conn.commit()

        return True


    def add_pending_payment(self, username: str, user_id: int, details: str,
                            do_after: Optional[Callable[[str, int, str], None]] = None) -> int:

        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO pending_payments (username, details, user_id)
                VALUES (?, ?, ?)
                """,
                (username, details, user_id)
            )
            payment_id = cursor.lastrowid
            conn.commit()

        if do_after:
            do_after(username, user_id, details)

        return payment_id

    def delete_user(self, username: str) -> bool:
        super().delete_user(username)
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pending_payments WHERE username = ?", (username,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted