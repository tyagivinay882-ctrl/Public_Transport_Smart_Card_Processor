
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import threading
from pathlib import Path

from database import initialize_database, DB_PATH
from processor import process_transaction

root = tk.Tk()
root.title("Metro Smart Card Processor")
root.geometry("1150x780")
root.minsize(950, 680)
root.configure(bg="#101827")

BG = "#101827"
PANEL = "#1c293b"
ACCENT = "#2563eb"
WHITE = "#f1f5f9"
MUTED = "#94a3b8"
GREEN = "#22c55e"
RED = "#ef4444"

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background=PANEL,
    foreground=WHITE,
    fieldbackground=PANEL,
    rowheight=30
)

style.configure(
    "Treeview.Heading",
    background="#26364c",
    foreground=WHITE,
    font=("Arial", 10, "bold")
)

style.map(
    "Treeview",
    background=[("selected", ACCENT)]
)

initialize_database()

def get_connection():
    return sqlite3.connect(DB_PATH)


def get_cards():
    with get_connection() as conn:
        return conn.execute(
            "SELECT card_id, passenger_name, balance FROM cards"
        ).fetchall()


def get_transactions():
    with get_connection() as conn:
        return conn.execute(
            """SELECT card_id, gate_id, fare, status, timestamp
               FROM transactions
               ORDER BY transaction_id DESC LIMIT 100"""
        ).fetchall()


def create_stat(parent, title, color):
    box = tk.Frame(parent, bg=PANEL, padx=18, pady=14)
    box.pack(side="left", fill="both", expand=True, padx=6)

    tk.Label(
        box, text=title, bg=PANEL, fg=MUTED,
        font=("Arial", 10)
    ).pack(anchor="w")

    value = tk.Label(
        box, text="0", bg=PANEL, fg=color,
        font=("Arial", 23, "bold")
    )
    value.pack(anchor="w", pady=(8, 0))

    return value


def update_dashboard():
    cards = get_cards()
    transactions = get_transactions()

    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        successful = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE status='SUCCESS'"
        ).fetchone()[0]

        failed = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE status='FAILED'"
        ).fetchone()[0]

    total_value.config(text=str(total))
    success_value.config(text=str(successful))
    failed_value.config(text=str(failed))
    card_value.config(text=str(len(cards)))

    for item in card_table.get_children():
        card_table.delete(item)

    for card in cards:
        card_table.insert(
            "", "end",
            values=(card[0], card[1], f"Rs. {card[2]}")
        )

    for item in transaction_table.get_children():
        transaction_table.delete(item)

    for transaction in transactions:
        transaction_table.insert(
            "", "end",
            values=transaction
        )

    for gate in gates:
        gate["combo"]["values"] = [
            card[0] for card in cards
        ]


def show_result(result, gate, button):
    button.config(state="normal")
    status_label.config(
        text=result,
        fg=GREEN if "SUCCESS" in result else RED
    )
    update_dashboard()


def tap_card(gate, combo, fare_entry, button):

    card_id = combo.get()

    try:
        fare = int(fare_entry.get())
        if fare <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror(
            "Invalid Fare",
            "Please enter a positive whole-number fare."
        )
        return

    if not card_id:
        messagebox.showwarning(
            "No Card Selected",
            "Please select a smart card."
        )
        return

    button.config(state="disabled")
    status_label.config(
        text=f"{gate}: Processing transaction...",
        fg="#facc15"
    )

    def worker():
        try:
            result = process_transaction(card_id, gate, fare)
        except Exception as error:
            result = f"FAILED: {error}"

        root.after(
            0, lambda: show_result(result, gate, button)
        )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


def simulate_all():

    for gate in gates:
        tap_card(
            gate["name"],
            gate["combo"],
            gate["fare"],
            gate["button"]
        )


def register_card():

    root.lift()
    root.focus_force()

    
    card_id = simpledialog.askstring(
    "Register Card",
    "Enter new card ID:",
    parent=root
    )

    if not card_id:
        return

    name = simpledialog.askstring(
    "Register Card",
    "Enter passenger name:",
    parent=root
)

    if not name:
        return

    balance = simpledialog.askinteger(
    "Register Card",
    "Enter initial balance:",
    parent = root

    )

    if balance is None:
        return

    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO cards
                (card_id, passenger_name, balance)
                VALUES (?, ?, ?)""",
                (card_id.strip().upper(), name.strip(), balance)
            )

        update_dashboard()
        messagebox.showinfo(
            "Success", "Smart card registered successfully!"
        )

    except sqlite3.IntegrityError:
        messagebox.showerror(
            "Error", "This card ID already exists."
        )


def recharge_card():

    card_id = simpledialog.askstring(
        "Recharge Card", "Enter card ID:"
    )

    if not card_id:
        return

    amount = simpledialog.askinteger(
        "Recharge", "Enter recharge amount:",
        minvalue=1
    )

    if amount is None:
        return

    with get_connection() as conn:

        cursor = conn.execute(
            """UPDATE cards
            SET balance = balance + ?
            WHERE card_id = ?""",
            (amount, card_id.strip().upper())
        )

        if cursor.rowcount == 0:
            messagebox.showerror(
                "Error", "Smart card not found."
            )
            return

    update_dashboard()

    messagebox.showinfo(
        "Recharge Successful",
        f"Rs. {amount} added to {card_id.upper()}."
    )


def reset_demo_data():

    confirm = messagebox.askyesno(
        "Reset Demo",
        "This will remove custom cards and transaction history "
        "and restore the original five sample cards. Continue?"
    )

    if not confirm:
        return

    sample_cards = [
        ("CARD1001", "Rahul", 100),
        ("CARD1002", "Priya", 80),
        ("CARD1003", "Arjun", 50),
        ("CARD1004", "Sneha", 15),
        ("CARD1005", "Kiran", 5)
    ]

    with get_connection() as conn:

        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM cards")

        conn.executemany(
            "INSERT INTO cards VALUES (?, ?, ?)",
            sample_cards
        )

    update_dashboard()

    status_label.config(
        text="SYSTEM RESET SUCCESSFUL",
        fg=GREEN
    )

    messagebox.showinfo(
        "Reset Complete",
        "Original sample cards and balances restored."
    )

header = tk.Frame(root, bg=BG, padx=25, pady=20)
header.pack(fill="x")

tk.Label(
    header,
    text="METRO SMART CARD PROCESSOR",
    bg=BG,
    fg=WHITE,
    font=("Arial", 21, "bold")
).pack(anchor="w")

tk.Label(
    header,
    text="PUBLIC TRANSPORT | AUTOMATED FARE COLLECTION SYSTEM",
    bg=BG,
    fg=MUTED,
    font=("Arial", 9)
).pack(anchor="w", pady=5)


toolbar = tk.Frame(root, bg=BG, padx=25)
toolbar.pack(fill="x", pady=5)

tk.Button(
    toolbar,
    text="+ REGISTER NEW CARD",
    bg=ACCENT,
    fg="white",
    relief="flat",
    padx=12,
    pady=8,
    command=register_card
).pack(side="left", padx=5)

tk.Button(
    toolbar,
    text="RECHARGE CARD",
    bg="#0f766e",
    fg="white",
    relief="flat",
    padx=12,
    pady=8,
    command=recharge_card
).pack(side="left", padx=5)

tk.Button(
    toolbar,
    text="RESET DEMO DATA",
    bg="#b45309",
    fg="white",
    relief="flat",
    padx=12,
    pady=8,
    command=reset_demo_data
).pack(side="right", padx=5)

stats = tk.Frame(root, bg=BG, padx=18, pady=8)
stats.pack(fill="x")

total_value = create_stat(stats, "TOTAL TRANSACTIONS", WHITE)
success_value = create_stat(stats, "SUCCESSFUL", GREEN)
failed_value = create_stat(stats, "FAILED", RED)
card_value = create_stat(stats, "REGISTERED CARDS", "#60a5fa")


gate_section = tk.Frame(root, bg=BG, padx=20, pady=12)
gate_section.pack(fill="x")

tk.Label(
    gate_section,
    text="VIRTUAL TICKET GATES",
    bg=BG,
    fg=WHITE,
    font=("Arial", 14, "bold")
).pack(anchor="w", pady=(0, 12))

gate_container = tk.Frame(gate_section, bg=BG)
gate_container.pack(fill="x")

gates = []

for i in range(4):

    gate_name = f"GATE0{i + 1}"

    frame = tk.Frame(
        gate_container,
        bg=PANEL,
        padx=12,
        pady=14
    )

    frame.grid(
        row=0,
        column=i,
        padx=6,
        sticky="nsew"
    )

    gate_container.grid_columnconfigure(i, weight=1)

    tk.Label(
        frame,
        text=f"🚇 {gate_name}",
        bg=PANEL,
        fg=WHITE,
        font=("Arial", 12, "bold")
    ).pack(pady=5)

    tk.Label(
        frame,
        text="Select Smart Card",
        bg=PANEL,
        fg=MUTED
    ).pack(pady=4)

    combo = ttk.Combobox(
        frame,
        state="readonly",
        width=16
    )
    combo.pack(pady=5)

    fare = tk.Entry(
        frame,
        width=15,
        justify="center",
        font=("Arial", 10)
    )
    fare.insert(0, "20")
    fare.pack(pady=7)

    button = tk.Button(
        frame,
        text="TAP CARD",
        bg=ACCENT,
        fg="white",
        activebackground="#1d4ed8",
        activeforeground="white",
        font=("Arial", 10, "bold"),
        relief="flat",
        padx=12,
        pady=7,
        command=lambda g=gate_name, c=combo, f=fare, b=None:
            tap_card(g, c, f, b)
    )

    button.pack(pady=7)

    gates.append({
        "name": gate_name,
        "combo": combo,
        "fare": fare,
        "button": button
    })

    button.config(
        command=lambda g=gate_name, c=combo, f=fare, b=button:
            tap_card(g, c, f, b)
    )


simulate_button = tk.Button(
    gate_section,
    text="SIMULATE ALL FOUR GATES",
    bg=GREEN,
    fg="white",
    font=("Arial", 10, "bold"),
    relief="flat",
    padx=15,
    pady=9,
    command=simulate_all
)
simulate_button.pack(pady=12)


status_frame = tk.Frame(root, bg=PANEL, padx=15, pady=10)
status_frame.pack(fill="x", padx=25, pady=5)

tk.Label(
    status_frame,
    text="PROCESSOR STATUS:",
    bg=PANEL,
    fg=WHITE,
    font=("Arial", 10, "bold")
).pack(side="left")

status_label = tk.Label(
    status_frame,
    text="SYSTEM READY",
    bg=PANEL,
    fg=GREEN,
    font=("Arial", 10, "bold")
)
status_label.pack(side="left", padx=12)


content = tk.Frame(root, bg=BG, padx=20, pady=12)
content.pack(fill="both", expand=True)

left = tk.Frame(content, bg=BG)
left.pack(side="left", fill="both", expand=True, padx=5)

right = tk.Frame(content, bg=BG)
right.pack(side="left", fill="both", expand=True, padx=5)

tk.Label(
    left,
    text="SMART CARD DATABASE",
    bg=BG,
    fg=WHITE,
    font=("Arial", 12, "bold")
).pack(anchor="w", pady=8)

card_table = ttk.Treeview(
    left,
    columns=("ID", "Name", "Balance"),
    show="headings",
    height=8
)

for column in ("ID", "Name", "Balance"):
    card_table.heading(column, text=column)
    card_table.column(column, width=110)

card_table.pack(fill="both", expand=True)


tk.Label(
    right,
    text="TRANSACTION HISTORY",
    bg=BG,
    fg=WHITE,
    font=("Arial", 12, "bold")
).pack(anchor="w", pady=8)

transaction_table = ttk.Treeview(
    right,
    columns=("Card", "Gate", "Fare", "Status", "Time"),
    show="headings",
    height=8
)

for column in ("Card", "Gate", "Fare", "Status", "Time"):
    transaction_table.heading(column, text=column)
    transaction_table.column(column, width=95)

transaction_table.pack(fill="both", expand=True)


footer = tk.Label(
    root,
    text="PUBLIC TRANSPORT SMART-CARD PROCESSOR | COA MINI PROJECT",
    bg=BG,
    fg=MUTED,
    font=("Arial", 8)
)
footer.pack(pady=10)

update_dashboard()

root.mainloop()
