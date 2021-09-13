import os
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory, session, g
from werkzeug.utils import secure_filename
from app import webapp, pytorch_infer
import requests
import errno
from app.config import db_config
from functools import wraps

import mysql.connector
import boto3

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
       
def make_tree():
    cnx = get_db()

    cursor = cnx.cursor()
    query="""
        select imagepath, num_faces, num_masked, num_unmasked from images where userid = %s
        """
    cursor.execute(query, (int(session['uid']), ))
    
    #categorize all the images
    tree = {'no_faces':list(), 'all_masked':list(), 'all_unmasked':list(), 'some_masked':list()}
    for row in cursor:
        imagepath = row[0]
        num_faces = row[1]
        num_masked = row[2]
        num_unmasked = row[3]
        if num_faces == 0:
            tree['no_faces'].append(imagepath)
        elif num_faces == num_masked:
            tree['all_masked'].append(imagepath)
        elif num_faces == num_unmasked:
            tree['all_unmasked'].append(imagepath)
        else:
            tree['some_masked'].append(imagepath)
            
    return tree

def get_path(name):
    path = os.path.join(webapp.config["UPLOAD_FOLDER"], str(session['uid']), name)
    if not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    return path

@webapp.route('/upload',methods=['GET', 'POST'])
@login_required
def upload_image():
    if request.method == 'POST':
        if request.form.get('Upload Via Browse'):
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(get_path(filename))
                return redirect(url_for('mask_detection', name = filename))
                
        elif request.form.get('Upload Via URL'):
            url = request.form.get('url',"")
            if url == '':
                flash('No selected file')
                return redirect(request.url)
            elif not allowed_file(url.split('/')[-1]):
                flash('url should end with extension png, jpeg...')
                return redirect(request.url)
            r = requests.get(url)

            # write to a file in the app's instance folder
            # come up with a better file name
            filename = url.split('/')[-1]
            with open(get_path(filename), 'wb') as f:
                f.write(r.content)
                return redirect(url_for('mask_detection', name = filename))

    user = session['user']
    if user == 'admin':
        return render_template("Return_to_admin.html", user=user)

    return render_template("main.html", user=user)

@webapp.route('/list_images')
@login_required
def list_images():
    return render_template('list_images.html', tree=make_tree())

@webapp.route('/show_image/<name>')
@login_required
def show_image(name):
    cnx = get_db()

    cursor = cnx.cursor()
    query="""
        select num_faces, num_masked, num_unmasked from images where userid = %s and imagepath = %s
        """
    path = str(session['uid']) + '/' + name
    cursor.execute(query, (int(session['uid']), name))
    row = list(cursor)[0]
    num_faces = row[0]
    num_masked = row[1]
    num_unmasked = row[2]
    
    download_path = get_path(name)
    s3 = boto3.client('s3')
    s3.download_file(webapp.config["BUCKET_NAME"], download_path, download_path)
    return render_template("mask_detection.html", num_faces=num_faces, num_masked=num_masked, num_unmasked=num_unmasked, image=path)

@webapp.route('/mask_detection/<name>')
@login_required
def mask_detection(name):
    output = pytorch_infer.pytorch_infer(get_path(name))
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
    cursor.execute(query, (int(session['uid']), name, num_faces, num_masked, num_unmasked))
    cnx.commit()
    
    return show_image(name)
