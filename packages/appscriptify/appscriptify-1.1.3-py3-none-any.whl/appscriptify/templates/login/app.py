from flask import Flask, render_template, request, redirect, url_for, session
import database
import asyncio
import secrets
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Set a secret key for session management
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route('/')
def home():
    return """Welcome to the AppScriptify Login Template!
    <br><a href='/auth/login'>Login</a> | <a href='/auth/signup'>Sign Up</a> | <a href='/auth/logout'>Logout</a>"""

def save_cookie(data:dict):
    resp = redirect(url_for('home'))
    for key, value in data.items():
        resp.set_cookie(
            key=key,
            value=value,
            httponly=True,      # Prevent JavaScript access
            secure=False,       # Set to True in production for HTTPS only
            samesite='Lax',     # Protect against CSRF
            max_age=86400*7,    # Cookie expires in 7 days
            path='/'            # Cookie available for all paths
        )
    return resp

def save_user_cookie(username, email):
    payload = {
        'login': json.dumps({
            'username': username,
            'email': email
        })
    }
    return save_cookie(payload)

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form.to_dict()
        print('\n[Login data received]')
        print(data, flush=True)

        # Add validation for required fields
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return "Username and password are required", 400

        result = loop.run_until_complete(database.get_user(
            email=username,
            password=password
        ))
        
        if not result:
            return "Invalid credentials", 400
            
        if result['ok'] == 0:
            return result['msg'], 400
        
        # Set up session and cookies for the logged-in user
        user = result['user']
        response = save_user_cookie(
            username=user['username'],
            email=user['email']
        )
        
        # Also store in session for server-side tracking
        session['user_id'] = str(user.get('_id'))
        session['username'] = user['username']
        session['email'] = user['email']
        
        return response

    return render_template('login.html')

@app.route('/auth/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form.to_dict()
        print('\n[Signup data received]')
        print(data, flush=True)

        if data.get('password') != data.get('confirm'):
            return "Passwords do not match!", 400

        result = loop.run_until_complete(database.save_user(
            username=data.get('username'),
            password=data.get('password'),
            email=data.get('email'),
            ip=request.remote_addr
        ))
        
        if result['ok'] == 0:
            return result['msg'], 400

        # Set cookies and session for the new user
        response = save_user_cookie(
            username=data.get('username'),
            email=data.get('email')
        )
        
        # Store in session
        session['username'] = data.get('username')
        session['email'] = data.get('email')
        
        return response
    return render_template('signup.html')

@app.route('/auth/logout')
def logout():
    session.clear()  # Clear the session data
    resp = redirect(url_for('home'))
    # Clear cookies by setting their expiration in the past
    resp.set_cookie('username', '', expires=0, path='/')
    resp.set_cookie('email', '', expires=0, path='/')
    return resp

def get_cookie(key=None):
    # Get specified cookie or all cookies if key is None
    if key:
        return request.cookies.get(key)
    else:
        return request.cookies


if __name__ == '__main__':
    app.run(debug=True)