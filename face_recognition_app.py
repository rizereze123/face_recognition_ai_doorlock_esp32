import face_recognition
import cv2
import numpy as np
import os
import requests
import mysql.connector
from datetime import datetime
import serial
import time


SERIAL_PORT = "COM9"
BAUD_RATE = 115200

# Initialize serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for ESP32 to initialize
    print(f"Connected to ESP32 on {SERIAL_PORT}")
except Exception as e:
    print(f"Failed to connect to ESP32: {e}")
    exit()


# Function to send commands to ESP32 via serial
def send_command(command):
    try:
        ser.write((command + '\n').encode())
        time.sleep(0.1)  # Small delay to ensure command is sent
        
        # Read response from ESP32
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"Sent: {command}, Response: {response}")
            return response
    except Exception as e:
        print(f"Failed to send command: {command}, Error: {e}")
        return None



# Load known faces from the known_faces directory
known_face_encodings = []
known_face_names = []
known_faces_dir = 'known_faces'

for filename in os.listdir(known_faces_dir):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        image_path = os.path.join(known_faces_dir, filename)
        image = face_recognition.load_image_file(image_path)
        face_encoding = face_recognition.face_encodings(image)[0]
        known_face_encodings.append(face_encoding)
        known_face_names.append(os.path.splitext(filename)[0])

sent_names = set()  # to prevent sending the same name repeatedly

# Initialize webcam
video_capture = cv2.VideoCapture(0)

process_this_frame = True
face_locations = []
face_encodings = []
face_names = []

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Failed to grab frame.")
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]

    if process_this_frame:
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                name = known_face_names[best_match_index]

                send_command("Success")

                # Simpan log hanya sekali per orang selama sesi
                try:
                    db = mysql.connector.connect(
                        host="localhost",
                        user="root",
                        password="",
                        database="smartdoorlock"
                    )
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO logs (name) VALUES (%s)", (name,))
                    db.commit()
                    cursor.close()
                    db.close()
                    print(f"[INFO] Log tersimpan untuk {name}")
                    sent_names.add(name)  # Tambahkan ke set agar tidak diulang
                except Exception as e:
                    print(f"[ERROR] Gagal simpan ke database: {e}")
            else:
                send_command("Error")
                
            face_names.append(name)

    process_this_frame = not process_this_frame

    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4; right *= 4; bottom *= 4; left *= 4
        color = (255, 0, 0) if name != "Unknown" else (0, 0, 255)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6),
                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

    cv2.imshow('Face Recognition', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
video_capture.release()
cv2.destroyAllWindows()
