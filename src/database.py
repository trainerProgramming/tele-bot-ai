import sqlite3

# Nama file database (akan dibuat otomatis)
DB_NAME = "umkm.db"

def init_db():
    """Membuat tabel jika belum ada"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabel Inventaris (Produk Digital)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_produk TEXT UNIQUE,
            stok INTEGER DEFAULT 0,
            harga INTEGER DEFAULT 0
        )
    ''')

    # 2. Tabel Info Toko (FAQ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS info (
            kunci TEXT PRIMARY KEY,
            isi TEXT
        )
    ''')

    # Isi data awal (Default Data)
    try:
        cursor.execute("INSERT INTO info VALUES ('jam_kerja', '09:00 - 21:00 WIB')")
        cursor.execute("INSERT INTO info VALUES ('kontak', 'Email: support@digieco.id')")
        cursor.execute("INSERT INTO produk (nama_produk, stok, harga) VALUES ('Ebook Python', 50, 50000)")
        cursor.execute("INSERT INTO produk (nama_produk, stok, harga) VALUES ('Template UI Kit', 20, 150000)")
    except sqlite3.IntegrityError:
        pass # Data sudah ada, abaikan error

    conn.commit()
    conn.close()

def query_db(query, params=(), fetch=False):
    """Fungsi pembantu untuk menjalankan perintah SQL"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    if fetch:
        result = cursor.fetchall()
    else:
        result = None
        conn.commit()
        
    conn.close()
    return result