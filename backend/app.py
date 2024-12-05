import jwt
import datetime
from functools import wraps
import os
from flask import Flask, request, jsonify, render_template
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__, template_folder='../templates')

# Secret key for encoding/decoding JWT
app.config['SECRET_KEY'] = 'your_secret_key'

# Database connection function
def get_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../db/tickets.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Token validation decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token.split(" ")[1], app.config['SECRET_KEY'], algorithms=['HS256'])
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
    return render_template('index.html')

# User registration
@app.route('/register', methods=['POST'])
def register():
    data = request.form
    name = data['name']
    email = data['email']
    password = data['password']

    # Check if user already exists
    conn = get_db_connection()
    existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if existing_user:
        conn.close()
        return jsonify({'error': 'User already exists!'}), 400

    password_hash = generate_password_hash(password)

    # Insert the new user
    conn.execute(
        'INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
        (name, email, password_hash, 'User')
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registered successfully!'}), 201

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login logic here
        data = request.form
        email = data['email']
        password = data['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            # Generate a JWT token with expiration
            token = jwt.encode(
                {
                    'user_id': user['id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=3600)  # 1 hour expiration
                },
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            return jsonify({'message': 'Login successful!', 'token': token}), 200
        return jsonify({'error': 'Invalid email or password'}), 401

    # For GET request, return the login page
    return render_template('login.html')  # Ensure you have login.html in templates folder

# Submit ticket route
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

# Get tickets for the logged-in user
@app.route('/tickets', methods=['GET'])
@token_required
def get_tickets(current_user):
    conn = get_db_connection()
    tickets = conn.execute(
        'SELECT * FROM tickets WHERE user_id = ?',
        (current_user['user_id'],)
    ).fetchall()
    conn.close()

    # Convert query results to a list of dictionaries for JSON response
    tickets_list = [dict(ticket) for ticket in tickets]

    # Return tickets as JSON instead of rendering HTML
    return jsonify({'tickets': tickets_list}), 200

# Resolve a ticket
@app.route('/resolve-ticket/<int:ticket_id>', methods=['POST'])
@token_required
def resolve_ticket(current_user, ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ? AND user_id = ?', (ticket_id, current_user['user_id'])).fetchone()
    
    if not ticket:
        conn.close()
        return jsonify({'error': 'Ticket not found or access denied'}), 404

    # Update ticket status to "Resolved"
    conn.execute('UPDATE tickets SET status = ? WHERE id = ?', ('Resolved', ticket_id))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Ticket {ticket_id} resolved successfully'}), 200

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)
