import boto3
from botocore.config import Config

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


def create_sec_group(client, name, sec_rules):
    vpcs = client.describe_vpcs()

    vpc_id = vpcs['Vpcs'][0]['VpcId']

    try:
        security_group = client.create_security_group(
            GroupName=name, Description="f", VpcId=vpc_id)
    except Exception as error:
        print("-------------------------------------------------------------")
        print(error)
        print("-------------------------------------------------------------")

    sec_group_id = security_group['GroupId']

    client.authorize_security_group_ingress(
        GroupId=sec_group_id, IpPermissions=sec_rules)
    print("-------------------------------------------------------------")
    print(f"Security Group {name} created")
    print("-------------------------------------------------------------")

    return sec_group_id

# =====================================================================================================================


def create_instance(region, machine_id, security_group, script, name: str, ec2):

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
        print("-------------------------------------------------------------")
        print("Creating " + name)
        print(" . ")
        instance[0].wait_until_running()
        instance[0].reload()
        print(" . ")
        print(name + " successfully created")
        print("-------------------------------------------------------------")

        instanceIP = instance[0].public_ip_address

        ec2_instances = ec2.describe_instances()
        instances = ec2_instances["Reservations"]
        for instance in instances:
            for i in instance["Instances"]:
                if i["State"]["Name"] == "running":
                    for tag in i["Tags"]:
                        if tag["Value"] == name:
                            instanceID = i["InstanceId"]
                            print(f"DJANGO_ID: {instanceID}")

        return instance, instanceIP, instanceID

    except Exception as e:
        print("-------------------------------------------------------------")
        print("ERROR")
        print("-------------------------------------------------------------")
        print(e)
        return False


# =====================================================================================================================


def create_image(ec2, instance_id, waiter, name):
    try:
        ami_instance = ec2.create_image(
            Name=name,
            InstanceId=instance_id,
            NoReboot=False,
            TagSpecifications=[
                {
                    "ResourceType": "image",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": name
                        }
                    ]
                }
            ]
        )

        imageID = ami_instance['ImageId']

        print("-------------------------------------------------------------")
        print("Creating image")
        print(" . ")

        waiter.wait(ImageIds=[imageID])

        print(" . ")
        print("Image created!")
        print("-------------------------------------------------------------")

        return imageID

    except Exception as e:

        print("-------------------------------------------------------------")
        print("ERROR")
        print("-------------------------------------------------------------")
        print(e)

        return False

# =====================================================================================================================


def create_target_group(ec2_north_virginia, ec2_load_balancer, name):
    try:
        target_groups = ec2_north_virginia.describe_vpcs()
        vpc_id = target_groups["Vpcs"][0]["VpcId"]

        print("-------------------------------------------------------------")
        print("Creating target group...")
        print(" . ")

        target_group_created = ec2_load_balancer.create_target_group(
            Name=name,
            Protocol='HTTP',
            Port=8080,
            TargetType='instance',
            VpcId=vpc_id
        )

        new_target_group = target_group_created["TargetGroups"][0]["TargetGroupArn"]

        print(" . ")
        print("Target group created")
        print("-------------------------------------------------------------")

        return new_target_group

    except Exception as e:
        print("-------------------------------------------------------------")
        print("ERROR")
        print("-------------------------------------------------------------")
        print(e)
        return False

# =====================================================================================================================


def create_loadbalancer(client, ec2_load_balancer, security_group, waiter, name):
    try:
        subnets = client.describe_subnets()
        subnets_list = []
        for subnet in subnets["Subnets"]:
            subnets_list.append(subnet["SubnetId"])

        load_balancer = ec2_load_balancer.create_load_balancer(
            Name=name,
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
        print("Creating load balancer...")
        print(" . ")

        waiter.wait(LoadBalancerArns=[load_balancer_arn])
        print(" . ")
        print("load balancer Created!")
        print("-------------------------------------------------------------")

        return load_balancer, load_balancer_arn

    except Exception as e:

        print("-------------------------------------------------------------")
        print("ERROR")
        print("-------------------------------------------------------------")
        print(e)

        return False


# =====================================================================================================================


def create_launch_config_ami(ec2, ami_id, security_group, name):
    try:
        print("-------------------------------------------------------------")
        print("Launching AMI...")
        print(" . ")

        ec2.create_launch_configuration(
            LaunchConfigurationName=name,
            ImageId=ami_id,
            SecurityGroups=[security_group],
            InstanceType='t2.micro',
        )
        print(" . ")
        print("AMI Launched")
        print("-------------------------------------------------------------")

    except Exception as e:
        print("-------------------------------------------------------------")
        print("Error launching AMI")
        print("-------------------------------------------------------------")
        print(e)


# =====================================================================================================================


def create_auto_scalling(ec2_auto_scalling, ec2_north_virginia, target_group, autoScallingName, launchName):
    try:
        print("-------------------------------------------------------------")
        print("Launching auto scalling group...")
        print(" . ")
        list_all_zones = []
        all_zones = ec2_north_virginia.describe_availability_zones()
        for i in all_zones["AvailabilityZones"]:
            list_all_zones.append(i["ZoneName"])

        ec2_auto_scalling.create_auto_scaling_group(
            AutoScalingGroupName=autoScallingName,
            LaunchConfigurationName=launchName,
            MinSize=1,
            MaxSize=3,
            TargetGroupARNs=[target_group],
            AvailabilityZones=list_all_zones
        )
        print(" . ")
        print("Auto scalling group created")
        print("-------------------------------------------------------------")

    except Exception as e:
        print("-------------------------------------------------------------")
        print("Error creating Auto scalling group")
        print("-------------------------------------------------------------")
        print(e)


# =====================================================================================================================


def attach_load_balancer(ec2_auto_scalling, target_group_arn, autoScallingName):
    try:
        print("-------------------------------------------------------------")
        print("Attaching load balancer to target group...")
        print(" . ")

        ec2_auto_scalling.attach_load_balancer_target_groups(
            AutoScalingGroupName=autoScallingName,
            TargetGroupARNs=[
                target_group_arn
            ]
        )
        print(" . ")
        print("Load balancer attached successfully")
        print("-------------------------------------------------------------")
        return
    except Exception as e:
        print("-------------------------------------------------------------")
        print("ERROR")
        print("-------------------------------------------------------------")
        print(e)
        return False

# =====================================================================================================================


def create_listener(ec2, target_group, load_balancer):
    try:
        print("-------------------------------------------------------------")
        print("Creating listener...")
        print(" . ")
        ec2.create_listener(
            LoadBalancerArn=load_balancer,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': target_group
                }
            ]
        )
        print(" . ")
        print("Listener created")
        print("-------------------------------------------------------------")
    except Exception as e:
        print("-------------------------------------------------------------")
        print("Error creating listener")
        print("-------------------------------------------------------------")
        print(e)

# =====================================================================================================================


def create_auto_scalling_policy(ec2, target_group, load_balancer):
    try:
        print("-------------------------------------------------------------")
        print("Creating auto scalling policy...")
        print(" . ")
        load_balancer_name = load_balancer[load_balancer.find("app"):]
        target_group_name = target_group[target_group.find(
            "targetgroup"):]

        ec2.put_scaling_policy(
            AutoScalingGroupName="auto_scaling_group",
            PolicyName="TargetTrackingScaling",
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
        print("Policy created")
        print("-------------------------------------------------------------")
    except:
        print("-------------------------------------------------------------")
        print("Could not create policy")
        print("-------------------------------------------------------------")

# =====================================================================================================================
