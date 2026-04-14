from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"

# 🔥 DB setup
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS users (email TEXT, password TEXT, name TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS tokens (email TEXT, token INTEGER)")

    conn.commit()
    conn.close()

init_db()

current_token = 1


# 🔐 LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Admin
        if email == "admin@gmail.com" and password == "admin":
            return redirect('/admin')

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()

        if user:
            session['user'] = email
            session['name'] = user[2]
            return redirect('/dashboard')
        else:
            error = "Invalid login"

        conn.close()

    return render_template("login.html", error=error)


# 📝 SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("INSERT INTO users VALUES (?,?,?)",
                    (request.form['email'], request.form['password'], request.form['name']))

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template("signup.html")


# 📊 DASHBOARD
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    global current_token

    if 'user' not in session:
        return redirect('/')

    email = session['user']

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT token FROM tokens WHERE email=?", (email,))
    data = cur.fetchone()

    user_token = data[0] if data else 0

    if request.method == 'POST':
        action = request.form.get("action")

        # 🎫 GET TOKEN
        if action == "get" and user_token == 0:
            cur.execute("SELECT MAX(token) FROM tokens")
            last = cur.fetchone()[0]
            new_token = 1 if last is None else last + 1

            cur.execute("INSERT INTO tokens VALUES (?,?)", (email, new_token))
            conn.commit()
            user_token = new_token

        # ❌ CANCEL TOKEN
        elif action == "cancel":
            cur.execute("DELETE FROM tokens WHERE email=?", (email,))
            conn.commit()
            user_token = 0

    people = max(user_token - current_token, 0)
    wait = people * 2

    status = "🟢 Waiting"
    if user_token == current_token and user_token != 0:
        status = "🔴 Your Turn Now!"
    elif user_token - current_token <= 2 and user_token != 0:
        status = "🟠 Your turn is near!"

    conn.close()

    return render_template("dashboard.html",
                           name=session.get('name'),
                           token=user_token,
                           current=current_token,
                           people=people,
                           wait=wait,
                           status=status)


# ⚙️ ADMIN
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global current_token

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == 'POST':
        current_token += 1

    cur.execute("SELECT COUNT(*) FROM tokens")
    total = cur.fetchone()[0]

    conn.close()

    return render_template("admin.html",
                           current=current_token,
                           total=total)


# 🚪 LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)