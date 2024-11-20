import os
from flask import Flask, request, jsonify, render_template
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Database connection function
def get_db_connection():
    # Get the absolute path of tickets.db
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db/tickets.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Home route
@app.route('/')
def home():
    return 'Ticketing System API is running!'

# User login
@app.route('/login', methods=['POST'])
def login():
    data = request.form
    email = data['email']
    password = data['password']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        return jsonify({'message': 'Login successful!'}), 200
    return jsonify({'error': 'Invalid email or password'}), 401

# Submit ticket
@app.route('/submit-ticket', methods=['POST'])
def submit_ticket():
    data = request.form
    title = data['title']
    description = data['description']
    priority = data['priority']
    user_id = 1  # Hardcoded for now; replace with session user ID later.

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO tickets (title, description, priority, user_id) VALUES (?, ?, ?, ?)',
        (title, description, priority, user_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Ticket submitted successfully!'}), 201

if __name__ == '__main__':
    app.run(debug=True)
