from flask import Flask
import config

webapp = Flask(__name__)
webapp.secret_key = config.SECRET_KEY

webapp.config['MAX_NUM_WORKERS'] = 8
webapp.config['MIN_NUM_WORKERS'] = 1
webapp.config['AUTO_SCALER_RUNNING'] = False
webapp.config['EXPAND_THRESHOLD'] = 80.0
webapp.config['SHRINK_THRESHOLD'] = 20.0
webapp.config['EXPAND_RATIO'] = 2.0
webapp.config['SHRINK_RATIO'] = 0.5

from app import InstancePage
from app import ELBV2Page
from app import Graphs
