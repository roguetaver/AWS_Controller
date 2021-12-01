import boto3
from botocore.config import Config

# =====================================================================================================================

# =====================================================================================================================

Security_IP_Database = [
    {
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'IpRanges': [
            {'CidrIp': '0.0.0.0/0'}
        ]
    },
    {
        'IpProtocol': 'tcp',
        'FromPort': 5432,
        'ToPort': 5432,
        'IpRanges': [
            {'CidrIp': '0.0.0.0/0'}
        ]
    },
    {
        'FromPort': 80,
        'ToPort': 80,
        'IpProtocol': 'tcp',
        'IpRanges': [
            {'CidrIp': '0.0.0.0/0'},
        ],
    },
]

Security_IP_Django = [
    {
        'IpProtocol': 'tcp',
        'FromPort': 22,
        'ToPort': 22,
        'IpRanges': [
            {'CidrIp': '0.0.0.0/0'}
        ]
    },
    {
        'IpProtocol': 'tcp',
        'FromPort': 8080,
        'ToPort': 8080,
        'IpRanges': [
            {'CidrIp': '0.0.0.0/0'}
        ]
    },
    {
        'FromPort': 80,
        'ToPort': 80,
        'IpProtocol': 'tcp',
        'IpRanges': [
            {'CidrIp': '0.0.0.0/0'},
        ],
    },
]

# =====================================================================================================================

# =====================================================================================================================


def create_sec_group(client, name, sec_rules):
    vpcs = client.describe_vpcs()

    vpc_id = vpcs['Vpcs'][0]['VpcId']

    try:
        security_group = client.create_security_group(
            GroupName=name, Description="f", VpcId=vpc_id)
    except Exception as error:
        print(error)

    sec_group_id = security_group['GroupId']

    client.authorize_security_group_ingress(
        GroupId=sec_group_id, IpPermissions=sec_rules)

    print(f"Security Group {name} created")

    return sec_group_id

# =====================================================================================================================


def delete_sec_group(client, sec_group_name):
    find_sec_group = False
    security_groups = client.describe_security_groups()
    for sec_group in security_groups['SecurityGroups']:
        if sec_group['GroupName'] == sec_group_name:
            find_sec_group = True

            deleted_sec_group = client.delete_security_group(
                GroupName=sec_group["GroupName"], GroupId=sec_group["GroupId"])
    if find_sec_group:
        print(f"{sec_group_name} deleted")
    else:
        print(f"{sec_group_name} not found")

# =====================================================================================================================


def create_instance(region, machine_id, security_group, script, name: str):

    try:
        region = Config(region_name=region)
        resource = boto3.resource("ec2", config=region)

        instance = resource.create_instances(
            ImageId=machine_id,
            MinCount=1,
            MaxCount=1,
            InstanceType="t2.micro",
            SecurityGroupIds=[security_group],
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": name
                        }
                    ]
                }
            ],
            UserData=script
        )
        print("####################################")
        print("Creating" + name + "Instance")
        print("####################################")
        instance[0].wait_until_running()
        instance[0].reload()
        print("####################################")
        print("Instance" + name + "successfully created")
        print("####################################")

        return instance, instance[0].public_ip_address

    except Exception as e:
        print("####################################")
        print("ERROR")
        print("####################################")
        print(e)
        return False

# =====================================================================================================================


def delete_all_instances(ec2, waiter):
    try:
        delete_instances_ids = []
        existing_instances = ec2.describe_instances()
        existing_instances = existing_instances["Reservations"]
        for instance in existing_instances:
            for i in instance["Instances"]:
                delete_instances_ids.append(i["InstanceId"])
        if len(delete_instances_ids) > 0:
            ec2.terminate_instances(InstanceIds=delete_instances_ids)
            print("####################################")
            print("deleting all instances...")
            print("####################################")
            waiter.wait(InstanceIds=delete_instances_ids)
            print("####################################")
            print("Instances deleted")
            print("####################################")
        else:
            print("####################################")
            print("No instances to delete")
            print("####################################")
            return
    except Exception as e:
        print("####################################")
        print("ERROR")
        print("####################################")
        print(e)

# =====================================================================================================================
