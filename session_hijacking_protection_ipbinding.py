import hashlib
import os
import requests

# Example function to simulate device fingerprinting using IP and User Agent
def generate_session_token(user_id, user_agent, ip_address):
    # Combine user_id, user_agent, and ip to generate a unique session token
    session_data = f"{user_id}-{user_agent}-{ip_address}"
    return hashlib.sha256(session_data.encode()).hexdigest()

# Function to get user's IP address (for demonstration, uses an external API)
def get_user_ip():
    response = requests.get('https://api.ipify.org?format=json')
    return response.json()['ip']

# Simulate session creation
def create_session(user_id, user_agent):
    ip_address = get_user_ip()
    session_token = generate_session_token(user_id, user_agent, ip_address)
    -
    # Store the session token securely in a database or session storage
    print(f"Session Token for User {user_id}: {session_token}")
    return session_token

# Simulate session validation
def validate_session(user_id, user_agent, session_token):
    ip_address = get_user_ip()
    expected_token = generate_session_token(user_id, user_agent, ip_address)
    
    if session_token == expected_token:
        print("Session is valid.")
    else:
        print("Session has been hijacked or invalid.")

# Example Usage
user_id = "user123"
user_agent = "Mozilla/5.0"  # Example user-agent string
session_token = create_session(user_id, user_agent)

# Later, validate the session to ensure it hasn't been hijacked
validate_session(user_id, user_agent, session_token)
