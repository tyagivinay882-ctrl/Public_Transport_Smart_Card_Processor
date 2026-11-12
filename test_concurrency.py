
import sqlite3
from pathlib import Path
from processor import process_simultaneously
from database import DB_PATH

DB_PATH = Path(DB_PATH)

# Prepare a test smart card
with sqlite3.connect(DB_PATH) as conn:

    conn.execute(
        "DELETE FROM transactions WHERE card_id = ?",
        ("TESTCARD",)
    )

    conn.execute(
        """INSERT OR REPLACE INTO cards
        (card_id, passenger_name, balance)
        VALUES (?, ?, ?)""",
        ("TESTCARD", "Test Passenger", 30)
    )

print("\nSIMULTANEOUS TRANSACTION TEST")
print("=" * 45)

# Two gates request fare from the same card
requests = [
    ("TESTCARD", "GATE01", 20),
    ("TESTCARD", "GATE02", 20)
]

results = process_simultaneously(requests)

for result in results:
    print(result)

# Check final balance
with sqlite3.connect(DB_PATH) as conn:

    balance = conn.execute(
        "SELECT balance FROM cards WHERE card_id = ?",
        ("TESTCARD",)
    ).fetchone()[0]

print("=" * 45)
print("FINAL BALANCE: Rs.", balance)

print(
    "TEST RESULT:",
    "PASSED" if balance == 10 else "FAILED"
)

print("\nINVALID CARD TEST")
result = process_simultaneously([
    ("INVALID999", "GATE03", 20)
])
print(result[0])
