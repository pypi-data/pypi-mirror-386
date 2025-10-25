import motor.motor_asyncio
from dotenv import load_dotenv
import os
import json
import hashlib
import secrets
import base64
import hmac

load_dotenv()

with open('config.json') as file:
    config = json.load(file)

if not config.get('users_database') or not config.get('users_collection') or os.environ.get('MONGO_URI') == 'your-mongodb-connection-string-here':
    print("Please set up your MongoDB configuration in config.json and .env files.")

USERS_DB = config['users_database']
USERS_COLLECTION = config['users_collection']

uri = os.environ['MONGO_URI']
client = motor.motor_asyncio.AsyncIOMotorClient(uri)
db = client[USERS_DB]
users = db[USERS_COLLECTION]

async def write_data(data):
    result = await users.insert_one(data)
    print("Inserted ID:", result.inserted_id)
    print('Data Updated')

async def update_data():
    result = await users.update_one(
        {'name':'Vansh'},
        {'$set': {'Age': 12}}
    )
    print("Matched:", result.matched_count, "Modified:", result.modified_count)

async def read_data(query):
    document = await users.find_one(query)
    return document

async def save_user(username, password, email, ip):
    # If already exist with same Email
    existing_user = await read_data({'email': email})
    if existing_user:
        return {'ok':0, 'msg':'Email already registered'}
    
    # Hash and salt the password together
    salt = secrets.token_bytes(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    pwd_storage = base64.b64encode(salt + pwd_hash).decode('utf-8')
    user_data = {
        'username': username,
        'password': pwd_storage,
        'email': email,
        'ip': ip
    }
    await write_data(user_data)
    return {'ok':1}

async def get_user(email, password):
    # Input validation
    if not email or not password:
        return {'ok': 0, 'msg': 'Email/username and password are required'}

    try:
        # Fetch user by email or username
        user = await read_data({
            '$or': [
                {'email': email},
                {'username': email}  # Allow login with username too
            ]
        })
        if not user:
            return {'ok': 0, 'msg': 'User not found'}
        
        # Verify password
        stored_data = base64.b64decode(user['password'])
        salt = stored_data[:16]
        stored_hash = stored_data[16:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        
        if hmac.compare_digest(stored_hash, pwd_hash):
            return {'ok': 1, 'user': user}
        return {'ok': 0, 'msg': 'Invalid password'}
    except Exception as e:
        print(f"Error in get_user: {str(e)}")
        return {'ok': 0, 'msg': 'An error occurred during login'}

