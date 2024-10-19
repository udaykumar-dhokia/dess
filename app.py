from flask import Flask, render_template, request, jsonify, redirect, url_for, jsonify, json, flash
from firebase_admin import credentials, firestore, initialize_app
from firebase.firebase_config import auth
from supabase import create_client, Client
import secrets
from datetime import datetime
from encryption import generate_keys, encrypt_message, decrypt_message
import requests
import os

app = Flask(__name__)
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://chxfteilgshegswapudu.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNoeGZ0ZWlsZ3NoZWdzd2FwdWR1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjkyNzg2ODksImV4cCI6MjA0NDg1NDY4OX0.mmdsAEmka_Q5UMqgwrDg6Xq3Eu7EbRsuS-F0doULIAY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
USER_DATA_FILE = 'users_data.json'
PINATA_API_KEY = '927a429a98f672d6736d'
app.secret_key = 'AIzaSyDfXfv2GAJMPwJO_4uCGaHOTHxkb8FBqHA'
PINATA_API_SECRET = '1c699bbca60f57bfe5fd809abd67c8450410a88c7472201316af5a506f9368b8'

def upload_to_pinata(email_record_json):    
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    
    files = {
        'file': ('email_record.json', email_record_json)
    }
    
    headers = {
        'pinata_api_key': PINATA_API_KEY,
        'pinata_secret_api_key': PINATA_API_SECRET
    }
    
    response = requests.post(url, files=files, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('IpfsHash')
    else:
        return None
    
def fetch_from_pinata(ipfs_hash):
    # Function to fetch email record from IPFS using Pinata
    url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
    response = requests.get(url)
    
    if response.status_code == 200:
        print(response.content.decode())
        return response.content.decode()
    else:
        print(f"Error fetching from Pinata: {response.status_code}")
        return None

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

users = load_users()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/inbox')
def inbox():
    return render_template('inbox.html', active_tab='inbox')

@app.route('/sent')
def sent():
    return render_template('sent.html', active_tab='sent')

@app.route('/starred')
def starred():
    return render_template('starred.html', active_tab='starred')

@app.route('/draft')
def draft():
    return render_template('draft.html', active_tab='draft')

@app.route('/settings')
def settings():
    return render_template('settings.html', active_tab='settings')

@app.route('/account')
def account():
    return render_template('account.html', active_tab='account')

@app.route('/user/<id>', methods=['GET'])
def user(id):
    uid = id
    
    if not uid:
        return redirect(url_for('login'))

    try:
        # Fetch user data based on the UID
        response = supabase.table('users').select('*').eq('uid', uid).execute()


        if response.data: 
            # Ensure that we have valid user data
            user_data = response.data[0]
            user_email = user_data['email']
            user_private_key = users[user_email]['private_key']
            
            # Fetch the received email hashes from the user's inbox
            received_hashes = user_data.get('inbox_mail', [])
            decrypted_emails = []
            
            if received_hashes:
                for ipfs_hash in received_hashes:
                    # Fetch the email record from IPFS (you may need to implement this function)
                    email_record_json = fetch_from_pinata(ipfs_hash)

                    if email_record_json:
                        email_record = json.loads(email_record_json)
                        # Decrypt the email body
                        decrypted_body = decrypt_message(email_record['body'], user_private_key)
                        email_record['body'] = decrypted_body  # Replace encrypted body with decrypted body
                        email_record['formatted_timestamp'] = format_timestamp(email_record['timestamp'])
                        decrypted_emails.append(email_record)
                        print(decrypted_emails)

            return render_template('landing.html', user=user_data, active_tab='inbox', emails=decrypted_emails)

        else:
            # Redirect to login if no user found
            return redirect(url_for('login'))

    except Exception as e:
        # Log the error and redirect to login on failure
        print(f"Error fetching user: {e}")
        return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        firstName = request.form.get("firstName")
        lastName = request.form.get("lastName")
        public_key, private_key = generate_keys()

        try:
            users[email] = {
            'private_key': private_key,
            'emails': []
        }
            
            save_users(users)

            uniqueId = secrets.token_hex(16)
            user_data = {'email': email, "password": password, 'uid':uniqueId,"lastName": lastName, "firstName": firstName, "public_key": public_key}
            supabase.table('users').insert(user_data).execute()

            return render_template('auth/login.html')

        except Exception as e:
            return jsonify({'error': str(e)}), 400

    # Render signup form if GET request
    return render_template('auth/signup.html')

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            # Fetch both the password and UID
            response = supabase.table('users').select('password', 'uid').eq('email', email).execute()
            
            # Check if data is returned
            if response.data:
                userPassword = response.data[0]["password"]
                user_uid = response.data[0]["uid"]
                
                # Verify password (consider hashing passwords in production)
                if password == userPassword:
                    # Redirect to the user's landing page using UID
                    return redirect(url_for('user', id=user_uid))
                else:
                    return jsonify({'error': 'Invalid credentials'}), 401
            else:
                return jsonify({'error': 'User not found'}), 404

        except Exception as e:
            print(f"Error during login: {e}")
            return jsonify({'error': str(e)}), 400

    # Render login form if GET request
    return render_template('auth/login.html')

@app.route('/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    email = data.get('email')
    
    response = supabase.table("users").select("email").execute()

    # Replace this with your actual database query to check if the email exists
    email_exists = any(user['email'] == email for user in response.data)

    if email_exists:
        return jsonify({"exists": True}), 200
    else:
        return jsonify({"exists": False}), 404
    

@app.route('/send-email', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        email_data = request.form
        recipient = email_data['recipient']
        body = email_data['body']
        sender = email_data['sender']
        userResponse = supabase.table('users').select('*').eq('email', sender).execute()

        # Encrypt the email body using the recipient's public key
        response = supabase.table("users").select("public_key").eq("email", recipient).execute()
        recipient_public_key = response.data[0]['public_key']
        if recipient_public_key:
            encrypted_body = encrypt_message(body, recipient_public_key)

            # Create the email record (dictionary)
            email_record = {
                'sender': sender,
                'recipient': recipient,
                'subject': email_data['subject'],
                'body': encrypted_body,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Serialize the email record to JSON
            email_record_json = json.dumps(email_record)

            # Upload to IPFS using Pinata
            ipfs_hash = upload_to_pinata(email_record_json)

            if ipfs_hash:
                # Add IPFS hash to 'sent' list for sender
                if 'sent' not in users[sender]:
                    users[sender]['sent'] = []
                users[sender]['sent'].append(ipfs_hash)

                # Add IPFS hash to 'received' list for recipient
                if 'received' not in users[recipient]:
                    users[recipient]['received'] = []
                users[recipient]['received'].append(ipfs_hash)

                save_users(users)  # Save the updated users data to file

                supabase.table('users').update({"inbox_mail": users[recipient]['received']}).eq("email", recipient).execute()
                supabase.table('users').update({"outbox_mail": users[sender]['sent']}).eq('email', sender).execute()

                flash('Email sent successfully!')
                return redirect(url_for('user', id=userResponse.data[0]['uid']))

        return render_template('landing.html', user=userResponse.data[0], error="Recipient not found!")

    return render_template('landing.html', user=userResponse.data[0])


def format_timestamp(timestamp):
    dt = datetime.fromisoformat(timestamp)
    # Format: Day Month Year, HH:MM AM/PM
    return dt.strftime('%d %B %Y, %I:%M %p')

    
@app.route('/logout')
def logout():
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)