import boto3
import config

class Initializer:
    def __init__(self, ISG=None, LSG=None, TGARN=None, ELBV2ARN=None, ELBV2DNS=None, LISARN=None):
        self.ec2client = boto3.client("ec2")
        self.elbv2client = boto3.client("elbv2")
        self.ISG_id = ISG
        self.LSG_id = LSG
        self.TG_ARN = TGARN
        self.ELBV2_ARN = ELBV2ARN
        self.ELBV2_DNS = ELBV2DNS
        self.LIS_ARN = LISARN
        self.initstatus = True

    def initialize(self):
        # Step1 Creating Security Group for instances and ELB
        if (not self.initInstanceSG()):
            print("initialize instance security group failed")
            self.initstatus = False
        else:
            print("initialize instance security group success")
        if (not self.initLoaderSG()):
            print("initialize loader security group failed")
            self.initstatus = False
        else:
            print("initialize loader security group success")
        if (not self.connectISG_LSG()):
            print("Connect Security Groups failed")
            self.initstatus = False
        else:
            print("Connect Security Groups success")

        # Step2 Create target groups
        if (not self.initTargetGroup()):
            print("create target group failed")
            self.initstatus = False
        else:
            print("Create target group success")

        # Step3 Create ELBV2 (Application Load Balancer)
        if (not self.initELBV2()):
            print("create ELBV2 failed")
            self.initstatus = False
        else:
            print("create ELBV2 success")

        # Step4 Add listener to ELBV2, default to routing all request to the only target group
        if (not self.addListener()):
            print("Add ELBV2 listener failed")
            self.initstatus = False
        else:
            print("Add ELBV2 listener (default http route all to target group) success")

        self.printKeyinfo()

    def initInstanceSG(self) -> bool:
        check = True
        try:
            response = self.ec2client.create_security_group(
                Description=config.ISG_DESCRIPTION,
                GroupName=config.ISG_NAME,
                VpcId=config.VPC_ID,
                DryRun=False
            )
            self.ISG_id = response['GroupId']
        except Exception as e:
            print("Security Group for instances exception:\n", e)
            check = False
        finally:
            return check

    def initLoaderSG(self) -> bool:
        check = True
        try:
            response = self.ec2client.create_security_group(
                Description=config.LSG_DESCRIPTION,
                GroupName=config.LSG_NAME,
                VpcId=config.VPC_ID,
                DryRun=False
            )
            self.LSG_id = response['GroupId']
        except Exception as e:
            print("Security Group for Loader exception:\n", e)
            check = False
        finally:
            return check

    def connectISG_LSG(self) -> bool:
        check = True
        try:
            # update instance group first, TCP 1024+, HTTP, SSH, HTTPS
            ISG_inbound_response = self.ec2client.authorize_security_group_ingress(
                DryRun=False,
                GroupId=self.ISG_id,
                IpPermissions=[
                    {'FromPort': 80,
                     'IpProtocol': 'tcp',
                     'IpRanges': [],
                     'Ipv6Ranges': [],
                     'PrefixListIds': [],
                     'ToPort': 80,
                     'UserIdGroupPairs': [
                         {'Description': 'http from ELb to instance',
                          'GroupId': self.LSG_id,
                          'UserId': config.USER_ID}
                     ]
                     },
                    {'FromPort': 22,
                     'IpProtocol': 'tcp',
                     'IpRanges': [
                         {'CidrIp': '0.0.0.0/0',
                          'Description': 'ssh tunnel'}],
                     'Ipv6Ranges': [
                         {'CidrIpv6': '::/0',
                          'Description': 'ssh tunnel'}],
                     'PrefixListIds': [],
                     'ToPort': 22,
                     'UserIdGroupPairs': []
                     },
                    {'FromPort': 443,
                     'IpProtocol': 'tcp',
                     'IpRanges': [],
                     'Ipv6Ranges': [],
                     'PrefixListIds': [],
                     'ToPort': 443,
                     'UserIdGroupPairs': [
                         {'Description': 'https from Elb to instance',
                          'GroupId': self.LSG_id,
                          'UserId': config.USER_ID}
                     ]
                     },
                    {'FromPort': 1024,
                     'IpProtocol': 'tcp',
                     'IpRanges': [],
                     'Ipv6Ranges': [],
                     'PrefixListIds': [],
                     'ToPort': 65535,
                     'UserIdGroupPairs': [
                         {'Description': ' custom TCP (1024+) Elb to instance',
                          'GroupId': self.LSG_id,
                          'UserId': config.USER_ID}]
                     }
                ]
            )

            ISG_outbound_response = self.ec2client.update_security_group_rule_descriptions_egress(
                DryRun=False,
                GroupId=self.ISG_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',
                        'IpRanges': [
                            {'CidrIp': '0.0.0.0/0'}
                        ],
                        'Ipv6Ranges': [],
                        'PrefixListIds': [],
                        'UserIdGroupPairs': []
                    }
                ]
            )

            LSG_inbound_response = self.ec2client.authorize_security_group_ingress(
                DryRun=False,
                GroupId=self.LSG_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                        'Ipv6Ranges': [],
                        'PrefixListIds': [],
                        'ToPort': 65535,
                        'UserIdGroupPairs': []
                    }
                ]
            )

            LSG_outbound_response = self.ec2client.authorize_security_group_egress(
                DryRun=False,
                GroupId=self.LSG_id,
                IpPermissions=[
                    {'FromPort': 80,
                     'IpProtocol': 'tcp',
                     'IpRanges': [],
                     'Ipv6Ranges': [],
                     'PrefixListIds': [],
                     'ToPort': 80,
                     'UserIdGroupPairs': [
                         {'Description': 'http ELB to instance',
                          'GroupId': self.ISG_id,
                          'UserId': config.USER_ID}]
                     },
                    {'FromPort': 443,
                     'IpProtocol': 'tcp',
                     'IpRanges': [],
                     'Ipv6Ranges': [],
                     'PrefixListIds': [],
                     'ToPort': 443,
                     'UserIdGroupPairs': [
                         {'Description': 'https ELB to instance ',
                          'GroupId': self.ISG_id,
                          'UserId': config.USER_ID}]},
                    {'FromPort': 1024,
                     'IpProtocol': 'tcp',
                     'IpRanges': [],
                     'Ipv6Ranges': [],
                     'PrefixListIds': [],
                     'ToPort': 65535,
                     'UserIdGroupPairs': [
                         {'Description': 'custom TCP (1024+) ELB to instance',
                          'GroupId': self.ISG_id,
                          'UserId': config.USER_ID}]
                     }
                ]
            )

            LSG_revokeoutbound_response = self.ec2client.revoke_security_group_egress(
                DryRun=False,
                GroupId=self.LSG_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
                        'Ipv6Ranges': [],
                        'PrefixListIds': [],
                        'UserIdGroupPairs': []
                    },
                ],
            )

            check = LSG_revokeoutbound_response['Return'] and check

        except Exception as e:
            print("Connect Security Group Exception:\n", e)
            check = False
        finally:
            return check

    def initTargetGroup(self) -> bool:
        check = True
        try:
            response = self.elbv2client.create_target_group(
                Name='A2-Loader-Instance-Target-Group',
                Protocol='HTTP',
                ProtocolVersion='HTTP1',
                Port=80,
                VpcId=config.VPC_ID,
                HealthCheckProtocol='HTTP',
                HealthCheckPort='traffic-port',
                HealthCheckEnabled=True,
                HealthCheckPath='/',
                HealthCheckIntervalSeconds=30,
                HealthCheckTimeoutSeconds=10,
                HealthyThresholdCount=5,
                UnhealthyThresholdCount=2,
                Matcher={
                    'HttpCode': '200',
                },
                TargetType='instance',
            )
            self.TG_ARN = response['TargetGroups'][0]['TargetGroupArn']
        except Exception as e:
            print("Target Group creation exception:\n", e)
            check = False
        finally:
            return check

    def initELBV2(self) -> bool:
        check = True
        try:
            response = self.elbv2client.create_load_balancer(
                Name=config.ELBV2_NAME,
                SecurityGroups=[
                    self.LSG_id,
                ],
                Subnets=config.VPC_SUBNETS,
                Scheme='internet-facing',
                Type='application',
                IpAddressType='ipv4',
            )
            # since only once to be created
            self.ELBV2_ARN = response['LoadBalancers'][0]['LoadBalancerArn']
            self.ELBV2_DNS = response['LoadBalancers'][0]['DNSName']
        except Exception as e:
            print("Load Balancer creation exception:\n", e)
            check = False
        finally:
            return check

    def addListener(self) -> bool:
        check = True
        try:
            response = self.elbv2client.create_listener(
                LoadBalancerArn=self.ELBV2_ARN,
                Protocol='HTTP',
                Port=80,
                DefaultActions=[
                    {'Type': 'forward',
                     'TargetGroupArn': self.TG_ARN,
                     'Order': 1,
                     'ForwardConfig': {'TargetGroups': [{
                         'TargetGroupArn': self.TG_ARN,
                         'Weight': 1}],
                         'TargetGroupStickinessConfig': {'Enabled': False}}}
                ],
            )
            #     Assume only one listener
            self.LIS_ARN = response['Listeners'][0]['ListenerArn']
        except Exception as e:
            print("Add ELBV2 Listener Exception, ", e)
            check = False
        finally:
            return check

    def printKeyinfo(self):
        if self.initstatus:
            print("initialization Successful")
            print("Copy to config.py\n")
            print("INSTANCE_SECURITY_GROUP=" + "\'" + self.ISG_id + '\'')
            print("ELB_SECURITY_GROUP=" + "\'" + self.LSG_id + "\'")
            print("TARGET_GROUP_ARN=" + "\'" + self.TG_ARN + "\'")
            print("ELB_ARN=" + "\'" + self.ELBV2_ARN + "\'")
            print("ELB_DNS=" + "\'" + self.ELBV2_DNS + "\'")
            print("LIS_ARN=" + "\'" + self.LIS_ARN + "\'")
            print("\n")
        else:
            print("\n")
            print("initialization Failed, Contact Alan")
            print("\n")


if __name__ == "__main__":
    # initscript = Initializer()
    # initscript.initialize()
    client = boto3.client("elbv2")
    response = client.modify_target_group(
        TargetGroupArn=config.TARGET_GROUP_ARN,
        HealthCheckIntervalSeconds=30,
        HealthCheckTimeoutSeconds=15,
        HealthyThresholdCount=2,
        UnhealthyThresholdCount=2,
    )
