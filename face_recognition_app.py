import face_recognition
import cv2
import numpy as np
import os
import mysql.connector
from datetime import datetime
import serial
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
import uuid

# --- Konfigurasi ---
SERIAL_PORT = "COM5"
BAUD_RATE = 115200
WINDOW_SIZE = "650x400"
KNOWN_FACES_DIR = "known_faces"

# --- Koneksi Serial ke ESP32 ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Tunggu ESP32 siap
    print(f"Connected to ESP32 on {SERIAL_PORT}")
except Exception as e:
    print(f"Failed to connect to ESP32: {e}")
    ser = None

def send_command(command):
    if not ser:
        return
    try:
        ser.write((command + '\n').encode())
        time.sleep(0.1)
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"Sent: {command}, Response: {response}")
    except Exception as e:
        print(f"Failed to send command: {e}")

# Pastikan folder log_capture ada
LOG_CAPTURE_DIR = "log_capture"
os.makedirs(LOG_CAPTURE_DIR, exist_ok=True)

def save_capture(frame):
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(LOG_CAPTURE_DIR, filename)
    cv2.imwrite(filepath, frame)
    return filename

# --- Fungsi cek PIN ---
def verify_pin():
    pin_input = simpledialog.askstring("Verifikasi PIN", "Masukkan PIN Anda:", show="*")
    if not pin_input:
        return None

    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="smartdoorlock"
        )
        cursor = db.cursor()
        cursor.execute("SELECT image_path FROM users WHERE pin = %s", (pin_input,))
        result = cursor.fetchone()
        cursor.close()
        db.close()

        if result:
            user_name = os.path.splitext(result[0])[0]
            return user_name
        else:
            messagebox.showerror("Error", "PIN salah!")
            return None
    except Exception as e:
        messagebox.showerror("Error", f"Gagal verifikasi PIN: {e}")
        return None

# --- Fungsi Face Recognition ---
def face_recognition_step(verified_user):
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith((".jpg", ".png")):
            image_path = os.path.join(KNOWN_FACES_DIR, filename)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_face_encodings.append(encodings[0])
                known_face_names.append(os.path.splitext(filename)[0])

    cv2.namedWindow("Face Recognition", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Face Recognition", 650, 600)

    video_capture = cv2.VideoCapture(0)
    process_this_frame = True
    sent_names = set()
    start_time = time.time()

    while True:
        ret, frame = video_capture.read()
        if not ret:
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
                    if name == verified_user:
                        send_command("Success")
                        if name not in sent_names:
                            try:
                                capture_filename = save_capture(frame)  # Simpan gambar
                                db = mysql.connector.connect(
                                    host="localhost",
                                    user="root",
                                    password="",
                                    database="smartdoorlock"
                                )
                                cursor = db.cursor()
                                cursor.execute("INSERT INTO logs (name, log_capture) VALUES (%s, %s)",(name, capture_filename))
                                db.commit()
                                cursor.close()
                                db.close()
                                sent_names.add(name)
                                messagebox.showinfo("Success", f"Akses diterima: {name}")
                            except Exception as e:
                                messagebox.showerror("Error", f"Gagal simpan log: {e}")
                        video_capture.release()
                        cv2.destroyAllWindows()
                        return
                    else:
                        send_command("Error")
                        try:
                            capture_filename = save_capture(frame)  # Simpan gambar
                            db = mysql.connector.connect(
                                host="localhost",
                                user="root",
                                password="",
                                database="smartdoorlock"
                            )
                            cursor = db.cursor()
                            cursor.execute(
                                "INSERT INTO logs (name, log_capture) VALUES (%s, %s)",
                                ("Unknown, Wajah Cocok Tapi PIN Salah - Mencoba Akses", capture_filename)
                            )
                            db.commit()
                            cursor.close()
                            db.close()
                        except Exception as e:
                            messagebox.showerror("Error", f"Gagal simpan log: {e}")
                        messagebox.showerror("Error", "Wajah cocok tapi tidak sesuai PIN!")
                        video_capture.release()
                        cv2.destroyAllWindows()
                        return
                else:
                    send_command("Error")
                    try:
                        capture_filename = save_capture(frame)
                        db = mysql.connector.connect(
                            host="localhost",
                            user="root",
                            password="",
                            database="smartdoorlock"
                        )
                        cursor = db.cursor()
                        cursor.execute(
                            "INSERT INTO logs (name, log_capture) VALUES (%s, %s)",
                            ("Unknown, Wajah Tidak Dikenal - Mencoba Akses", capture_filename)
                        )
                        db.commit()
                        cursor.close()
                        db.close()
                    except Exception as e:
                        messagebox.showerror("Error", f"Gagal simpan log: {e}")
                    messagebox.showerror("Error", "Wajah Tidak Dikenal!")
                    video_capture.release()
                    cv2.destroyAllWindows()

                face_names.append(name)

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            color = (255, 0, 0) if name != "Unknown" else (0, 0, 255)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

        cv2.imshow("Face Recognition", frame)

        process_this_frame = not process_this_frame
        

        if (time.time() - start_time) > 10:  # timeout 10 detik
            messagebox.showerror("Error", "Waktu habis untuk scan wajah!")
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

# --- Fungsi titik awal ---
def start_verification():
    user = verify_pin()
    if user:
        face_recognition_step(user)

# --- GUI Utama ---
root = tk.Tk()
root.title("Smart Doorlock")
root.geometry(WINDOW_SIZE)

label = tk.Label(root, text="Mulai Verifikasi Smart Doorlock", font=("Arial", 14))
label.pack(pady=20)

btn_mulai = tk.Button(root, text="Mulai", font=("Arial", 12), command=start_verification)
btn_mulai.pack(pady=20)

root.mainloop()
