import boto3

def getInfo():
    ec2 = boto3.resource("ec2")
    elbv2 = boto3.client("elbv2")
    ec2client = boto3.client("ec2")

    vpclist = list(ec2.vpcs.all())
    print("VPC:")
    printlist(vpclist)
    print("\n")

    subnetlist = list(ec2.subnets.all())
    print("ALL VPC Subnets:")
    printlist(subnetlist)
    print("\n")

    isglist = list(ec2.security_groups.all())
    print("ALL Security Groups:")
    printlist(isglist)
    print("\n")


def printlist(input: list):
    for item in input:
        print(item)

if __name__ == "__main__":
    getInfo()
