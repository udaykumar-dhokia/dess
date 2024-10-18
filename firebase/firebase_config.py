# firebase_config.py
import firebase_admin
from firebase_admin import credentials, auth

# Initialize the Firebase Admin SDK
cred = credentials.Certificate('firebase/dess.json')
firebase_admin.initialize_app(cred)

# Pyrebase Configuration for Web API usage (use this for user signup/login)
import pyrebase

# firebase_config = {
#     "apiKey": "your-api-key",
#     "authDomain": "your-app.firebaseapp.com",
#     "projectId": "your-project-id",
#     "storageBucket": "your-project-id.appspot.com",
#     "messagingSenderId": "your-messaging-sender-id",
#     "appId": "your-app-id",
#     "measurementId": "your-measurement-id",
# }

firebaseConfig = {
  "apiKey": "AIzaSyDfXfv2GAJMPwJO_4uCGaHOTHxkb8FBqHA",
  "authDomain": "dess-2c181.firebaseapp.com",
  "projectId": "dess-2c181",
  "storageBucket": "dess-2c181.appspot.com",
  "messagingSenderId": "781221941944",
  "appId": "1:781221941944:web:4a2041ca386609738b9a4d",
  "measurementId": "G-XJHFBE7DX0",
  "databaseURL": "",
};

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
