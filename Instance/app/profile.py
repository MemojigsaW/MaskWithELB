from flask import render_template, g, request, redirect, flash, session, url_for
from app import webapp, authenticate
import mysql.connector
from app.config import db_config
from functools import wraps
import gc

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


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'loggedin' in session:
            return f(*args, **kwargs)
        else:
            flash("Need to login", "error")
            return redirect('/login')
    return wrap

@webapp.route('/profile', methods=['GET'])
@login_required
def do_profile():
    uid = session['uid']
    user = session['user']
    cnx = get_db()
    cursor = cnx.cursor()
    query = """
    SELECT imagepath FROM images
    WHERE userid = %s
    """
    cursor.execute(query, (int(uid), ))
    return render_template('profile.html', cursor=cursor, user=user)

@webapp.route('/api/add_path', methods=['POST'])
def add_path():

    uid = session['uid']
    n_path = request.form.get("new_path")

    if not n_path:
        return redirect(url_for('do_profile'))

    cnx = get_db()
    cursor = cnx.cursor()
    query="""
    INSERT INTO images (userid, imagepath) VALUES (%s, %s)
    """
    cursor.execute(query, (int(uid), n_path))
    cnx.commit()

    return redirect(url_for('do_profile'))

@webapp.route('/api/change_pw', methods=['POST'])
def change_pw():
    uid = session['uid']
    n_pw = request.form.get("new_pw")
    if not n_pw:
        return redirect(url_for('do_profile'))

    n_salt = authenticate.gen_salt()
    encrypt_pw = authenticate.encrypt_to_hex(n_pw, n_salt)

    cnx = get_db()
    cursor = cnx.cursor()
    query="""
    UPDATE users SET password = %s, pwsalt = %s WHERE id = %s
    """
    cursor.execute(query, (encrypt_pw, n_salt, int(uid),))
    cnx.commit()
    flash("Password Changed", "info")
    return redirect(url_for('do_profile'))

@webapp.route('/api/logout', methods=['POST'])
@login_required
def do_logout():
    session.clear()
    gc.collect()
    return redirect('/login')

