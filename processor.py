
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "cards.db"

card_locks = {}
lock_manager = threading.Lock()


def get_card_lock(card_id):
    with lock_manager:
        if card_id not in card_locks:
            card_locks[card_id] = threading.Lock()
        return card_locks[card_id]


def process_transaction(card_id, gate_id, fare=20):

    with get_card_lock(card_id):

        with sqlite3.connect(DB_PATH, timeout=10) as conn:

            conn.execute("BEGIN IMMEDIATE")

            card = conn.execute(
                "SELECT balance FROM cards WHERE card_id = ?",
                (card_id,)
            ).fetchone()

            if card is None:
                conn.rollback()
                return f"{gate_id}: Invalid card!"

            balance = card[0]

            if balance < fare:
                status = "FAILED"
                message = "Insufficient balance"

            else:
                status = "SUCCESS"
                message = "Fare deducted successfully"

                conn.execute(
                    "UPDATE cards SET balance = ? WHERE card_id = ?",
                    (balance - fare, card_id)
                )

            conn.execute(
                """INSERT INTO transactions
                (card_id, gate_id, fare, status, message)
                VALUES (?, ?, ?, ?, ?)""",
                (card_id, gate_id, fare, status, message)
            )

            conn.commit()

            return (
                f"{gate_id} | {card_id} | "
                f"{status} | {message}"
            )


def process_simultaneously(requests):

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(
                lambda request: process_transaction(*request),
                requests
            )
        )

    return results


if __name__ == "__main__":

    requests = [
        ("CARD1001", "GATE01", 20),
        ("CARD1002", "GATE02", 20),
        ("CARD1003", "GATE03", 20),
        ("CARD1004", "GATE04", 20)
    ]

    print("\nPUBLIC TRANSPORT SMART-CARD PROCESSOR")
    print("=" * 55)

    results = process_simultaneously(requests)

    for result in results:
        print(result)

    print("=" * 55)
    print("TRANSACTION PROCESSING COMPLETED")
