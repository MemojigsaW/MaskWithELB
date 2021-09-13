from flask import render_template, redirect, url_for, request, g, session, flash
from app import webapp
import mysql.connector
from app.config import db_config
from functools import wraps


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   port=db_config['port'],
                                   database=db_config['database'])

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


#@webapp.route('/upload_image', methods=['GET'])
#@login_required
#def main():
#    user = session['user']
#    if user =='admin':
#        return render_template("Return_to_admin.html", user=user)
#
#    else:
#        return render_template("main.html", user=user)



