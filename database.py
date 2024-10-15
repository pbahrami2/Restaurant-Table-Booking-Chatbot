import sqlite3

class Database:
    # Initializes the Database class with a database path and sets up the database
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.setup_database()

    
    def setup_database(self):
        #Creates tables in the database if they do not exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY,
                capacity INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                table_id INTEGER,
                date TEXT,
                time TEXT,
                party_size INTEGER,
                FOREIGN KEY(table_id) REFERENCES tables(id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE,
                phone_number TEXT
            )
        ''')
        self.conn.commit()

    def add_table(self, capacity):
        #Adds a new table with the specified capacity to the database
        self.cursor.execute("INSERT INTO tables (capacity) VALUES (?)", (capacity,))
        self.conn.commit()

    def add_user(self, name, email, phone_number):
        #Adds a new user to the database
        self.cursor.execute("INSERT INTO users (name, email, phone_number) VALUES (?, ?, ?)", (name, email, phone_number))
        self.conn.commit()

    def __del__(self):
        self.conn.close()


