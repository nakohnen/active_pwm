from flask import Flask, request, render_template_string, redirect, url_for
import bcrypt
import os

app = Flask(__name__)

# Simple login page template
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
    """Check if the provided password matches the stored hash."""
    if os.path.exists('pw_hash.txt'):
        with open('pw_hash.txt', 'rb') as file:
            stored_hash = file.read()
            # Passwords need to be in bytes for bcrypt
            return bcrypt.checkpw(password.encode(), stored_hash)
    return False

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if check_password(password):
            return redirect(url_for('home'))
        else:
            return 'Login Failed', 403
    return render_template_string(LOGIN_PAGE)

@app.route('/home')
def home():
    return 'You are logged in'

if __name__ == '__main__':
    app.run(debug=True)

