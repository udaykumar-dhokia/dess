from flask import Flask, render_template, request, jsonify, redirect, url_for, jsonify, json, flash
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
app.secret_key = 'AIzaSyDfXfv2GAJMPwJO_4uCGaHOTHxkb8FBqHA'
PINATA_API_KEY = '927a429a98f672d6736d'
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
    url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
    response = requests.get(url)
    
    if response.status_code == 200:
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

@app.route('/user/<id>', methods=['GET'])
def user(id):
    uid = id
    if not uid:
        return redirect(url_for('login'))

    try:
        response = supabase.table('users').select('*').eq('uid', uid).execute()


        if response.data: 
            user_data = response.data[0]
            user_email = user_data['email']
            user_private_key = users[user_email]['private_key']
            
            received_hashes = user_data.get('inbox_mail', [])
            decrypted_emails = []
            
            if received_hashes:
                for ipfs_hash in received_hashes:
                    email_record_json = fetch_from_pinata(ipfs_hash)

                    if email_record_json:
                        email_record = json.loads(email_record_json)
                        decrypted_body = decrypt_message(email_record['body'], user_private_key)
                        email_record['body'] = decrypted_body 
                        email_record['formatted_timestamp'] = format_timestamp(email_record['timestamp'])
                        decrypted_emails.append(email_record)
                        print(decrypted_emails)

            return render_template('landing.html', user=user_data, active_tab='inbox', emails=decrypted_emails)

        else:
            return redirect(url_for('login'))

    except Exception as e:
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

    return render_template('auth/signup.html')

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            response = supabase.table('users').select('password', 'uid').eq('email', email).execute()
            
            if response.data:
                userPassword = response.data[0]["password"]
                user_uid = response.data[0]["uid"]
                
                if password == userPassword:
                    # Set the user email in cookies
                    response = redirect(url_for('user', id=user_uid))
                    response.set_cookie('user_email', email)
                    return response
                else:
                    return jsonify({'error': 'Invalid credentials'}), 401
            else:
                return jsonify({'error': 'User not found'}), 404

        except Exception as e:
            print(f"Error during login: {e}")
            return jsonify({'error': str(e)}), 400

    return render_template('auth/login.html')

@app.route('/outbox', methods=['GET'])
def outbox():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data:
            user_data = response.data[0]
            return render_template('outbox.html', user_data=user_data, active_tab='outbox')
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 400

    return render_template('outbox.html')
    


@app.route('/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    email = data.get('email')
    
    response = supabase.table("users").select("email").execute()

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

        response = supabase.table("users").select("public_key").eq("email", recipient).execute()
        recipient_public_key = response.data[0]['public_key']
        if recipient_public_key:
            encrypted_body = encrypt_message(body, recipient_public_key)

            email_record = {
                'sender': sender,
                'recipient': recipient,
                'subject': email_data['subject'],
                'body': encrypted_body,
                'timestamp': datetime.utcnow().isoformat()
            }

            email_record_json = json.dumps(email_record)

            ipfs_hash = upload_to_pinata(email_record_json)

            if ipfs_hash:
                # Update sender and recipient records
                if 'sent' not in users[sender]:
                    users[sender]['sent'] = []
                users[sender]['sent'].append(ipfs_hash)

                if 'received' not in users[recipient]:
                    users[recipient]['received'] = []
                users[recipient]['received'].append(ipfs_hash)

                save_users(users)

                supabase.table('users').update({"inbox_mail": users[recipient]['received']}).eq("email", recipient).execute()
                supabase.table('users').update({"outbox_mail": users[sender]['sent']}).eq('email', sender).execute()

                # Flash success message and store IPFS hash in session
                flash('Email sent successfully!', 'success')
                return render_template('landing.html', user=userResponse.data[0], ipfs_hash=ipfs_hash)

        # Handle recipient not found
        flash('Recipient not found!', 'error')
        return render_template('landing.html', user=userResponse.data[0], error="Recipient not found!")

    return render_template('landing.html', user=userResponse.data[0])



def format_timestamp(timestamp):
    dt = datetime.fromisoformat(timestamp)
    return dt.strftime('%d %B %Y, %I:%M %p')

@app.route('/email/<email_id>')
def view_email(email_id):
    email_response = supabase.table("users").select('inbox_mail').eq("email", email_id).execute()
    
    if email_response.data:
        email = email_response.data[0]
        user_email = email_response['email']
        user_private_key = users[user_email]['private_key']
        email['body'] = decrypt_message(email['body'], user_private_key)
        return render_template('view_email.html', email=email)
    else:
        flash("Email not found!")
        return redirect(url_for('landing_page'))
    

@app.route('/account')
def account():
    try:
        # Assuming you have the user ID or email stored in session or cookies
        user_email = request.cookies.get('user_email')
        
        if not user_email:
            flash("User not logged in!", "error")
            return redirect(url_for('login'))
        
        # Fetch user data from Supabase
        response = supabase.table('users').select('*').eq('email', user_email).execute()
        
        if response.data:
            user_data = response.data[0]
            return render_template('account.html', user=user_data, active_tab='account')
        else:
            flash("User not found!", "error")
            return redirect(url_for('login'))
    
    except Exception as e:
        print(f"Error fetching user data: {e}")
        flash("An error occurred while fetching account information.", "error")
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    response.delete_cookie('user_email')
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)