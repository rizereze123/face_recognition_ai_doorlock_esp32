# from flask import Flask, render_template, request, redirect, url_for
# import os
# import mysql.connector

# app = Flask(__name__)

# # Konfigurasi folder upload
# UPLOAD_FOLDER = '../known_faces'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# # Koneksi ke database
# db = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="",  # ganti jika password MySQL kamu ada
#     database="smartdoorlock"
# )

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/register', methods=['POST'])
# def register():
#     image = request.files['image']

#     if image:
#         image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
#         image.save(image_path)

#         cursor = db.cursor()
#         cursor.execute("INSERT INTO users (image_path) VALUES (%s)",
#                        (image.filename))
#         db.commit()

#         return redirect('/')
#     else:
#         return "Form tidak lengkap!"

# @app.route('/logs')
# def logs():
#     cursor = db.cursor()
#     cursor.execute("SELECT * FROM logs ORDER BY access_time DESC")
#     log_data = cursor.fetchall()
#     return render_template('logs.html', logs=log_data)

# if __name__ == '__main__':
#     app.run(debug=True)


# from flask import Flask, render_template, request, redirect
# import os
# import mysql.connector

# app = Flask(__name__)
# UPLOAD_FOLDER = '../known_faces'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# def get_db_connection():
#     return mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="",
#         database="smartdoorlock"
#     )

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/register', methods=['POST'])
# def register():
#     image = request.files['image']
#     if image:
#         image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
#         image.save(image_path)

#         db = get_db_connection()
#         cursor = db.cursor()
#         cursor.execute("INSERT INTO users (image_path) VALUES (%s)", (image.filename,))
#         db.commit()
#         cursor.close()
#         db.close()

#         return redirect('/')
#     else:
#         return "Gagal: Tidak ada gambar yang dipilih"

# @app.route('/logs')
# def logs():
#     db = get_db_connection()
#     cursor = db.cursor()
#     cursor.execute("SELECT name, access_time FROM logs ORDER BY access_time DESC")
#     logs = cursor.fetchall()
#     cursor.close()
#     db.close()
#     return render_template('logs.html', logs=logs)

# if __name__ == '__main__':
#     app.run(debug=True)



from flask import Flask, render_template, request, redirect
import os
import mysql.connector
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
UPLOAD_FOLDER = '../known_faces'  # Sesuaikan path relatif
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="smartdoorlock"
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    image = request.files['image']

    if name and image:
        # Rename file sesuai nama yang diinput (plus ekstensi asli)
        name = request.form['name'].strip()
        # Hanya mengizinkan huruf, angka, spasi, dan strip agar tetap aman
        name_cleaned = re.sub(r'[^\w\s-]', '', name).strip()

        filename = f"{name_cleaned}{os.path.splitext(image.filename)[1]}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # Simpan ke database
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (image_path) VALUES (%s)", (filename,))
        db.commit()
        cursor.close()
        db.close()

        return redirect('/')
    else:
        return "Gagal: Nama dan Gambar wajib diisi"

@app.route('/logs')
def logs():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT name, access_time FROM logs ORDER BY access_time DESC")
    logs = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('logs.html', logs=logs)

@app.route('/users')
def users():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, image_path FROM users")
    users = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('users.html', users=users)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT image_path FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    if result:
        image_path = result[0]
        # Hapus file gambar
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_path))
        except Exception as e:
            print(f"Gagal hapus file: {e}")
        # Hapus dari database
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()
    cursor.close()
    db.close()
    return redirect('/users')


if __name__ == '__main__':
    app.run(debug=True)
