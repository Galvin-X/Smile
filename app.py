from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime


DB_NAME = "smile.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "@*#(!HbJ@#LKJyl,!@#*aSDd**)sHdgsC^ExA&^*@#L!@#uiyoy:EWzA)R(_IAO:SD<?xiVqH{}#@$)_#(@)_IqI!"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
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

    query = "SELECT id, name, description, volume, image, price FROM product"

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

@app.route('/addtocart/<productid>')
def addtocart(productid):
    userid = session['userid']
    timestamp = datetime.now()

    print(f"User {userid} would like to add {productid} to cart at {timestamp}")

    query = "INSERT INTO cart(id,userid,productid,timestamp) VALUES (NULL,?,?,?)"
    con = create_connection(DB_NAME)
    cur = con.cursor()

    # Catch insertion errors
    try:
        cur.execute(query, (userid, productid, timestamp))
    except sqlite3.IntegrityError as e:
        print(e)
        print("### PROBLEM INSERTING INTO DATABASE - FOREIGN KEY ###")
        con.close()
        return redirect('/menu?error=Something+went+wrong')

    con.commit()
    con.close()

    return redirect('/menu')

@app.route('/cart')
def render_cart():
    userid = session['userid']

    query = "SELECT productid FROM cart WHERE userid=?;"
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute(query, (userid, ))
    product_ids = cur.fetchall()

    for i in range(len(product_ids)):
        product_ids[i] = product_ids[i][0]
    print(product_ids)

    unique_product_ids = list(set(product_ids))

    for i in range(len(unique_product_ids)):
        product_count = product_ids.count(unique_product_ids[i])
        unique_product_ids[i] = [unique_product_ids[i], product_count]
    print(unique_product_ids)

    query = """SELECT name, price FROM product WHERE id = ?;"""
    for item in unique_product_ids:
        cur.execute(query, item[0])
        item_details = cur.fetchall()
        print(item_details)
        item.append(item_details[0][0])
        item.append(item_details[0][1])

    con.close()
    print(unique_product_ids)

    return render_template('cart.html', cart_data=unique_product_ids, logged_in=is_logged_in())


@app.route('/removefromcart/<productid>')
def remove_from_cart(productid):
    print(f"Remove: {productid}")

    query = "DELETE FROM cart WHERE productid=?;"
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute(query, (productid,))
    con.commit()
    con.close()

    return redirect('/cart')


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
