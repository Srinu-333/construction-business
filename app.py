from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
import sqlite3
import csv
import io
import hashlib
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the database and create required tables
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Customer Registration Table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            property TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # Admin Credentials Table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Create default admin if not exists
    cur.execute("SELECT * FROM admins WHERE username = ?", ("admin",))
    if not cur.fetchone():
        default_password = "pallavi123"
        password_hash = hashlib.sha256(default_password.encode()).hexdigest()
        cur.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ("admin", password_hash))

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    property = request.form['property']
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not name or not phone or not email:
        flash('All fields are required!', 'danger')
        return redirect(url_for('home'))

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO customers (name, phone, email, property, created_at) VALUES (?, ?, ?, ?, ?)',
                (name, phone, email, property, created_at))
    conn.commit()
    conn.close()

    flash('Inquiry submitted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username = ? AND password_hash = ?", (username, password_hash))
        admin = cur.fetchone()
        conn.close()

        if admin:
            session['admin_logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))  # ✅ Redirects to main webpage


@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        flash('Access denied. Please login as admin.', 'danger')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM customers')
    customers = cur.fetchall()
    conn.close()
    return render_template('admin.html', customers=customers)

@app.route('/export/customers')
def export_customers():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM customers')
    rows = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Phone', 'Email', 'Property', 'Created At'])
    writer.writerows(rows)
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     as_attachment=True, download_name='customers.csv')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
