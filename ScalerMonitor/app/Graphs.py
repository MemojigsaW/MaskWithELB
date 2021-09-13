from flask import render_template
from app import webapp, AutoScaling
import config
from operator import itemgetter
import Instance_util
import datetime
from datetime import timedelta
import pytz
import boto3


@webapp.route('/<id>', methods=['GET'])
def CPUgraph(id):
    run_util = Instance_util.AWSValues()
    instance_id = id
    AutoScaling.startAutoScaler()
    ins_dict = run_util.get_All_Instances()
    current_time = datetime.datetime.now(pytz.timezone("UTC"))
    client = boto3.client("cloudwatch")

    response = run_util.get_CPU_Utilization_all(instance_id, (60 * 30))

    cpu_stats = []

    for point in response['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + (minute / 60)
        cpu_stats.append([time, point['Average']])
    cpu_stats = sorted(cpu_stats, key=itemgetter(0))


    end_time = current_time
    start_time = current_time - timedelta(seconds=(30 * 60))

    http_request = client.get_metric_statistics(
        Period=60,
        StartTime=start_time,
        EndTime=end_time,
        MetricName='HTTPRequest',
        Namespace='Custom',
        Statistics=['Sum'],
        Dimensions=[
            {
                'Name': 'InstanceID',
                'Value': instance_id
            },
        ],
    )

    http_stats = []
    for point in http_request['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + (minute / 60)
        http_stats.append([time, point['Sum']])
    http_stats = sorted(http_stats, key=itemgetter(0))


    instancelist = []
    for reservation in ins_dict['Reservations']:
        if len(reservation['Instances'][0]['SecurityGroups']) != 0 and reservation['Instances'][0]['ImageId']==config.AMI_USED:
            instancelist.append(reservation['Instances'][0])

    return render_template("CPUGraph.html", cpu_stats=cpu_stats, http_stats=http_stats, instance_dict_list=instancelist)




