from flask import Flask, session, redirect, url_for, request
import mysql.connector
import datetime
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'supersecretkey'


def get_db():
    """Öppnar en ny anslutning till databasen."""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='får_för_fårskallar'
    )


def query(sql, params=(), fetchone=False):
    """Liten hjälpfunktion: kör en fråga och returnerar rader som dict:ar."""
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)  # <- ger dict:ar istället för tupler
        cur.execute(sql, params)
        if fetchone:
            result = cur.fetchone()
        else:
            result = cur.fetchall()
        conn.commit()   # behövs för INSERT/UPDATE/DELETE
        return result
    finally:
        conn.close()    # viktigt: stäng anslutningen!


@app.route('/', methods=['GET', 'POST'])
def index():
    användarnamn = session.get('användarnamn')

    if användarnamn:
        # Hämta färsk info från databasen – inte från sessionen!
        user = query(
            'SELECT id, användarnamn, namn FROM users WHERE användarnamn = %s',
            (användarnamn,),
            fetchone=True
        )

        if user is None:
            # Användaren finns inte längre – logga ut
            session.clear()
            return redirect(url_for('index'))

        return f'''
            <h1>Välkommen, {user['användarnamn']}!</h1>
            <p>Ditt id i databasen: {user['id']}</p>
            <ul>
                <li><a href="/profile">Min profil</a></li>
                <li><a href="/forum">forum</a></li>
                <li><a href="/session-info">Visa sessionens innehåll</a></li>
                <li><a href="/logout">Logga ut</a></li>
            </ul>
        '''
    else:
        return '''
            <h1>Inte inloggad</h1>
            <p>Du måste logga in för att se mer.</p>
            <a href="/login">Logga in</a>
        '''
        


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        användarnamn = request.form['användarnamn']
        lösenord = request.form['lösenord']

        user = query(
            'SELECT id, användarnamn, lösenord FROM users WHERE användarnamn = %s',
            (användarnamn,),
            fetchone=True
        )

        # Kolla att användaren finns OCH att lösenordet stämmer
        if user and user['lösenord'] == lösenord:
            session['användarnamn'] = user['användarnamn']
            return redirect(url_for('index'))
        else:
            return 'Fel användarnamn eller lösenord. <a href="/login">Försök igen</a>'

    return '''
        <h1>Logga in</h1>
        <form method="post">
            Användarnamn: <input type="text" name="användarnamn"><br>
            Lösenord:     <input type="password" name="lösenord"><br>
            <input type="submit" value="Logga in">
        </form>
    '''


@app.route('/profile')
def profile():
    if 'användarnamn' not in session:
        return redirect(url_for('login'))

    user = query(
        'SELECT id, användarnamn, namn FROM users WHERE användarnamn = %s',
        (session['användarnamn'],),
        fetchone=True
    )

    return f'''
        <h1>Profil för {user['användarnamn']}</h1>
        <p>Id: {user['id']}</p>
        <p><a href="/">Tillbaka</a></p>
    '''



@app.route('/forum', methods=['GET', 'POST'])
def forum():
    if request.method == 'POST':
        # Läs in formulärdata
        name = request.form['användarnamn']
        text = request.form['inlägg']

        # Spara i databasen
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO posts (användarnamn, inlägg) VALUES (%s, %s)',
            (name, text)
        )
        conn.commit()
        conn.close()

        # Skicka tillbaka användaren till GET-sidan (undvik omsändning)
        return redirect(url_for('forum'))

    # GET: hämta alla inlägg och visa formulär + lista
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT användarnamn, inlägg FROM posts ORDER BY id DESC')
    posts = cur.fetchall()
    conn.close()

    rows = ''.join(
        f'<li><b>{p["användarnamn"]}</b>: {p["inlägg"]}</li>' for p in posts
    )

    return f'''
        <h1>Nytt inlägg</h1>
        <form method="post">
            Användarnamn: <input type="text" name="användarnamn"><br>
            Inlägg: <input type="text" name="inlägg"><br>
            <input type="submit" value="Spara">
        </form>

        <h2>Inlägg</h2>
        <ul>{rows}</ul>
    '''



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/session-info')
def session_info():
    return f"Session data: {dict(session)}"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')