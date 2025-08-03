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

# ESP32 Configuration
# esp32_ip = '10.102.200.231'
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

                # # Simpan log hanya sekali per orang selama sesi
                # if name not in sent_names:
                #     try:
                #         db = mysql.connector.connect(
                #             host="localhost",
                #             user="root",
                #             password="",
                #             database="smartdoorlock"
                #         )
                #         cursor = db.cursor()
                #         cursor.execute("INSERT INTO logs (name) VALUES (%s)", (name,))
                #         db.commit()
                #         cursor.close()
                #         db.close()
                #         print(f"[INFO] Log tersimpan untuk {name}")
                #         sent_names.add(name)  # Tambahkan ke set agar tidak diulang
                #     except Exception as e:
                #         print(f"[ERROR] Gagal simpan ke database: {e}")

                # Send to ESP32 if not already sent
                # if name not in sent_names:
                #     try:
                #         url = f"http://{esp32_ip}/unlock?name={name}"
                #         response = requests.get(url, timeout=2)
                #         if response.status_code == 200:
                #             print(f"[INFO] Sent to ESP32: {name}")
                #             sent_names.add(name)
                #         else:
                #             print(f"[ERROR] Failed to send to ESP32. Status code: {response.status_code}")
                #     except requests.exceptions.RequestException as e:
                #         print(f"[ERROR] ESP32 request failed: {e}")
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


# import face_recognition
# import cv2
# import numpy as np
# import os


# # Load known faces from the known_faces directory
# known_face_encodings = []
# known_face_names = []
# known_faces_dir = 'known_faces'

# for filename in os.listdir(known_faces_dir):
#     if filename.endswith(".jpg") or filename.endswith(".png"):
#         # Load an image file
#         image_path = os.path.join(known_faces_dir, filename)
#         image = face_recognition.load_image_file(image_path)
#         # Encode the face
#         face_encoding = face_recognition.face_encodings(image)[0]
#         # Add encoding and name to lists
#         known_face_encodings.append(face_encoding)
#         known_face_names.append(os.path.splitext(filename)[0])

# # Initialize some variables
# face_locations = []
# face_encodings = []
# face_names = []
# process_this_frame = True

# # Open the webcam
# video_capture = cv2.VideoCapture(0)

# while True:
#     # Grab a single frame of video
#     ret, frame = video_capture.read()

#     # Resize frame of video to 1/4 size for faster face recognition processing
#     small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

#     # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
#     rgb_small_frame = small_frame[:, :, ::-1]

#     # Only process every other frame of video to save time
#     if process_this_frame:
#         # Find all the faces and face encodings in the current frame of video
#         face_locations = face_recognition.face_locations(rgb_small_frame)
#         face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

#         face_names = []
#         for face_encoding in face_encodings:
#             # See if the face is a match for the known face(s)
#             matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
#             name = "Unknown"

#             # Use the known face with the smallest distance to the new face
#             face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
#             best_match_index = np.argmin(face_distances)
#             if matches[best_match_index]:
#                 name = known_face_names[best_match_index]


#             face_names.append(name)

#     process_this_frame = not process_this_frame

#     # Display the results
#     for (top, right, bottom, left), name in zip(face_locations, face_names):
#         # Scale back up face locations since the frame we detected in was scaled to 1/4 size
#         top *= 4
#         right *= 4
#         bottom *= 4
#         left *= 4

#         # Set the color for the rectangle and label
#         if name == "Unknown":
#             color = (0, 0, 255)  # Red for unknown faces
#         else:
#             color = (255, 0, 0)  # Blue for known faces

#         # Draw a box around the face
#         cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

#         # Draw a label with a name below the face
#         cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
#         font = cv2.FONT_HERSHEY_DUPLEX
#         cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

#     # Display the resulting image
#     cv2.imshow('Video', frame)

#     # Hit 'q' on the keyboard to quit!
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Release handle to the webcam
# video_capture.release()
# cv2.destroyAllWindows()


# from flask import Flask, request, jsonify
# import face_recognition
# import numpy as np
# import base64
# from PIL import Image
# import io
# import os

# app = Flask(__name__)

# known_face_encodings = []
# known_face_names = []

# # Load known faces
# known_faces_dir = "known_faces"
# for filename in os.listdir(known_faces_dir):
#     if filename.endswith(".jpg") or filename.endswith(".png"):
#         image = face_recognition.load_image_file(os.path.join(known_faces_dir, filename))
#         encoding = face_recognition.face_encodings(image)[0]
#         known_face_encodings.append(encoding)
#         known_face_names.append(os.path.splitext(filename)[0])

# @app.route('/recognize', methods=['POST'])
# def recognize():
#     data = request.json
#     image_data = base64.b64decode(data['image'])
#     image = Image.open(io.BytesIO(image_data))
#     image_np = np.array(image)
    
#     face_locations = face_recognition.face_locations(image_np)
#     face_encodings = face_recognition.face_encodings(image_np, face_locations)
    
#     for face_encoding in face_encodings:
#         matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
#         if True in matches:
#             first_match_index = matches.index(True)
#             name = known_face_names[first_match_index]
#             return jsonify({"status": "success", "name": name})
    
#     return jsonify({"status": "failed", "message": "Face not recognized"})

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5000)
