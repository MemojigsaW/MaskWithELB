import errno

from flask import render_template, g, session, flash, redirect, url_for, request, jsonify
from app import webapp, authenticate, pytorch_infer
import mysql.connector
from app.config import db_config
from functools import wraps
from werkzeug.utils import secure_filename
import os
import re

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

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if ('loggedin' in session) and (session['user']=='admin'):
            return f(*args, **kwargs)
        else:
            flash("Need to login as admin", "error")
            return redirect('/login')
    return wrap

@webapp.route('/admin',methods=['GET'])
@admin_required
def admin_page():
    cnx = get_db()

    cursor = cnx.cursor()
    query = "SELECT * FROM users"
    cursor.execute(query)

    return render_template("admin.html", cursor=cursor)

@webapp.route('/admin/api/adduser', methods=['POST'])
def add_user():
    n_user = request.form.get("n_username").strip()
    n_pw = request.form.get("n_pw").strip()
    n_email = request.form.get("n_email").strip()
    if (not n_user) or (not n_pw) or (not n_email):
        flash("one of the field is empty", "admin_error")
        return redirect(url_for("admin_page"))

    regex = '[^@]+@[^@]+\.[^@]+'
    if (re.match(regex, n_email) is None):
        flash("Invalid Email", "admin_error")
        return redirect(url_for("admin_page"))

    cnx = get_db()
    cursor = cnx.cursor()
    query = """
    SELECT * FROM users 
    WHERE username = %s 
    OR email = %s
    """
    cursor.execute(query, (n_user, n_email, ))
    result = cursor.fetchall()
    if (len(result)>0):
        flash("username or email already exist", "admin_error")
        return redirect(url_for("admin_page"))

    n_salt = authenticate.gen_salt()
    encrypt_pw = authenticate.encrypt_to_hex(n_pw, n_salt)

    query = """
    INSERT INTO users (username, password, pwsalt, email) VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (n_user, encrypt_pw, n_salt, n_email))
    cnx.commit()
    flash("New User Created", "admin_error")
    return redirect(url_for("admin_page"))

@webapp.route('/admin/api/viewimg/<int:id>', methods=['GET'])
def view_user_img(id):
    cnx = get_db()

    cursor = cnx.cursor()
    query = """
        SELECT * FROM images
        WHERE userid = %s
        """
    cursor.execute(query, (int(id),))

    images = []
    for item in cursor:
        images.append(item)

    query = "SELECT * FROM users"
    cursor.execute(query)

    return render_template('admin_view_img_stub.html', cursor = cursor, images=images)

@webapp.route('/admin/api/delete/<int:id>', methods=['POST'])
def delete_user(id):
    cnx = get_db()
    cursor = cnx.cursor()
    query = """
    DELETE FROM users WHERE id = %s
    """
    cursor.execute(query, (int(id), ))

    # since on delete cascades
    # query = """
    # DELETE FROM images WHERE userid = %s
    # """
    # cursor.execute(query, (int(id), ))
    cnx.commit()

    return redirect(url_for('admin_page'))


@webapp.route('/api/register', methods=['POST'])
def testing_add_user():
    if 'username' not in request.form or 'password' not in request.form:
        msg = {
            'success':'false',
            'error':{
                'code': 422,
                'message': 'missing parameter'
            }
        }
    else:
        n_username = request.form.get('username').strip()
        n_pw = request.form.get('password').strip()

        if (not n_username) or (not n_pw):
            msg = {
                'success': 'false',
                'error': {
                    'code': 401,
                    'message': 'empty username or pw'
                }
            }
            return jsonify(msg)

        #check if username is duplicate
        cnx = get_db()
        cursor = cnx.cursor()
        query = """
        SELECT COUNT(id) FROM users WHERE username = %s
        """
        cursor.execute(query, (n_username, ))
        result = cursor.fetchone()
        if result[0] >0:
            msg = {
                'success': 'false',
                'error': {
                    'code': 401,
                    'message': 'duplicate username'
                }
            }
        else:
            n_salt = authenticate.gen_salt()
            encrypt_pw = authenticate.encrypt_to_hex(n_pw, n_salt)

            query = """
                INSERT INTO users (username, password, pwsalt) VALUES (%s, %s, %s)
                """
            cursor.execute(query, (n_username, encrypt_pw, n_salt))
            cnx.commit()
            msg = {'success': 'true'}
    return jsonify(msg)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@webapp.route('/api/upload', methods=['POST'])
def testing_upload():
    if 'username' not in request.form or 'password' not in request.form or 'file' not in request.files:
        msg = {
            'success':'false',
            'error':{
                'code': 422,
                'message': 'missing parameter'
            }
        }
    else:
        n_username = request.form.get('username').strip()
        pw = request.form.get('password').strip()
        file = request.files['file']

        if (not n_username) or (not pw):
            msg = {
                'success': 'false',
                'error': {
                    'code': 401,
                    'message': 'empty username or pw'
                }
            }
            return jsonify(msg)

        cnx = get_db()
        cursor = cnx.cursor()
        query = """
        SELECT * FROM users WHERE username = %s
        """
        cursor.execute(query, (n_username, ))
        result = cursor.fetchone()
        if result is None:
            msg = {
                'success': 'false',
                'error': {
                    'code': 401,
                    'message': 'username does not exist'
                }
            }
            return jsonify(msg)

        salt = result[3]
        encrypt_pw = authenticate.encrypt_to_hex(pw, salt)
        if encrypt_pw != result[2]:
            msg = {
                'success': 'false',
                'error': {
                    'code': 401,
                    'message': 'pw incorrect'
                }
            }
            return jsonify(msg)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            query = """
                SELECT id FROM users WHERE username = %s
                """
            cursor.execute(query, (n_username,))
            row = cursor.fetchone()
            uid = row[0]
            path = os.path.join(webapp.config["UPLOAD_FOLDER"], str(uid), filename)
            if not os.path.exists(os.path.dirname(path)):
                try:
                    os.makedirs(os.path.dirname(path))
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

            file.save(path)

            output = pytorch_infer.pytorch_infer(path)
            num_faces = len(output)
            num_masked = 0
            num_unmasked = 0
            for info in output:
                if (info[0]==0):
                    num_masked+=1
                else:
                    num_unmasked+=1
                    
            # store image info into db
            cnx = get_db()

            cursor = cnx.cursor()
            query="""
                INSERT INTO images (userid, imagepath, num_faces, num_masked, num_unmasked) VALUES (%s, %s, %s, %s, %s)
                """
            cursor.execute(query, (int(uid), filename, num_faces, num_masked, num_unmasked))
            cnx.commit()
            msg = {'success': 'true',
                   'payload' : {
                       'num_faces' : num_faces,
                       'num_masked' : num_masked,
                       'num_unmasked' : num_unmasked}
                   }
        else:
            msg = {
                'success': 'false',
                'error': {
                    'code': 401,
                    'message': 'file format not supported'
                }
            }
    return jsonify(msg)
