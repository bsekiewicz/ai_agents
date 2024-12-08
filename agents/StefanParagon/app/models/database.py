import os
import sqlite3

DATABASE_FOLDER = 'app/db'
DATABASE_FILE = os.path.join(DATABASE_FOLDER, 'receipts.db')


def get_db_connection():
    os.makedirs(DATABASE_FOLDER, exist_ok=True)
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates tables in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            state_or_region TEXT,
            street TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            tax_id TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            general_category TEXT,
            sub_category TEXT,
            product_type TEXT,
            unit_of_measure TEXT DEFAULT 'pcs'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            receipt_number TEXT NOT NULL UNIQUE,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            currency TEXT DEFAULT 'PLN',
            total_amount REAL NOT NULL,
            total_discount REAL DEFAULT 0,
            FOREIGN KEY (store_id) REFERENCES stores (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receipt_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            promotional BOOLEAN DEFAULT FALSE,
            quantity REAL NOT NULL,
            unit_price REAL,
            total_price REAL NOT NULL,
            discount REAL DEFAULT 0,
            total_price_with_discount REAL NOT NULL,
            FOREIGN KEY (receipt_id) REFERENCES receipts (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            upload_timestamp TEXT NOT NULL,
            receipt_id INTEGER,
            FOREIGN KEY (receipt_id) REFERENCES receipts (id)
        )
    ''')
    conn.commit()
    conn.close()


def save_receipt_to_db(receipt):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Save store if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO stores (
                name, city, state_or_region, street, postal_code, tax_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            receipt.store.name,
            receipt.store.get_purchase_address().city,
            receipt.store.get_purchase_address().state_or_region,
            receipt.store.get_purchase_address().street,
            receipt.store.get_purchase_address().postal_code,
            receipt.store.tax_id
        ))
        store_id = cursor.lastrowid or \
            cursor.execute('SELECT id FROM stores WHERE tax_id = ?', (receipt.store.tax_id,)).fetchone()[0]

        # Save receipt
        cursor.execute('''
            INSERT INTO receipts (
                store_id, receipt_number, date, time, payment_method, currency, total_amount, total_discount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            store_id,
            receipt.receipt_number,
            receipt.date,
            receipt.time,
            receipt.payment_method,
            receipt.currency,
            receipt.total_amount,
            receipt.total_discount
        ))
        receipt_id = cursor.lastrowid

        # Save products and receipt items
        for product in receipt.products:
            cursor.execute('''
                INSERT INTO products (
                    name, general_category, sub_category, product_type, unit_of_measure
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                product.name,
                product.category.general_category,
                product.category.sub_category,
                product.category.product_type,
                product.unit_of_measure
            ))
            product_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO receipt_items (
                    receipt_id, product_id, promotional, quantity, unit_price, total_price, discount, 
                    total_price_with_discount 
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                receipt_id,
                product_id,
                product.promotional,
                product.quantity,
                product.unit_price,
                product.total_price,
                product.discount,
                product.total_price_with_discount
            ))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return receipt_id
