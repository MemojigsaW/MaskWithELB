from app import webapp, AutoScaling
import Instance_util
import config
from flask import render_template, flash, url_for, redirect, request, g
import ELB_util
import random
import threading
import boto3

import mysql.connector

def connect_to_database():
    return mysql.connector.connect(user=config.db_config['user'],
                                   passwd=config.db_config['password'],
                                   host=config.db_config['host'],
                                   port=config.db_config['port'],
                                   database=config.db_config['database']
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
        

@webapp.route('/', methods=['GET'])
def loadInstancePage():
    AutoScaling.startAutoScaler()
    run_util = Instance_util.AWSValues()
    ins_dict = run_util.get_All_Instances()

    instancelist = []
    for reservation in ins_dict['Reservations']:
        if len(reservation['Instances'][0]['SecurityGroups']) != 0 and reservation['Instances'][0]['ImageId']==config.AMI_USED:
            instancelist.append(reservation['Instances'][0])
    #print(instancelist)
    return render_template('InstancePage.html', instance_dict_list = instancelist)

@webapp.route('/api/createinstance', methods=['GET'])
def createInstance():
    run_util = Instance_util.AWSValues()
    number_of_instances = run_util.Number_of_Running_Instances()
    if number_of_instances < webapp.config['MAX_NUM_WORKERS']:
        thread = threading.Thread(target = addWorker, args=())
        thread.start()
        flash("Instance Created. " + str(number_of_instances+1) + " Instances are Running." + " Please Refresh the Page to View New Instance", "InstancePage_error")
    else:
        flash("8 Instances are already running.", "InstancePage_error")
    #flash(str(number_of_instances), "InstancePage_error")
    #flash("Not implemented", "InstancePage_error")
    return redirect(url_for('loadInstancePage'))

@webapp.route('/api/removeinstance/<id>', methods=['GET'])
def removeInstance(id):
    removeWorker(id)
    return redirect(url_for('loadInstancePage'))


@webapp.route('/api/cleardata', methods=['GET'])
def clearData():
    #clear all files from S3
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(config.BUCKET_NAME)
    for key in bucket.objects.all():
        key.delete()
    #truncate images table from RDS
    cnx = get_db()
    cursor = cnx.cursor()
    query="""
        truncate images
        """
    cursor.execute(query)
    #delete all rows in user table where username is not admin
    query = """
        delete from users where username <> 'admin'
        """
    cursor.execute(query)
    cnx.commit()
    
    return redirect(url_for('loadInstancePage'))

@webapp.route('/shutdown', methods=['GET'])
def shutdown():
    #shutdown autoscaler so it does not create instances in the background before the autoscaler is restarted
    AutoScaling.stopAutoScaler()
    #terminate all workers, despite running or not
    run_util = Instance_util.AWSValues()
    workers = run_util.get_All_Workers()
    for id in workers:
        removeWorker(id)
    #shutdown server
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the werkzeug server')
    func()
    return 'Manager app is shutdown'

def addWorker():
    print("addWorker is called")
    run_util = Instance_util.AWSValues()

    instances = run_util.create_Instance()
    assert (len(instances)==1)
    instance = instances[0]
    print("blocking, waiting to be running")
    instance.wait_until_running(DryRun=False)
    instance_status = run_util.get_instance_state(instance.id)
    print("unblocking, new status: ", instance_status['Name'])
    if (instance_status['Code']!=16):
        print("new instance failed to run after 40 checks, now terminating")
        run_util.terminate_Instance(instance.id)
    else:
        ELB_util.reg_instance_to_TG(instance.id)
        print("blocking, wait for in service, this takes forever 5+ min....")
        try:
            ELB_util.block_until_inservice(instance.id)
            print("unblocking, instance now in-service")
        except Exception as e:
            print("Excepting wait till-in-service", e)


def removeWorker(instanceId = None):
    print("removeWorker is called")
    run_util = Instance_util.AWSValues()
    if instanceId is None:
        workers = run_util.get_Running_Workers()
        # remove unhealthy worker first
        instanceId = None
        response = ELB_util.get_TargetsHealth()
        for TH in response['TargetHealthDescriptions']:
            if (TH['TargetHealth']['State'] not in {'healthy', 'initial'}):
                print("Found unhealthy: ", TH['Target']['Id'])
                instanceId = TH['Target']['Id']
                break
        if(instanceId==None):
            print("all healthy, randoming")
            instanceId = random.choice(workers)

    ELB_util.dereg_instance_from_TG(instanceId)
    print("blocking, till dereg")
    ELB_util.block_until_dereg(instanceId)
    print("unblocking, from dereg")
    run_util.terminate_Instance(instanceId)




