from flask import render_template, g, request, redirect, flash, session, url_for
from app import webapp, mail, authenticate
from flask_mail import Message
import mysql.connector
import jwt
import datetime
from app.config import db_config
from functools import wraps

def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   passwd=db_config['password'],
                                   host=db_config['host'],
                                   port=db_config['port'],
                                   database=db_config['database']
                                   )

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def login_wrap(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'uid' in session and session['loggedin'] is True:
            return redirect(url_for('do_profile'))
        else:
            return f(*args, **kwargs)
    return wrap

@webapp.route('/login', methods=['GET'])
@webapp.route('/', methods=['GET'])
@login_wrap
def login_form():
    return render_template("login.html")

@webapp.route('/login', methods=['POST'])
def do_login():
    user = request.form.get("username")
    pw = request.form.get("pw")

    cnx = get_db()
    cursor = cnx.cursor()
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (user,))

    result = cursor.fetchall()
    if (not result):
        flash("Incorrect Username. Please try again.", "loginerror")
        return redirect('/login')
    else:
        #should be exactly one, else something wrong when init db
        n_result = len(result)
        if n_result != 1:
            flash("number of username is " + str(n_result), "loginerror")
            return redirect('/login')
        db_pw = result[0][2]
        db_salt = result[0][3]
        encrypt_pw = authenticate.encrypt_to_hex(pw, db_salt)
        if encrypt_pw == db_pw:
            session['user'] = user
            session['uid'] = result[0][0]
            session['loggedin'] = True
            session.permanent = True
            if user == 'admin':
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('upload_image'))
        else:
            flash("Incorrect Password. Please try again.", "loginerror")
            return redirect('/login')

@webapp.route('/api/recoverpw', methods=['POST'])
def recoverpw():

    username = request.form.get("r_username")
    root_url = request.url_root

    cnx = get_db()
    cursor = cnx.cursor()
    query = """
    SELECT COUNT(id) FROM users WHERE username = %s
    """
    cursor.execute(query, (username, ))
    result = cursor.fetchone()
    if (result[0] == 0):
        flash("Username does not exist.", "error")
        return redirect(url_for('recoverypage'))

    query = """
    SELECT email FROM users WHERE username = %s
    """
    cursor.execute(query, (username, ))
    result = cursor.fetchone()
    if (result[0] is not None):
        encoded_jwt = jwt.encode(
            {
                "username": username,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
            },
            webapp.secret_key,
            algorithm='HS256'
        )
        print(root_url)
        url_gen = root_url + 'resetpage' + '?' + 'token=' + encoded_jwt
        print("generating recovery email with link: \n"+ url_gen)

        msg = Message('PW recover email - ece1779',
                      sender= webapp.config['MAIL_USERNAME'],
                      recipients=[result[0]])

        msg.html = render_template('email_body.html', url_gen = url_gen)
        try:
            mail.send(msg)
        except:
            flash("Recovery email sent to " + result[0] + " failed", "error")
            return redirect(url_for('recoverypage'))

        flash("Recovery email sent to " + result[0] + ". Link will expires in 5 min", "error")
        return redirect(url_for('recoverypage'))
    else:
        flash("User does not have an email.", "error")
        return redirect(url_for('recoverypage'))

def token_check_wrap(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            flash("missing token", "error")
            return redirect(url_for('do_login'))
        try:
            data = jwt.decode(token, webapp.secret_key, algorithms="HS256")
        except jwt.exceptions.ExpiredSignatureError:
            flash("expired token", "error")
            return redirect(url_for('do_login'))
        except:
            flash("invalid token", "error")
            return redirect(url_for('do_login'))
        return f(*args, data=data, **kwargs)
    return wrap


@webapp.route('/resetpage', methods=['GET'])
@token_check_wrap
def resetpage(data=None):
    user = data['username']
    return render_template('resetpw.html', user=user)

@webapp.route('/resetpw/<username>', methods=['POST'])
def do_resetpw(username):
    n_pw = request.form.get("new_pw")
    if not n_pw:
        flash("pw cannot be empty")
        return redirect(url_for('resetpage'))

    n_salt = authenticate.gen_salt()
    encrypt_pw = authenticate.encrypt_to_hex(n_pw, n_salt)

    cnx = get_db()
    cursor = cnx.cursor()
    query = """
        UPDATE users SET password = %s, pwsalt = %s WHERE username = %s
        """
    cursor.execute(query, (encrypt_pw, n_salt, username,))
    cnx.commit()
    #flash("Password Successfully Changed", "error")
    return redirect(url_for('do_login'))

@webapp.route('/recoverypage', methods=['GET'])
@login_wrap
def recoverypage():
    return render_template('recoverpw.html')

