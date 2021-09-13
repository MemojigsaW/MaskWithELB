import boto3
import datetime
from datetime import timedelta
import pytz
import Instance_util
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from operator import itemgetter


run_util = Instance_util.AWSValues()
# y_cpu, x_time = run_util.cpu_data_30()
# y_cpu, x_time = run_util.new_cpu_data(y_cpu, x_time)
#
# def cpu(i):
#     plt.cla()
#     plt.plot(x_time, y_cpu)
#     plt.tight_layout()
#     plt.xlabel('Time (GMT)')
#     plt.ylabel('Percent CPU Usage')
#     plt.xticks(np.arange(0, len(x_time) + 1, 3))
#
# ani = FuncAnimation(plt.gcf(), cpu, interval=60000)
# plt.tight_layout()
# plt.show()

workers = run_util.get_Running_Workers()
y_cpu = []
x_time = []

for i in range(1, 30):
    cpu_utilization = 0
    for workerId in workers:
        cpu_utilization += run_util.get_CPU_Utilization(workerId, (60*(30-i)))
        cpu_utilization /= len(workers)
        y_cpu.append(cpu_utilization)
        now = datetime.datetime.now(pytz.timezone("UTC"))-timedelta(seconds=(60*(30-i)))
        x_time.append(datetime.datetime.strftime(now, '%H:%M'))


def cpu(i):
    cpu_utilization = 0
    for workerId in workers:
        cpu_utilization += run_util.get_CPU_Utilization(workerId, 120)
        cpu_utilization /= len(workers)
        y_cpu.append(cpu_utilization)
        now2 = datetime.datetime.now(pytz.timezone("UTC"))
        x_time.append(datetime.datetime.strftime(now2, '%H:%M'))
        y_cpu.pop(0)
        x_time.pop(0)
    plt.cla()
    plt.plot(x_time, y_cpu)
    plt.tight_layout()
    plt.xlabel('Time (GMT)')
    plt.ylabel('Percent CPU Usage')
    plt.xticks(np.arange(0, len(x_time) + 1, 3))


ani = FuncAnimation(plt.gcf(), cpu, interval=60000)
plt.tight_layout()
plt.show()


# client = boto3.client('cloudwatch')
# instance_id = 'i-062d723a6e0ecacc8'
#
# current_time = datetime.datetime.now(pytz.timezone("UTC"))
#
# end_time = current_time
# start_time = current_time - timedelta(seconds=120)
#
# response = client.get_metric_statistics(
#     Namespace='AWS/EC2',
#     MetricName='CPUUtilization',
#     Dimensions=[
#         {
#             'Name': 'InstanceId',
#             'Value': instance_id
#         },
#     ],
#     StartTime=start_time,
#     EndTime=end_time,
#     Period=60,
#     Statistics=[
#         'Average',
#     ],
#     Unit='Percent'
# )
# print(response)
#
# for k, v in response.items():
#     if k == 'Datapoints':
#         for y in v:
#             print(y['Average'])
#
#
# cpu_stats = []
#
# for point in response['Datapoints']:
#     hour = point['Timestamp'].hour
#     minute = point['Timestamp'].minute
#     time = hour + minute / 60
#     cpu_stats.append([time, point['Average']])
#
# cpu_stats = sorted(cpu_stats, key=itemgetter(0))
# print(cpu_stats)

# client = boto3.client('cloudwatch')
# ec2 = boto3.resource('ec2')
#
# current_time = datetime.datetime.now(pytz.timezone("UTC"))
#
# end_time = current_time
# start_time = current_time - timedelta(seconds=30*60)
# instance_id = 'i-062d723a6e0ecacc8'
# instance = ec2.Instance(instance_id)
#
# cpu = client.get_metric_statistics(
#     Namespace='AWS/EC2',
#     MetricName='CPUUtilization',
#     Dimensions=[
#         {
#             'Name': 'InstanceId',
#             'Value': instance_id
#         },
#     ],
#     StartTime=start_time,
#     EndTime=end_time,
#     Period=60,
#     Statistics=[
#         'Average',
#     ],
#     Unit='Percent'
# )

# cpu_stats = []
#
# for point in cpu['Datapoints']:
#     hour = point['Timestamp'].hour
#     minute = point['Timestamp'].minute
#     time = hour + minute / 60
#     cpu_stats.append([time, point['Average']])
#
# cpu_stats = sorted(cpu_stats, key=itemgetter(0))
