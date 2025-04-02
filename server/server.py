import cv2
import face_recognition
import numpy as np
import sqlite3
import requests
import datetime
import random
import math
import argparse

LOGGING_SERVER_URL = "http://localhost:3000/log"

# Create SQLite database and tables
def create_db():
    conn = sqlite3.connect('face_recognition.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    encoding BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    camera_id TEXT,
                    timestamp TEXT)''')
    conn.commit()
    conn.close()

# Save face encoding to the database
def save_face(name, encoding):
    conn = sqlite3.connect('face_recognition.db')
    c = conn.cursor()
    c.execute('INSERT INTO faces (name, encoding) VALUES (?, ?)', (name, encoding))
    conn.commit()
    conn.close()

# Check if the face is recognized
def get_face_id(face_encoding):
    conn = sqlite3.connect('face_recognition.db')
    c = conn.cursor()
    c.execute('SELECT id, name, encoding FROM faces')
    rows = c.fetchall()
    conn.close()

    # Convert face_encoding to a numpy array for comparison
    encoding_array = np.frombuffer(face_encoding, np.float64)
    
    for row in rows:
        face_id, name, stored_encoding = row
        stored_encoding_array = np.frombuffer(stored_encoding, np.float64)

        # Use np.linalg.norm to check similarity instead of exact equality
        if np.linalg.norm(encoding_array - stored_encoding_array) < 0.52:  # Adjust the threshold as needed
            return face_id, name
    return None, None

# Log the detected face
def log_face(name, camera_id):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {"name": name, "camera_id": camera_id, "timestamp": timestamp}

    try:
        response = requests.post(LOGGING_SERVER_URL, json=log_entry)
        if response.status_code == 200:
            print("✅ Log sent to server:", log_entry)
        else:
            print("❌ Failed to send log:", response.text)
    except Exception as e:
        print("❌ Error:", e)
        

# Main function for video processing
def process_video(camera_url):
    video_capture = cv2.VideoCapture(camera_url)  # Use IP Camera URL instead of 0

    if not video_capture.isOpened():
        print(f"❌ Failed to connect to {camera_url}")
        return

    known_face_encodings = []
    known_face_names = []

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("⚠️ Failed to receive frame. Exiting...")
            break
        
        rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            face_id, name = get_face_id(face_encoding.tobytes())

            if face_id is None:
                num = math.floor(random.random() * 1000000000000000)
                name = f"Person{num}"
                known_face_encodings.append(face_encoding)
                known_face_names.append(name)
                save_face(name, face_encoding.tobytes())

            log_face(name, camera_url)  # Log the face detection with camera URL

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        cv2.imshow(f'Camera {camera_url}', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    # Initialize video capture

    video_capture = cv2.VideoCapture(camera_id)
    known_face_encodings = []
    known_face_names = []

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        
        rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])  

        face_locations = face_recognition.face_locations(rgb_frame)
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Check if the face is recognized
            face_id, name = get_face_id(face_encoding.tobytes())
            if face_id is None:
                # New face detected, assign a new name
                num = math.floor(random.random()* 1000000000000000)
                name = f"Person{num}"
                known_face_encodings.append(face_encoding)
                known_face_names.append(name)
                save_face(name, face_encoding.tobytes())
            else:
                # If recognized, update name variable
                name = name

            # Log the detection
            log_face(name, camera_url)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow(f'Camera {camera_url}', frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()



# Main script entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face Recognition with OpenCV and SQLite")
    parser.add_argument("camera_source", help="Camera source: 0 for local webcam or an IP camera URL")
    args = parser.parse_args()

    create_db()
    process_video(args.camera_source)
# process_video(0)
# process_video("http://192.168.29.160:5000/video_feed")
