from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
import re

# app instance
app = Flask(__name__)

# Enable CORS for frontend connection
CORS(app, origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","))

# Secret key for JWT
app.config['JWT_SECRET_KEY'] = 'your-super-secret-jwt-key-change-this-in-production'

# Database setup
def init_db():
    conn = sqlite3.connect('retailiq.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            store_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Helper functions
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_token(user_id):
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload.get('user_id')
    except:
        return None

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# /api/home
@app.route("/api/home", methods=['GET'])
def return_home():
    return jsonify({
        'message': "Welcome to RetailIQ API!",
        'status': 'running',
        'endpoints': {
            'signup': 'POST /api/auth/signup',
            'login': 'POST /api/auth/login',
            'profile': 'GET /api/auth/user/profile'
        }
    })

# /api/health
@app.route("/api/health", methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'message': 'RetailIQ API is healthy',
        'status': 'running'
    })

# /api/auth/signup
@app.route("/api/auth/signup", methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        store_name = data.get('store_name', '').strip()
        
        # Validation
        if not email or not password or not store_name:
            return jsonify({'success': False, 'error': 'Email, password, and store name are required'}), 400
        
        if not validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        # Database operations
        conn = sqlite3.connect('retailiq.db')
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Email already registered'}), 409
        
        # Create user
        hashed_password = hash_password(password)
        cursor.execute(
            'INSERT INTO users (email, hashed_password, store_name) VALUES (?, ?, ?)',
            (email, hashed_password, store_name)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Generate token
        token = generate_token(user_id)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user': {
                    'id': user_id,
                    'email': email,
                    'store_name': store_name
                },
                'token': token
            }
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# /api/auth/login
@app.route("/api/auth/login", methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        # Database operations
        conn = sqlite3.connect('retailiq.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, hashed_password, store_name FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not verify_password(password, user[2]):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Generate token
        token = generate_token(user[0])
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': {
                    'id': user[0],
                    'email': user[1],
                    'store_name': user[3]
                },
                'token': token
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# /api/auth/user/profile
@app.route("/api/auth/user/profile", methods=['GET'])
def get_profile():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Get user from database
        conn = sqlite3.connect('retailiq.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, store_name, created_at FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': {
                'user': {
                    'id': user[0],
                    'email': user[1],
                    'store_name': user[2],
                    'created_at': user[3]
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# /api/auth/verify-token
@app.route("/api/auth/verify-token", methods=['POST'])
def verify_token_endpoint():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        return jsonify({
            'success': True,
            'message': 'Token is valid',
            'data': {'user_id': user_id}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Invalid token'}), 401

if __name__ == "__main__":
    # Initialize database
    init_db()
    print("🚀 Starting RetailIQ API Server...")
    print("📍 Available endpoints:")
    print("   GET  /api/home")
    print("   GET  /api/health") 
    print("   POST /api/auth/signup")
    print("   POST /api/auth/login")
    print("   GET  /api/auth/user/profile")
    print("   POST /api/auth/verify-token")
    print("✅ Server ready at http://localhost:5000")
    
    app.run(debug=True, port=5000)