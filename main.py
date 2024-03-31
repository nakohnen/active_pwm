from flask import Flask, request, render_template_string, redirect, url_for, session
import os
import bcrypt

app = Flask(__name__)

# Set the secret key to a random bytes. Keep this really secret!
app.secret_key = os.urandom(24)

# Set the permanent session lifetime to 1 day
from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=1)

DATABASE_PATH = 'pw_db.sqlite3'

LOGIN_PAGE = '''
    <!doctype html>
    <title>Login</title>
    <h1>Login</h1>
    <form method=post>
        <label for="password">Password:</label>
        <input type=password name=password>
        <input type=submit value=Login>
    </form>
'''

def check_password(password):
    if os.path.exists('pw_hash.txt'):
        with open('pw_hash.txt', 'rb') as file:
            stored_hash = file.read()
            return bcrypt.checkpw(password.encode(), stored_hash)
    return False

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if check_password(password):
            session.permanent = True  # Use the app's permanent session lifetime
            session['user_id'] = os.urandom(24).hex()  # Setting a random session ID
            return redirect(url_for('home'))
        else:
            return 'Login Failed', 403
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template_string(LOGIN_PAGE)

@app.route('/home')
def home():
    if 'user_id' in session:
        return f'You are logged in'
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

