from flask import Flask, jsonify, request, g, render_template, redirect, url_for, session
import sqlite3
import random
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = 'blik_users.db'

def get_db():
    # Pobiera połączenie z bazą danych, jeśli nie istnieje, tworzy nowe
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    # Zamyka połączenie z bazą danych po zakończeniu kontekstu aplikacji
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    # Wykonuje zapytanie do bazy danych i zwraca wynik
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def update_blik_code(user_id, blik_code='', blik_time=0):
    # Aktualizuje kod BLIK i czas jego ważności dla użytkownika w bazie danych
    get_db().execute('UPDATE users SET blik_code = ?, blik_time = ? WHERE id = ?', [blik_code, blik_time, user_id])
    get_db().commit()

def is_user_logged_in():
    # Sprawdza, czy użytkownik jest zalogowany, poprzez sprawdzenie obecności 'user_id' w sesji
    return 'user_id' in session

def update_user_balance(user_id, new_balance):
    # Aktualizuje saldo użytkownika w bazie danych
    get_db().execute('UPDATE users SET balance = ? WHERE id = ?', [new_balance, user_id])
    get_db().commit()

@app.before_request
def clear_expired_blik_codes():
    # Usuwa wygasłe kody BLIK przed przetworzeniem jakiegokolwiek żądania
    current_time = int(time.time())
    get_db().execute('UPDATE users SET blik_code = ?, blik_time = ? WHERE blik_time <= ?', ['', 0, current_time])
    get_db().commit()

@app.route('/')
def index():
    # Renderuje stronę logowania lub przekierowuje do strony generowania kodu BLIK, jeśli użytkownik jest zalogowany
    if is_user_logged_in():
        return redirect(url_for('generate_blik_page'))
    return render_template('login.html')

@app.route('/generate_blik_page')
def generate_blik_page():
    # Generuje i wyświetla kod BLIK dla zalogowanego użytkownika
    if not is_user_logged_in():
        return redirect(url_for('index'))

    user_id = session['user_id']
    user = query_db('SELECT * FROM users WHERE id = ?', [user_id], one=True)

    current_time = int(time.time())

    # Usuwa wygasły kod BLIK, jeśli istnieje
    if user['blik_time'] and current_time > user['blik_time']:
        update_blik_code(user_id)

    # Generuje nowy kod BLIK
    blik_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    expiry_time = current_time + 90  # Kod BLIK ważny przez 90 sekund

    # Aktualizuje bazę danych
    update_blik_code(user_id, blik_code, expiry_time)

    time_left = expiry_time - current_time
    return render_template('blik_code.html', blik_code=blik_code, time_left=time_left)

@app.route('/verify_blik', methods=['POST'])
def verify_blik():
    # Weryfikuje kod BLIK i przetwarza transakcję
    blik_code = request.json.get('blik_code')
    amount = request.json.get('amount')
    current_time = int(time.time())

    user = query_db('SELECT * FROM users WHERE blik_code = ?', [blik_code], one=True)

    if user:
        # Sprawdza, czy kod BLIK wygasł
        if current_time > user['blik_time']:
            update_blik_code(user['id'])
            return jsonify({"message": "BLIK code expired"}), 400

        # Sprawdza, czy użytkownik ma wystarczające saldo
        if user['balance'] >= amount:
            new_balance = user['balance'] - amount
            update_user_balance(user['id'], new_balance)
            return jsonify({"message": "Transaction successful", "new_balance": new_balance})
        else:
            return jsonify({"message": "Insufficient funds"}), 400
    else:
        return jsonify({"message": "Invalid BLIK code"}), 400

@app.route('/check_balance', methods=['POST'])
def check_balance():
    # Sprawdza saldo dla transakcji kartą
    try:
        card_id = request.json.get('card_id')
        amount = request.json.get('amount')

        if not card_id or not amount:
            return jsonify({"message": "Invalid input"}), 400

        user = query_db('SELECT * FROM users WHERE id = ?', [card_id], one=True)

        if user and user['balance'] >= amount:
            new_balance = user['balance'] - amount
            update_user_balance(card_id, new_balance)
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
                (2, '2', '2', 200.0, '', 0),
                (3, '3', '3', 300.0, '', 0),
                (4, '4', '4', 400.0, '', 0),
                (5, '5', '5', 500.0, '', 0),
                (6, '6', '6', 600.0, '', 0),
                (7, '7', '7', 700.0, '', 0),
                (8, '8', '8', 800.0, '', 0),
                (9, '9', '9', 900.0, '', 0),
                (10, '10', '10', 1000.0, '', 0)
            ]
            db.executemany('INSERT INTO users (id, login, password, balance, blik_code, blik_time) VALUES (?, ?, ?, ?, ?, ?)', users)
            db.commit()

    app.run(host='0.0.0.0', port=8080, debug=True)