
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "cards.db"


def initialize_database():
    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                card_id TEXT PRIMARY KEY,
                passenger_name TEXT NOT NULL,
                balance INTEGER NOT NULL CHECK(balance >= 0)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT,
                gate_id TEXT,
                fare INTEGER,
                status TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards(card_id)
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM cards"
        ).fetchone()[0]

        if count == 0:
            sample_cards = [
                ("CARD1001", "Rahul", 100),
                ("CARD1002", "Priya", 80),
                ("CARD1003", "Arjun", 50),
                ("CARD1004", "Sneha", 15),
                ("CARD1005", "Kiran", 5)
            ]

            conn.executemany(
                "INSERT INTO cards VALUES (?, ?, ?)",
                sample_cards
            )

    print("Database initialized successfully!")


if __name__ == "__main__":
    initialize_database()

    with sqlite3.connect(DB_PATH) as conn:
        cards = conn.execute(
            "SELECT * FROM cards"
        ).fetchall()

        print("\nREGISTERED SMART CARDS:")
        for card in cards:
            print(card)
