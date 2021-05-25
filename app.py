from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import MySQLdb.cursors
import re

app = Flask(__name__)
app.config['MAIL_DEBUG']= True
app.config['TESTING']= False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT']= 587
app.config['MAIL_USE_SSL']= False
app.config['MAIL_USE_TLS']= True
app.config['MAIL_USERNAME'] ='sender3564@gmail.com'
app.config['MAIL_PASSWORD'] = 'm12213443'
app.config['MAIL_DEFAULT_SENDER'] = 'sender3564@gmail.com'
app.config['MAIL_ASCII_ATTACHMENTS'] = False

mail=Mail(app)
# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'manu'


app.config['MYSQL_HOST'] = "remotemysql.com"   #'localhost'
app.config['MYSQL_USER'] = "NumC49VpHC"        #'root'
app.config['MYSQL_PASSWORD'] = "IcdaWkVloR"    #''
app.config['MYSQL_DB'] = "NumC49VpHC"          #'pythonlogin'

# Intialize MySQL
mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
                # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['balance'] = account['balance']
            session['monthly_limit'] = account['monthly_limit']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg='')

# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s,0,0)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

@app.route('/home', methods=['GET', 'POST'])
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor) #
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],)) #
        account = cursor.fetchone()#
        if request.method == 'POST' and 'addlimit' in request.form:
            addlimit = int(request.form['addlimit'])
            cursor.execute('UPDATE accounts SET monthly_limit=%s WHERE id = %s', (addlimit, session['id'],))
            mysql.connection.commit()
        return render_template('home.html', account=account) #username=session['username']
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
     # Output message if something goes wrong...
    msg = ''
    if 'loggedin' in session:
        if request.method == 'POST' and 'item' in request.form and 'cost' in request.form and 'date' in request.form:
            # Create variables for easy access
            item = request.form['item']
            cost = int(request.form['cost'])
            date = request.form['date']
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
            account = cursor.fetchone()
            
            if not item or not cost or not date:
                msg = 'Please fill out the form!'
            else:
                if account['monthly_limit'] > 0:
                    if  (account['monthly_limit'] - cost ) > 0 :
                        account['balance'] = account['balance'] + cost
                        account['monthly_limit'] = account['monthly_limit']-cost
                        cursor.execute('INSERT INTO expense VALUES (NULL, %s, %s, %s, %s)', ( session['id'], item, cost, date,))
                        cursor.execute('UPDATE accounts SET balance=%s WHERE id = %s', (account['balance'], session['id'],))
                        cursor.execute('UPDATE accounts SET monthly_limit=%s WHERE id = %s', ( account['monthly_limit'], session['id'],))
                        mysql.connection.commit()
                        msg = 'New Expense Updated!'
                    else:
                        account['balance'] = account['balance'] + cost
                        account['monthly_limit'] = account['monthly_limit']-cost
                        cursor.execute('INSERT INTO expense VALUES (NULL, %s, %s, %s, %s)', ( session['id'], item, cost, date,))
                        cursor.execute('UPDATE accounts SET balance=%s WHERE id = %s', (account['balance'], session['id'],))
                        cursor.execute('UPDATE accounts SET monthly_limit=%s WHERE id = %s', ( account['monthly_limit'], session['id'],))
                        mysql.connection.commit()
                        message=Message('You Reached Your monthly limit',  recipients=[account['email']])
                        mail.send(message)
                        msg = 'You reached your monthly limit!'
                else:
                    message=Message('You Reached Your monthly limit',  recipients=[account['email']])
                    mail.send(message)
                    msg = 'You reached your monthly limit!'
        elif request.method == 'POST':
            # Form is empty... (no POST data)
            msg = 'Please fill out the form!'   
    return render_template("expenses.html", msg=msg)

@app.route('/expenses_report')
def expenses_report():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT item, cost, date FROM expense WHERE id = %s', (session['id'],))
        account = cursor.fetchall(); #to get multipe row we use fetch all
    return render_template("expenses_report.html", account=account)

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(host ='0.0.0.0', debug = True, port = 8080)