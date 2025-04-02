# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('surveillance.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    encoding BLOB NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    face_id INTEGER,
                    camera_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (face_id) REFERENCES faces(id))''')

    conn.commit()
    conn.close()

def add_face(name, encoding):
    conn = sqlite3.connect('surveillance.db')
    c = conn.cursor()
    c.execute("INSERT INTO faces (name, encoding) VALUES (?, ?)", (name, encoding))
    conn.commit()
    face_id = c.lastrowid
    conn.close()
    return face_id

def log_sighting(face_id, camera_id):
    conn = sqlite3.connect('surveillance.db')
    c = conn.cursor()
    c.execute("INSERT INTO logs (face_id, camera_id) VALUES (?, ?)", (face_id, camera_id))
    conn.commit()
    conn.close()

def get_faces():
    conn = sqlite3.connect('surveillance.db')
    c = conn.cursor()
    c.execute("SELECT * FROM faces")
    faces = c.fetchall()
    conn.close()
    return faces
