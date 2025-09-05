from typing import *
import sqlite3
import random
import string
from datetime import datetime, timedelta


class Handler: ...


class SQLite_Handler(Handler):
    def __init__(self, filepath: str = 'db.sqlite3'):
        self.filepath = filepath

        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT,
                    cipher TEXT,
                    key TEXT,
                    balance INTEGER DEFAULT 0
                );
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    tariff_name TEXT,
                    bought_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (username) REFERENCES users(username)
                );
            ''')
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


    def add_user(self, username: str) -> bool:
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(8, 32)))
        try:
            with sqlite3.connect(self.filepath) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, password)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            pass
        return False

    def buy(self, username: str, tariff_name: str, duration_days: int, price: int) -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()

            if row is None: # user not exists
                return False
            balance = row[0]
            if balance < price: # not enough money
                return False

            cursor.execute('''
                        SELECT MAX(expires_at) FROM buys
                        WHERE username = ? AND tariff_name = ?
                    ''', (username, tariff_name))
            last_expiry_row = cursor.fetchone()
            last_expiry = last_expiry_row[0] if last_expiry_row and last_expiry_row[0] else None

            now = datetime.now()
            if last_expiry:
                last_expiry_dt = datetime.fromisoformat(last_expiry)
                start_time = max(now, last_expiry_dt)
            else:
                start_time = now
            new_expiry = start_time + timedelta(days=duration_days)

            cursor.execute("UPDATE users SET balance = ? WHERE username = ?", (balance - price, username))

            cursor.execute(
                """
                INSERT INTO buys (username, tariff_name, expires_at)
                VALUES (?, ?, ?)
                """,
                (username, tariff_name, new_expiry.isoformat())
            )

            conn.commit()
            return True

    def pay(self, username: str, amount: int) -> bool:
        if amount <= 0:
            return False
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row is None:
                return False
            new_balance = row[0] + amount
            cursor.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, username))
            conn.commit()
            return True

    def is_subscriber(self, username: str) -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM buys
                WHERE username = ?
                  AND expires_at > CURRENT_TIMESTAMP
                LIMIT 1
            ''', (username,))
            result = cursor.fetchone()
            return result is not None


    def save_key(self, username: str, key: str) -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET key = ? WHERE username = ?', (key, username))
            conn.commit()
        return True

    def save_cipher(self, username: str, cipher: str) -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET cipher = ? WHERE username = ?', (cipher, username))
            conn.commit()
        return True

    def save_password(self, username: str, password: str) -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password = ? WHERE username = ?', (password, username))
            conn.commit()
        return True


    def find_key(self, username: str) -> str:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            return result[0] if result else ''

    def find_cipher(self, username: str) -> str:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT cipher FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            return result[0] if result else ''

    def find_password(self, username: str) -> str:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            return result[0] if result else ''


    def get_user_balance(self, username: str) -> int:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT balance FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_access_expiry(self, username: str) -> Optional[datetime]:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(expires_at) FROM buys
                WHERE username = ? AND expires_at > CURRENT_TIMESTAMP
            ''', (username,))
            result = cursor.fetchone()
            if result and result[0]:
                return datetime.fromisoformat(result[0])
            return None

    def tarif_was(self, username: str, tarif_name: str = "free_3_days") -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT bought_at FROM buys
                WHERE username = ? AND tariff_name = ?
                ORDER BY bought_at ASC
                LIMIT 1
            ''', (username, tarif_name))
            result = cursor.fetchone()
            if result is None:
                return True

            first_buy_date = datetime.fromisoformat(result[0])
            now = datetime.now()
            return (now - first_buy_date).days < 3


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

            self.pay(username, amount)

            cursor.execute("DELETE FROM pending_payments WHERE id = ?", (payment_id,))
            conn.commit()
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

    def delete_user(self, username: str) -> bool:
        with sqlite3.connect(self.filepath) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM buys WHERE username = ?", (username,))
            cursor.execute("DELETE FROM pending_payments WHERE username = ?", (username,))
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted