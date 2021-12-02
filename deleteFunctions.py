import boto3
from botocore.config import Config


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
        print("-------------------------------------------------------------")
        print(f"{sec_group_name} deleted")
        print("-------------------------------------------------------------")
    else:
        print("-------------------------------------------------------------")
        print(f"{sec_group_name} not found")
        print("-------------------------------------------------------------")

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
            print("-------------------------------------------------------------")
            print("deleting all instances...")
            print(" . ")
            waiter.wait(InstanceIds=delete_instances_ids)
            print(" . ")
            print("Instances deleted")
            print("-------------------------------------------------------------")
        else:
            print("-------------------------------------------------------------")
            print("No instances to delete")
            print("-------------------------------------------------------------")
            return
    except Exception as e:
        print("-------------------------------------------------------------")
        print("ERROR")
        print("-------------------------------------------------------------")
        print(e)

# =====================================================================================================================


def delete_image(ec2, image_name):
    images_described = ec2.describe_images(Filters=[
        {
            'Name': 'name',
            'Values': [
                image_name,
            ]
        },
    ])
    if len(images_described['Images']) < 1:
        print("-------------------------------------------------------------")
        print(f"There is no image with name {image_name}")
        print("-------------------------------------------------------------")
        return
    else:
        image_id = images_described['Images'][0]['ImageId']
        ec2.deregister_image(ImageId=image_id)
        print("-------------------------------------------------------------")
        print(f"Image {image_name} deleted")
        print("-------------------------------------------------------------")

# =====================================================================================================================


def delete_target_group(client_lb, tg_name):
    try:
        tgs = client_lb.describe_target_groups(Names=[tg_name])
    except:
        print("-------------------------------------------------------------")
        print(f"No target group with name {tg_name}")
        print("-------------------------------------------------------------")
        return
    tg_arn = tgs['TargetGroups'][0]['TargetGroupArn']
    client_lb.delete_target_group(TargetGroupArn=tg_arn)
    print("-------------------------------------------------------------")
    print(f"Target Group {tg_name} deleted")
    print("-------------------------------------------------------------")

# =====================================================================================================================


def delete_load_balancer(client_lb, lb_name):
    waiter = client_lb.get_waiter('load_balancers_deleted')
    try:
        load_balancers = client_lb.describe_load_balancers(Names=[lb_name])
    except:
        print("-------------------------------------------------------------")
        print(f"No load_balancers with name {lb_name}")
        print("-------------------------------------------------------------")
        return
    for lb in load_balancers['LoadBalancers']:
        client_lb.delete_load_balancer(LoadBalancerArn=lb['LoadBalancerArn'])
        lb_arn = lb['LoadBalancerArn']

    print("-------------------------------------------------------------")
    print(f"Load Balancer with name {lb_name} deleted")
    print("-------------------------------------------------------------")
    return lb_arn

# =====================================================================================================================


def delete_launch_configuration(as_client, launch_config_name):
    try:
        print("-------------------------------------------------------------")
        print("deleting launch configuration")
        print(" . ")

        as_client.delete_launch_configuration(
            LaunchConfigurationName=launch_config_name
        )
        print(" . ")
        print("launch configuration deleted")
        print("-------------------------------------------------------------")
    except:
        print("-------------------------------------------------------------")
        print("launch configuration not found")
        print("-------------------------------------------------------------")
        return

# =====================================================================================================================


def delete_auto_scalling(ec2, name):
    try:
        print("-------------------------------------------------------------")
        print("Deleting auto scalling group...")
        print(" . ")

        ec2.delete_auto_scaling_group(
            AutoScalingGroupName=name,
            ForceDelete=True
        )
        print(" . ")
        print("Auto scalling group deleted")
        print("-------------------------------------------------------------")

    except:
        print("-------------------------------------------------------------")
        print("Auto Scalling Group not found")
        print("-------------------------------------------------------------")
