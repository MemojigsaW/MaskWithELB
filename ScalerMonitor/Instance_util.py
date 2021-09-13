import boto3
import config
import datetime
from datetime import timedelta
import pytz



class AWSValues:
    def __init__(self):
        self.ec2client = boto3.client("ec2")
        self.cloudwatch = boto3.client("cloudwatch")
        self.ec2resource = boto3.resource('ec2')
        self.ami_id = config.AMI_USED
        self.instance_size = config.INSTANCE_TYPE
        self.key_name = config.PEM_KEY
        self.security_group = config.ISG_NAME
        #self.instance = instanceid

    def get_All_Instances(self):
        client = self.ec2client
        response = client.describe_instances(
            DryRun=False,
        )
        return response

    def get_Running_Workers(self):
        response = self.get_All_Instances()

        instances = []
        for i in response['Reservations']:
            instances.append({
                'Id': i['Instances'][0]['InstanceId'],
                'State': i['Instances'][0]['State']['Name'],
                'Image': i['Instances'][0]['ImageId']
            })
        #print(instances)

        workers = list()
        for j in instances:
            if (j['State']) == 'running' and j['Image'] == self.ami_id:
                workers.append(j['Id'])

        print('Workers that are running:', workers)


        return workers
    
    def get_All_Workers(self):
        response = self.get_All_Instances()

        instances = []
        for i in response['Reservations']:
            instances.append({
                'Id': i['Instances'][0]['InstanceId'],
                'State': i['Instances'][0]['State']['Name'],
                'Image': i['Instances'][0]['ImageId']
            })
        #print(instances)

        workers = list()
        for j in instances:
            if j['Image'] == self.ami_id:
                workers.append(j['Id'])

        print('All Workers despite running or not:', workers)


        return workers
        

    def Number_of_Running_Instances(self):
        response=self.get_All_Instances()

        instances = []
        for i in response['Reservations']:
            instances.append({
                'State': i['Instances'][0]['State']['Name']
            })

        number_of_instances = 0
        for k in instances:
            if (k['State']) == 'running':
                number_of_instances = number_of_instances + 1
        return number_of_instances


    def create_Instance(self):
        ec2 = self.ec2resource

        # create a new EC2 instance
        instances = ec2.create_instances(
            ImageId=config.AMI_USED,
            InstanceType=config.INSTANCE_TYPE,
            KeyName=config.PEM_KEY,
            MaxCount=1,
            MinCount=1,

            SecurityGroupIds=[
                config.INSTANCE_SECURITY_GROUP,
            ],
            Monitoring={'Enabled': True},
            UserData=config.USER_DATA,
            DryRun=False,
            IamInstanceProfile={'Name': config.IAM_ROLE_NAME}
        )

        print('1 instance created', instances)
        return instances

    def terminate_Instance(self, instanceId):
        print("terminates instance", instanceId)
        client = self.ec2client

        response = client.terminate_instances(InstanceIds = [instanceId])
        return response

    def get_CPU_Utilization(self, instance_id, delta):
        client = self.cloudwatch

        current_time = datetime.datetime.now(pytz.timezone("UTC"))

        end_time = current_time - timedelta(seconds=(delta-120))
        start_time = current_time - timedelta(seconds=delta)


        response = client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=[
                'Average',
            ],
            Unit='Percent'
        )

        sum = 0
        count = 0
        for k, v in response.items():
            if k == 'Datapoints':
                for y in v:
                    #print('average over 1 minute', y['Average'])
                    sum += y['Average']
                    count += 1

        if (count==0):
            return 0
        return sum/count

    def get_instance_state(self, instance_id:str):
        response=self.ec2client.describe_instance_status(
            InstanceIds=[
                instance_id
            ],
            DryRun=False,
            IncludeAllInstances=False,
        )
        return response['InstanceStatuses'][0]['InstanceState']

    def cpu_data_30(self):
        workers = self.get_Running_Workers()
        y_cpu = []
        x_time = []

        for i in range(1, 30):
            cpu_utilization = 0
            for workerId in workers:
                cpu_utilization += self.get_CPU_Utilization(workerId, (60 * (30 - i)))
                cpu_utilization /= len(workers)
                y_cpu.append(cpu_utilization)
                now = datetime.datetime.now(pytz.timezone("UTC")) - timedelta(seconds=(60 * (30 - i)))
                x_time.append(datetime.datetime.strftime(now, '%H:%M'))
        return y_cpu, x_time

    def new_cpu_data(self, y_cpu, x_time):
        workers = self.get_Running_Workers()
        cpu_utilization = 0
        for workerId in workers:
            cpu_utilization += self.get_CPU_Utilization(workerId, 120)
            cpu_utilization /= len(workers)
            y_cpu.append(cpu_utilization)
            now = datetime.datetime.now(pytz.timezone("UTC"))
            x_time.append(datetime.datetime.strftime(now, '%H:%M'))
            y_cpu.pop(0)
            x_time.pop(0)
        return (y_cpu, x_time)

    def get_CPU_Utilization_all(self, instance_id, start):
        client = self.cloudwatch

        current_time = datetime.datetime.now(pytz.timezone("UTC"))
        end_time = current_time
        start_time = current_time - timedelta(seconds=start)

        response = client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance_id
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=[
                'Average',
            ],
            Unit='Percent'
        )
        return response


if __name__ == "__main__":
    pass

