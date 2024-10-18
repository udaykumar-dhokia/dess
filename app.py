from flask import Flask, render_template, request
from firebase_admin import credentials, firestore, initialize_app
from firebase.firebase_config import auth

app = Flask(__name__)
app.secret_key = 'AIzaSyBJtv9e801Xn8grL2oEeg_ix1tYtiVnxQc'
db = firestore.client()

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


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)