from flask import Flask, render_template, request, jsonify, redirect, url_for, jsonify
from firebase_admin import credentials, firestore, initialize_app
from firebase.firebase_config import auth
from supabase import create_client, Client
import secrets

import os

app = Flask(__name__)
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://chxfteilgshegswapudu.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNoeGZ0ZWlsZ3NoZWdzd2FwdWR1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjkyNzg2ODksImV4cCI6MjA0NDg1NDY4OX0.mmdsAEmka_Q5UMqgwrDg6Xq3Eu7EbRsuS-F0doULIAY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        
        # Print the response for debugging
        print(response.data)

        if response.data: 
            # Ensure that we have valid user data
            user_data = response.data[0]
            return render_template('landing.html', user=user_data, active_tab='inbox')
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

        try:
            uniqueId = secrets.token_hex(16)
            user_data = {'email': email, "password": password, 'uid':uniqueId,"lastName": lastName, "firstName": firstName}
            supabase.table('users').insert(user_data).execute()

            return jsonify({'message': 'User signed up successfully', 'user': user_data, "lastName": lastName, "firstName": firstName}), 201

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



@app.route('/get_user/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        # Fetch user data from Supabase table
        response = supabase.table('users').select('*').eq('id', user_id).execute()

        if response.data:
            return jsonify({'user': response.data[0]}), 200
        else:
            return jsonify({'message': 'User not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/logout')
def logout():
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)