import boto3

ec2 = boto3.client('ec2')
response = ec2.describe_instances()
print(response)

instances = []
for i in response['Reservations']:
    instances.append({
        'Id': i['Instances'][0]['InstanceId'],
        'State': i['Instances'][0]['State']['Name']
    })
#print(instances)

print('Instances that are running:')
for j in instances:
    if (j['State']) == 'running':
        print(j['Id'])

number_of_instances = 0
for k in instances:
    if (k['State']) == 'running':
        number_of_instances = number_of_instances + 1
print(number_of_instances)