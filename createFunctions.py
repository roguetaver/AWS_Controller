import boto3
import time
from botocore.config import Config
from request_functions import *

# =====================================================================================================================

security_group_IP_rules_database = [
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

security_group_IP_rules_django = [
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


def create_security_group(client, security_group_name, ip_rules):
    vpcs = client.describe_vpcs()

    vpc_id = vpcs['Vpcs'][0]['VpcId']

    try:
        security_group = client.create_security_group(
            GroupName=security_group_name,
            Description='F',
            VpcId=vpc_id
        )

    except Exception as e:
        print("-------------------------------------------------------------")
        print("Error creating " + security_group_name)
        logging.info("Error creating " + security_group_name)
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)
        return False

    security_group_id = security_group['GroupId']

    client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=ip_rules
    )

    print("-------------------------------------------------------------")
    print(security_group_name + " created")
    logging.info(security_group_name + " created")
    print("-------------------------------------------------------------")

    return security_group_id

# =====================================================================================================================


def create_instance(region, image_id, security_group, script, instance_name, ec2):

    try:
        region = Config(region_name=region)
        resource = boto3.resource("ec2", config=region)

        instance = resource.create_instances(
            KeyName="andre.tavernaro",
            ImageId=image_id,
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
                            "Value": instance_name
                        }
                    ]
                }
            ],
            UserData=script
        )

        print("-------------------------------------------------------------")
        print("Creating " + instance_name)
        logging.info("Creating " + instance_name)
        print(" . ")

        instance[0].wait_until_running()
        instance[0].reload()
        time.sleep(90)

        print(" . ")
        print(instance_name + " successfully created")
        logging.info(instance_name + " successfully created")
        print("-------------------------------------------------------------")

        instanceIP = instance[0].public_ip_address

        client_instances = ec2.describe_instances()
        instances = client_instances["Reservations"]
        for instance in instances:
            for i in instance["Instances"]:
                if i["State"]["Name"] == "running":
                    for tag in i["Tags"]:
                        if tag["Value"] == instance_name:
                            instanceID = i["InstanceId"]
                            print(
                                "-------------------------------------------------------------")
                            print("ID:" + instanceID)
                            logging.info("ID:" + instanceID)
                            print(
                                "-------------------------------------------------------------")

        return instance, instanceIP, instanceID

    except Exception as e:

        print("-------------------------------------------------------------")
        print("Error creating " + instance_name)
        logging.info("Error creating " + instance_name)
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)
        return False


# =====================================================================================================================


def create_image(ec2, instance_id, waiter, image_name):
    try:
        ami_instance = ec2.create_image(
            Name=image_name,
            InstanceId=instance_id,
            NoReboot=False,
            TagSpecifications=[
                {
                    "ResourceType": "image",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": image_name
                        }
                    ]
                }
            ]
        )

        imageID = ami_instance['ImageId']

        print("-------------------------------------------------------------")
        print("Creating " + image_name)
        logging.info("Creating " + image_name)
        print(" . ")

        waiter.wait(ImageIds=[imageID])

        print(" . ")
        print(image_name + " created!")
        logging.info(image_name + " created!")
        print("-------------------------------------------------------------")

        return imageID

    except Exception as e:

        print("-------------------------------------------------------------")
        print("Error creating " + image_name)
        logging.info("Error creating " + image_name)
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)

        return False

# =====================================================================================================================


def create_target_group(ec2_north_virginia, ec2_load_balancer, target_group_name):
    try:
        target_groups = ec2_north_virginia.describe_vpcs()
        vpc_id = target_groups["Vpcs"][0]["VpcId"]

        print("-------------------------------------------------------------")
        print("Creating  " + target_group_name)
        logging.info("Creating  " + target_group_name)
        print(" . ")

        target_group_created = ec2_load_balancer.create_target_group(
            Name=target_group_name,
            Protocol='HTTP',
            HealthCheckEnabled=True,
            HealthCheckProtocol='HTTP',
            HealthCheckPort='8080',
            HealthCheckPath='/admin/',
            Matcher={
                'HttpCode': '200,302',
            },
            Port=8080,
            TargetType='instance',
            VpcId=vpc_id
        )

        new_target_group = target_group_created["TargetGroups"][0]["TargetGroupArn"]

        print(" . ")
        print(target_group_name + " created")
        logging.info(target_group_name + " created")
        print("-------------------------------------------------------------")

        return new_target_group

    except Exception as e:

        print("-------------------------------------------------------------")
        print("Error creating " + target_group_name)
        logging.info("Error creating " + target_group_name)
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)
        return False

# =====================================================================================================================


def create_load_balancer(client, ec2_load_balancer, security_group, waiter, load_balancer_name):
    try:

        subnets = client.describe_subnets()
        subnets_list = []

        for subnet in subnets["Subnets"]:
            subnets_list.append(subnet["SubnetId"])

        load_balancer = ec2_load_balancer.create_load_balancer(
            Name=load_balancer_name,
            SecurityGroups=[security_group],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': 'Load_Balancer'
                }
            ],
            IpAddressType='ipv4',
            Subnets=subnets_list
        )

        load_balancer_arn = load_balancer['LoadBalancers'][0]['LoadBalancerArn']

        print("-------------------------------------------------------------")
        print("Creating " + load_balancer_name)
        logging.info("Creating " + load_balancer_name)
        print(" . ")

        waiter.wait(LoadBalancerArns=[load_balancer_arn])

        print(" . ")
        print(load_balancer_name + " created")
        logging.info(load_balancer_name + " created")
        print("-------------------------------------------------------------")

        return load_balancer, load_balancer_arn

    except Exception as e:

        print("-------------------------------------------------------------")
        print("Error creating " + load_balancer_name)
        logging.info("Error creating " + load_balancer_name)
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)

        return False


# =====================================================================================================================


def create_launch_config_ami(ec2, image_id, security_group, launch_config_name):
    try:
        print("-------------------------------------------------------------")
        print("Launching " + launch_config_name)
        logging.info("Launching " + launch_config_name)
        print(" . ")

        ec2.create_launch_configuration(
            LaunchConfigurationName=launch_config_name,
            ImageId=image_id,
            SecurityGroups=[security_group],
            InstanceType='t2.micro',
        )

        print(" . ")
        print(launch_config_name + " Launched")
        logging.info(launch_config_name + " Launched")
        print("-------------------------------------------------------------")

    except Exception as e:

        print("-------------------------------------------------------------")
        print("Error creating " + launch_config_name)
        logging.info("Error creating " + launch_config_name)
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)


# =====================================================================================================================


def create_auto_scalling(ec2_auto_scalling, ec2_north_virginia, target_group_arn, auto_scalling_Name, launch_config_Name):
    try:
        print("-------------------------------------------------------------")
        print("Launching " + auto_scalling_Name)
        logging.info("Launching " + auto_scalling_Name)
        print(" . ")

        all_zones_list = []
        zones = ec2_north_virginia.describe_availability_zones()

        for i in zones["AvailabilityZones"]:
            all_zones_list.append(i["ZoneName"])

        ec2_auto_scalling.create_auto_scaling_group(
            AutoScalingGroupName=auto_scalling_Name,
            LaunchConfigurationName=launch_config_Name,
            MinSize=1,
            MaxSize=3,
            TargetGroupARNs=[target_group_arn],
            AvailabilityZones=all_zones_list
        )

        print(" . ")
        print(auto_scalling_Name + " created")
        logging.info(auto_scalling_Name + " created")
        print("-------------------------------------------------------------")

    except Exception as e:
        print("-------------------------------------------------------------")
        print("Error creating " + auto_scalling_Name)
        logging.info("Error creating " + auto_scalling_Name)
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)


# =====================================================================================================================


def attach_load_balancer(ec2_auto_scalling, target_group_arn, auto_scalling_Name):
    try:
        print("-------------------------------------------------------------")
        print("Attaching " + auto_scalling_Name + "to target group")
        logging.info("Attaching " + auto_scalling_Name + "to target group")
        print(" . ")

        ec2_auto_scalling.attach_load_balancer_target_groups(
            AutoScalingGroupName=auto_scalling_Name,
            TargetGroupARNs=[
                target_group_arn
            ]
        )

        print(" . ")
        print(auto_scalling_Name + " attached successfully to target group")
        logging.info(auto_scalling_Name +
                     " attached successfully to target group")
        print("-------------------------------------------------------------")
        return

    except Exception as e:

        print("-------------------------------------------------------------")
        print("Error attaching " + auto_scalling_Name + "to target group")
        logging.info("Error attaching " +
                     auto_scalling_Name + "to target group")
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)
        return False

# =====================================================================================================================


def create_listener(ec2, target_group_arn, load_balancer):
    try:
        print("-------------------------------------------------------------")
        print("Creating listener...")
        logging.info("Creating listener...")
        print(" . ")

        ec2.create_listener(
            LoadBalancerArn=load_balancer,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': target_group_arn
                }
            ]
        )

        print(" . ")
        print("Listener created")
        logging.info("Listener created")
        print("-------------------------------------------------------------")

    except Exception as e:

        print("-------------------------------------------------------------")
        print("Error creating listener")
        logging.info("Error creating listener")
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)

# =====================================================================================================================


def create_auto_scalling_group_policy(client, target_group_arn, load_balancer_arn, auto_scaling_group_name, policy_name):
    try:
        print("-------------------------------------------------------------")
        print("Creating " + policy_name)
        logging.info("Creating " + policy_name)
        print(" . ")

        load_balancer_name = load_balancer_arn[load_balancer_arn.find("app"):]
        target_group_name = target_group_arn[target_group_arn.find(
            "targetgroup"):]

        client.put_scaling_policy(
            AutoScalingGroupName=auto_scaling_group_name,
            PolicyName=policy_name,
            PolicyType="TargetTrackingScaling",
            TargetTrackingConfiguration={
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": "ALBRequestCountPerTarget",
                    "ResourceLabel": f"{load_balancer_name}/{target_group_name}"
                },
                "TargetValue": 50
            }
        )

        print(" . ")
        print(policy_name + " created")
        logging.info(policy_name + " created")
        print("-------------------------------------------------------------")

    except:
        print("-------------------------------------------------------------")
        print("Error creating" + policy_name)
        logging.info("Error creating " + policy_name)
        print("-------------------------------------------------------------")

# =====================================================================================================================
