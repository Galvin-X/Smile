from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt


DB_NAME = "smile.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "@*#(!HbJ@#LKJyl,!@#*aSDd**)sHdgsC^ExA&^*@#L!@#uiyoy:EWzA)R(_IAO:SD<?xiVqH{}#@$)_#(@)_IqI!"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None


@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in=is_logged_in())


@app.route('/menu')
def render_menu_page():
    con = create_connection(DB_NAME)

    query = "SELECT name, description, volume, image, price FROM product"

    cur = con.cursor()
    cur.execute(query)
    product_list = cur.fetchall()
    con.close()

    return render_template('menu.html', products=product_list, logged_in=is_logged_in())


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', logged_in=is_logged_in())


@app.   route('/login', methods=['GET', 'POST'])
def render_login_page():
    if is_logged_in():
        return redirect('/')

    if request.method == "POST":
        email = request.form['email'].strip().lower()
        pass1 = request.form['pass1'].strip()

        query = """SELECT id, fname, pass FROM customer WHERE email = ?"""
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            userid = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
        except IndexError:
            return redirect('/login?error=Email+or+password+incorrect')

        # Check hashed password against entered password

        if not bcrypt.check_password_hash(db_password, pass1):
            return redirect(request.referrer + '?error=Email+or+password+incorrect')

        #if db_password != pass1:
        #    return redirect('/login?error=Email+or+password+incorrect')

        session['email'] = email
        session['userid'] = userid
        session['firstname'] = firstname
        print(session)
        return redirect('/')
    return render_template('login.html', logged_in=is_logged_in())


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if is_logged_in():
        return redirect('/')

    if request.method == "POST":
        # Show form in console
        print(request.form)

        # Get data
        fname = request.form.get('fname').strip().title()
        lname = request.form.get('lname').strip().title()
        email = request.form.get('email').strip().lower()
        pass1 = request.form.get('pass1')
        pass2 = request.form.get('pass2')

        # Check passwords
        if pass1 != pass2:
            return redirect('/signup?error=Passwords+dont+match')

        if len(pass1) < 8:
            return redirect('/signup?error=Passwords+must+be+8+characters+or+more')

        # Hash Password
        hashed_pass = bcrypt.generate_password_hash(pass1)

        # Connect to DB
        con = create_connection(DB_NAME)

        query = "INSERT INTO customer(id, fname, lname, email, pass) VALUES(NULL,?,?,?,?)"

        # Execute query
        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_pass))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()

        return redirect('login')

    return render_template('signup.html', logged_in=is_logged_in())


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time!')


def is_logged_in():
    if session.get("email") is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


app.run(host='0.0.0.0', debug=True)
