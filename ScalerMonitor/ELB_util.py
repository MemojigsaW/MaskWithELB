
import boto3
import config

def get_listeners():
    client = boto3.client("elbv2")
    response = client.describe_listeners(
        LoadBalancerArn=config.ELB_ARN
    )
    return response

def get_ELBV2():
    client = boto3.client("elbv2")
    response = client.describe_load_balancers()
    return response

def get_TargetGroup():
    client = boto3.client("elbv2")
    response = client.describe_target_groups()
    return response

def get_TargetsHealth():
    client = boto3.client("elbv2")
    response = client.describe_target_health(
        TargetGroupArn=config.TARGET_GROUP_ARN
    )
    return response

def get_TargetHealth(instance_id:str):
    client=boto3.client("elbv2")
    response = client.describe_target_health(
        TargetGroupArn=config.TARGET_GROUP_ARN,
        Targets=[
            {
                'Id':instance_id
            }
        ]
    )
    return response

def reg_instance_to_TG(instance_id:str):
    client = boto3.client("elbv2")
    response = client.register_targets(
        TargetGroupArn=config.TARGET_GROUP_ARN,
        Targets=[
            {
                'Id': instance_id,
                'Port': config.FLASK_PORT
            },
        ]
    )
    print("reg instance to TG", instance_id)
    return response

def dereg_instance_from_TG(instance_id:str):
    client = boto3.client("elbv2")
    response = client.deregister_targets(
        TargetGroupArn=config.TARGET_GROUP_ARN,
        Targets=[
            {
                'Id': instance_id,
                'Port': config.FLASK_PORT,
            },
        ]
    )
    print("dereg instance to TG", instance_id)
    return response

def block_until_inservice(instance_id:str):
    client = boto3.client("elbv2")
    waiter = client.get_waiter('target_in_service')
    waiter.wait(
        TargetGroupArn=config.TARGET_GROUP_ARN,
        Targets=[
            {
                'Id':instance_id,
                'Port': config.FLASK_PORT
            }
        ],
        WaiterConfig={
            'Delay': config.INSERVICE_BLOCK_INTERVAL,
            'MaxAttempts':config.INSERVICE_BLOCK_ATTEMPTS
        }
    )

def block_until_dereg(instance_id:str):
    client=boto3.client("elbv2")
    waiter = client.get_waiter('target_deregistered')
    waiter.wait(
        TargetGroupArn=config.TARGET_GROUP_ARN,
        Targets=[
            {
                'Id': instance_id,
                # 'Port': config.FLASK_PORT
            },
        ],
    )


if __name__ == "__main__":
    pass
    # instance_id = "i-0e8f92316b340b7b0"
    #
    # reg_instance_to_TG(instance_id)
    # print("block reg")
    # block_until_inservice(instance_id)
    # print("unblock reg")
    # print(get_TargetHealth(instance_id))
    #
    # dereg_instance_from_TG(instance_id)
    # print("dereg block")
    # block_until_dereg(instance_id)
    # print("dereg unblock")




