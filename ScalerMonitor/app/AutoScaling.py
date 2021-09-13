from app import webapp, InstancePage
import Instance_util
from flask import render_template, flash, url_for, redirect, request
import math

import time
import threading

@webapp.route('/auto_scaling', methods=['GET', 'POST'])
def configureAutoScaler():
    startAutoScaler()
    if request.method == 'POST':
        expandThreshold = float(request.form.get('expandThreshold'))
        shrinkThreshold = float(request.form.get('shrinkThreshold'))
        expandRatio = float(request.form.get('expandRatio'))
        shrinkRatio = float(request.form.get('shrinkRatio'))
        
        if (expandThreshold < shrinkThreshold):
            flash('expand threshold should be greater than shrink threshold', 'thresholderror')
        elif (expandRatio < 1.0):
            flash('expand ratio should be greater than or equal to 1.0', 'ratioerror')
        elif (shrinkRatio > 1.0):
            flash('shrink ratio should be less than or equal to 1.0', 'ratioerror')
        else:
            webapp.config['EXPAND_THRESHOLD'] = expandThreshold
            webapp.config['SHRINK_THRESHOLD'] = shrinkThreshold
            webapp.config['EXPAND_RATIO'] = expandRatio
            webapp.config['SHRINK_RATIO'] = shrinkRatio

    return render_template('AutoScaling.html', expandThreshold = webapp.config['EXPAND_THRESHOLD'], shrinkThreshold = webapp.config['SHRINK_THRESHOLD'], expandRatio = webapp.config['EXPAND_RATIO'], shrinkRatio = webapp.config['SHRINK_RATIO'])

def startAutoScaler():
    if not webapp.config['AUTO_SCALER_RUNNING']:
        webapp.config['AUTO_SCALER_RUNNING'] = True
        thread = threading.Thread(target = AutoScaler, args=())
        thread.start()
    else:
        print("AutoScaler Already Started")
    
def AutoScaler():
    print("AutoScaler Starting")
    run_util = Instance_util.AWSValues()

    while webapp.config['AUTO_SCALER_RUNNING']:
        print("running one check of autoscaler")
        workers = run_util.get_Running_Workers()
        # if there are no workers, set the size of the pool to 1, and naively wait until it is running
        if (len(workers) == 0):
            print("Starting worker cause there are 0")
            InstancePage.addWorker()
            while len(workers) == 0:
                time.sleep(10)
                workers = run_util.get_Running_Workers()
            
        cpuUtilization = 0
        for workerId in workers:
            cpuUtilization += run_util.get_CPU_Utilization(workerId, 120)
        cpuUtilization /= len(workers)
        print('average over all workers in the past 2 minutes', cpuUtilization)
        
        if (cpuUtilization > webapp.config['EXPAND_THRESHOLD']):
            endNumWorker = min(math.ceil(webapp.config['EXPAND_RATIO'] * len(workers)), webapp.config['MAX_NUM_WORKERS'])
            numWorkerAdded = endNumWorker - len(workers)
            print("expanding, add workers: ", numWorkerAdded)
            for i in range(numWorkerAdded):
                InstancePage.addWorker()
        elif (cpuUtilization < webapp.config['SHRINK_THRESHOLD']):
            endNumWorker = max(math.ceil(webapp.config['SHRINK_RATIO'] * len(workers)), webapp.config['MIN_NUM_WORKERS'])
            numWorkerRemoved = len(workers) - endNumWorker
            print("shrinking, remove workers: ", numWorkerRemoved)
            for i in range(numWorkerRemoved):
                InstancePage.removeWorker()
        print("Expand t: ", webapp.config['EXPAND_THRESHOLD'],
              "\nShrink t: ", webapp.config['SHRINK_THRESHOLD'],
              "\nExpand r: ", webapp.config['EXPAND_RATIO'],
              "\nSrink r: ", webapp.config['SHRINK_RATIO'])
        print("AutoScaler wait 60s")
        time.sleep(60)

    print("AutoScaler is not running ")

def stopAutoScaler():
    webapp.config['AUTO_SCALER_RUNNING'] = False
    webapp.config['EXPAND_RATIO'] = 1
    webapp.config['SHRINK_RATIO'] = 1
