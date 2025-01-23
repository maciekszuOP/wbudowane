from flask import Flask, jsonify, request, g, render_template, redirect, url_for, session
import sqlite3
import random
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = 'blik_users.db'

def get_db():
    """Get a database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """Query the database."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.before_request
def clear_expired_blik_codes():
    """Clear expired BLIK codes before processing any request."""
    current_time = int(time.time())
    get_db().execute('UPDATE users SET blik_code = ?, blik_time = ? WHERE blik_time <= ?', ['', 0, current_time])
    get_db().commit()

@app.route('/')
def index():
    """Render the login page or redirect to BLIK code generation page if logged in."""
    if 'user_id' in session:
        return redirect(url_for('generate_blik_page'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    login = request.form['login']
    password = request.form['password']
    user = query_db('SELECT * FROM users WHERE login = ? AND password = ?', [login, password], one=True)
    if user:
        session['user_id'] = user['id']
        return redirect(url_for('generate_blik_page'))
    else:
        return render_template('login.html', error="Invalid credentials")

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/generate_blik_page')
def generate_blik_page():
    """Generate and display a BLIK code for the logged-in user."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    user = query_db('SELECT * FROM users WHERE id = ?', [user_id], one=True)

    current_time = int(time.time())

    # Clear expired BLIK code if exists
    if user['blik_time'] and current_time > user['blik_time']:
        get_db().execute('UPDATE users SET blik_code = ?, blik_time = ? WHERE id = ?', ['', 0, user_id])
        get_db().commit()

    # Generate a new BLIK code
    blik_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    expiry_time = current_time + 90  # BLIK code valid for 90 seconds

    # Update the database
    get_db().execute('UPDATE users SET blik_code = ?, blik_time = ? WHERE id = ?', [blik_code, expiry_time, user_id])
    get_db().commit()

    time_left = expiry_time - current_time
    return render_template('blik_code.html', blik_code=blik_code, time_left=time_left)

@app.route('/verify_blik', methods=['POST'])
def verify_blik():
    """Verify the BLIK code and process the transaction."""
    blik_code = request.json.get('blik_code')
    amount = request.json.get('amount')
    current_time = int(time.time())

    user = query_db('SELECT * FROM users WHERE blik_code = ?', [blik_code], one=True)

    if user:
        # Check if the BLIK code is expired
        if current_time > user['blik_time']:
            get_db().execute('UPDATE users SET blik_code = ?, blik_time = ? WHERE id = ?', ['', 0, user['id']])
            get_db().commit()
            return jsonify({"message": "BLIK code expired"}), 400

        # Check if the user has sufficient balance
        if user['balance'] >= amount:
            new_balance = user['balance'] - amount
            get_db().execute('UPDATE users SET balance = ? WHERE id = ?', [new_balance, user['id']])
            get_db().commit()
            return jsonify({"message": "Transaction successful", "new_balance": new_balance})
        else:
            return jsonify({"message": "Insufficient funds"}), 400
    else:
        return jsonify({"message": "Invalid BLIK code"}), 400

@app.route('/check_balance', methods=['POST'])
def check_balance():
    """Check the balance for a card transaction."""
    try:
        card_id = request.json.get('card_id')
        amount = request.json.get('amount')

        if not card_id or not amount:
            return jsonify({"message": "Invalid input"}), 400

        user = query_db('SELECT * FROM users WHERE id = ?', [card_id], one=True)

        if user and user['balance'] >= amount:
            new_balance = user['balance'] - amount
            get_db().execute('UPDATE users SET balance = ? WHERE id = ?', [new_balance, card_id])
            get_db().commit()
            return jsonify({"message": "Transaction successful", "new_balance": new_balance})
        else:
            return jsonify({"message": "Insufficient funds or invalid card"}), 400

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "Internal server error"}), 500

if __name__ == '__main__':
    with app.app_context():
        db = get_db()
        db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, login TEXT, password TEXT, balance REAL, blik_code TEXT, blik_time INTEGER)')
        if not query_db('SELECT * FROM users'):
            users = [
                (636958224221, '1', '1', 100.0, '', 0),
                (2, 'user2', 'password2', 200.0, '', 0),
                (3, 'user3', 'password3', 300.0, '', 0),
                (4, 'user4', 'password4', 400.0, '', 0),
                (5, 'user5', 'password5', 500.0, '', 0),
                (6, 'user6', 'password6', 600.0, '', 0),
                (7, 'user7', 'password7', 700.0, '', 0),
                (8, 'user8', 'password8', 800.0, '', 0),
                (9, 'user9', 'password9', 900.0, '', 0),
                (10, 'user10', 'password10', 1000.0, '', 0)
            ]
            db.executemany('INSERT INTO users (id, login, password, balance, blik_code, blik_time) VALUES (?, ?, ?, ?, ?, ?)', users)
            db.commit()

    app.run(host='0.0.0.0', port=5000, debug=True)
#koniec
