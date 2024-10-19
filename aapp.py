from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from supabase import create_client, Client
import secrets
import os
import json
from datetime import datetime
import requests
from web3 import Web3
from encryption import generate_keys, encrypt_message, decrypt_message

app = Flask(__name__)
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://chxfteilgshegswapudu.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNoeGZ0ZWlsZ3NoZWdzd2FwdWR1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjkyNzg2ODksImV4cCI6MjA0NDg1NDY4OX0.mmdsAEmka_Q5UMqgwrDg6Xq3Eu7EbRsuS-F0doULIAY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
USER_DATA_FILE = 'users_data.json'
app.secret_key = 'AIzaSyDfXfv2GAJMPwJO_4uCGaHOTHxkb8FBqHA'
PINATA_API_KEY = '927a429a98f672d6736d'
PINATA_API_SECRET = '1c699bbca60f57bfe5fd809abd67c8450410a88c7472201316af5a506f9368b8'

# Configure Web3 for Polygon Mumbai Testnet
MUMBAI_RPC_URL = 'https://polygon-mumbai.infura.io/v3/e4d28daef2554058ae5d943b26043547'
web3 = Web3(Web3.HTTPProvider(MUMBAI_RPC_URL))
CONTRACT_ADDRESS = '0xf8e81D47203A594245E36C48e151709F0C19fBe8'
CONTRACT_ABI = [
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "emailId",
				"type": "uint256"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "sender",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "recipient",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "string",
				"name": "subject",
				"type": "string"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"name": "EmailSent",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "emailId",
				"type": "uint256"
			}
		],
		"name": "getEmail",
		"outputs": [
			{
				"components": [
					{
						"internalType": "string",
						"name": "sender",
						"type": "string"
					},
					{
						"internalType": "string",
						"name": "recipient",
						"type": "string"
					},
					{
						"internalType": "string",
						"name": "subject",
						"type": "string"
					},
					{
						"internalType": "string",
						"name": "body",
						"type": "string"
					},
					{
						"internalType": "uint256",
						"name": "timestamp",
						"type": "uint256"
					}
				],
				"internalType": "struct EmailStorage.Email",
				"name": "",
				"type": "tuple"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getEmailsBySender",
		"outputs": [
			{
				"internalType": "uint256[]",
				"name": "",
				"type": "uint256[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "sender",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "recipient",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "subject",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "body",
				"type": "string"
			}
		],
		"name": "sendEmail",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]

# Initialize the smart contract
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

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

            return render_template('landing.html', user=user_data, active_tab='inbox', emails=decrypted_emails)

        else:
            return redirect(url_for('login'))

    except Exception as e:
        print(f"Error fetching user: {e}")
        return redirect(url_for('login'))

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
                if 'sent' not in users[sender]:
                    users[sender]['sent'] = []
                users[sender]['sent'].append(ipfs_hash)

                if 'received' not in users[recipient]:
                    users[recipient]['received'] = []
                users[recipient]['received'].append(ipfs_hash)

                save_users(users)  # Save the updated users data to file

                # Store email metadata on the blockchain
                store_email_on_chain(sender, recipient, email_data['subject'], ipfs_hash)

                supabase.table('users').update({"inbox_mail": users[recipient]['received']}).eq("email", recipient).execute()
                supabase.table('users').update({"outbox_mail": users[sender]['sent']}).eq('email', sender).execute()

                flash('Email sent successfully!')
                return redirect(url_for('user', id=userResponse.data[0]['uid']))

        return render_template('landing.html', user=userResponse.data[0], error="Recipient not found!")

    return render_template('landing.html', user=userResponse.data[0])

def store_email_on_chain(sender, recipient, subject, ipfs_hash):
    # Prepare the transaction
    txn = contract.functions.sendEmail(recipient, subject, ipfs_hash).buildTransaction({
        'from': sender,  # Ensure 'sender' is the user's address
        'nonce': web3.eth.getTransactionCount(sender),
        'gas': 2000000,
        'gasPrice': web3.toWei('50', 'gwei')
    })

    # Sign the transaction (replace 'YOUR_PRIVATE_KEY' with the sender's actual private key)
    signed_txn = web3.eth.account.signTransaction(txn, private_key='28531a9a1a584313c018b3ba556cf0e0f4044fe83a9a132b45e651b24da852ea')

    # Send the transaction
    txn_hash = web3.eth.sendRawTransaction(signed_txn.rawTransaction)
    
    # Wait for transaction receipt
    txn_receipt = web3.eth.waitForTransactionReceipt(txn_hash)
    
    return txn_receipt

def format_timestamp(timestamp):
    dt = datetime.fromisoformat(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    app.run(debug=True)
