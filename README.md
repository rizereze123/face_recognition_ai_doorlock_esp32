# Hand Gesture Recognition API

Aplikasi ini mendeteksi wajah menggunakan webcam/kamera dan mengirimkan perintah ke ESP32 melalui serial.

## Persyaratan
- Python 3.9.7 (wajib)
- Lihat `requirements.txt` untuk daftar dependensi Python

## Instalasi
1. Pastikan Python 3.9.7 sudah terpasang di sistem Anda.
2. Buat Env Virtual
    ```bash
   python -m venv env
   ```
3. Aktifkan Env Virtual dengan Cara masuk kedalam Powershell VSCode
   ```bash
   cd env/Scripts
   ./Activate.ps1
   ```  
4. Install dependensi dengan perintah:
   
   ```bash
   pip install -r requirements.txt
   pip install dlib-19.22.99-cp39-cp39-win_amd64.whl
   ```

## Penggunaan
1. Sambungkan ESP32 ke komputer dan pastikan port serial sudah benar di `face_recognition_app.py` (ubah variabel `SERIAL_PORT` jika perlu).
2. Jalankan aplikasi:
   
   ```bash
   python face_recognition_app.py
   ```
3. Arahkan wajah ke kamera, wajah akan dideteksi dan perintah dikirim ke ESP32.

## Catatan
- Pastikan port serial sesuai dengan perangkat Anda (misal: `COM8` di Windows).
- Untuk keluar dari aplikasi, tekan tombol `q` pada jendela tampilan.
