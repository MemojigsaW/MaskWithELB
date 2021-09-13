
from flask import Flask
from flask_mail import Mail
import os

from app import config as cfg

UPLOAD_FOLDER = cfg.IMG_PATH
webapp = Flask(__name__, static_folder=UPLOAD_FOLDER)

webapp.secret_key = cfg.SECRET_KEY
webapp.permanent_session_lifetime = cfg.SESSION_TIME
webapp.config['BUCKET_NAME'] = cfg.BUCKET_NAME
webapp.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
webapp.config['TEMPLATES_AUTO_RELOAD'] = True
webapp.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

webapp.config['MAIL_SERVER']=cfg.MAIL_SERVER
webapp.config['MAIL_PORT'] = cfg.MAIL_PORT
webapp.config['MAIL_USERNAME'] = cfg.MAIL_USERNAME
webapp.config['MAIL_PASSWORD'] = cfg.MAIL_PASSWORD
webapp.config['MAIL_USE_TLS'] = cfg.MAIL_USE_TLS
webapp.config['MAIL_USE_SSL'] = cfg.MAIL_USE_SSL

mail = Mail()
mail.init_app(webapp)


from app import mask_detection
from app import main
from app import pytorch_infer

from app import login
from app import profile
from app import admin
