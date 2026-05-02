import sqlite3

connection = sqlite3.connect("warehouse.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    row INTEGER NOT NULL,
    col INTEGER NOT NULL,
    weight REAL NOT NULL
)
""")

cursor.execute("DELETE FROM products")

products = [
    ("C1", "Carpet A", 2, 4, 20),
    ("C2", "Carpet B", 2, 6, 12),
    ("C3", "Carpet C", 5, 6, 28),
    ("C4", "Carpet D", 5, 2, 16),
]

cursor.executemany(
    "INSERT INTO products (id, name, row, col, weight) VALUES (?, ?, ?, ?, ?)",
    products
)

connection.commit()
connection.close()

print("Database initialized successfully: warehouse.db")