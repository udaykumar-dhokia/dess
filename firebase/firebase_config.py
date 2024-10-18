# firebase_config.py
import firebase_admin
from firebase_admin import credentials, auth

# Initialize the Firebase Admin SDK
cred = credentials.Certificate('firebase/dmail-11bb6-firebase-adminsdk-4hkyf-1d618a571d.json')
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
  'apiKey': "AIzaSyBJtv9e801Xn8grL2oEeg_ix1tYtiVnxQc",
  'authDomain': "dmail-11bb6.firebaseapp.com",
  'projectId': "dmail-11bb6",
  'storageBucket': "dmail-11bb6.appspot.com",
  'messagingSenderId': "1037426651907",
  'appId': "1:1037426651907:web:c2611460264a9a87d06f36",
  'measurementId': "G-FGZN3Z5158",
  "databaseURL":""
};

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
