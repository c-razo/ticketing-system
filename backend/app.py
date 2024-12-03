import jwt
import datetime
from functools import wraps
import os
from flask import Flask, request, jsonify, render_template
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Secret key for encoding/decoding JWT
app.config['SECRET_KEY'] = 'your_secret_key'

# Database connection function
def get_db_connection():
    # Get the absolute path of tickets.db
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db/tickets.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Token validation decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')  # Fetch token from Authorization header

        print("Authorization Header:", token)  # Log the raw token

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        try:
            # Decode token using the app's SECRET_KEY
            data = jwt.decode(token.split(" ")[1], app.config['SECRET_KEY'], algorithms=['HS256'])

            print("Decoded Token:", data)  # Log decoded data (if decoding succeeds)

            current_user = {'user_id': data['user_id']}
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# Home route
@app.route('/')
def home():
    return 'Ticketing System API is running!'

# User registration
@app.route('/register', methods=['POST'])
def register():
    data = request.form
    name = data['name']
    email = data['email']
    password = data['password']

    # Check if the user already exists
    conn = get_db_connection()
    existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if existing_user:
        conn.close()
        return jsonify({'error': 'User already exists!'}), 400

    # Hash the password
    password_hash = generate_password_hash(password)

    # Insert the new user into the database
    conn.execute(
        'INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
        (name, email, password_hash, 'User')
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registered successfully!'}), 201

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
        # Generate a JWT token with 10 seconds expiration time
        token = jwt.encode(
            {
                'user_id': user['id'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return jsonify({'message': 'Login successful!', 'token': token}), 200

    return jsonify({'error': 'Invalid email or password'}), 401

# Submit ticket
@app.route('/submit-ticket', methods=['POST'])
@token_required
def submit_ticket(current_user):
    data = request.form
    title = data['title']
    description = data['description']
    priority = data['priority']

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO tickets (title, description, priority, user_id) VALUES (?, ?, ?, ?)',
        (title, description, priority, current_user['user_id'])
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Ticket submitted successfully!'}), 201

@app.route('/tickets', methods=['GET'])
@token_required
def get_tickets(current_user):
    conn = get_db_connection()
    tickets = conn.execute(
        'SELECT * FROM tickets WHERE user_id = ?',
        (current_user['user_id'],)
    ).fetchall()
    conn.close()

    # Convert tickets to a list of dictionaries
    tickets_list = [dict(ticket) for ticket in tickets]

    return jsonify({'tickets': tickets_list}), 200

if __name__ == '__main__':
    app.run(debug=True)

