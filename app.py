from flask import Flask, render_template, request
from firebase_admin import credentials, firestore, initialize_app
from firebase.firebase_config import auth

app = Flask(__name__)
app.secret_key = 'AIzaSyBJtv9e801Xn8grL2oEeg_ix1tYtiVnxQc'
db = firestore.client()

@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)