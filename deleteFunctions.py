import boto3
from botocore.config import Config
from request_functions import *

# =====================================================================================================================


def delete_security_group(ec2, security_group_name):
    security_group_bool = False
    security_groups = ec2.describe_security_groups()

    for security_group in security_groups['SecurityGroups']:
        if security_group['GroupName'] == security_group_name:
            try:
                security_group_bool = True
                deleted_sec_group = ec2.delete_security_group(
                    GroupName=security_group["GroupName"], GroupId=security_group["GroupId"])
            except:
                print("-------------------------------------------------------------")
                print("Error deleting " + security_group_name)
                logging.info("Error deleting " + security_group_name)
                print("-------------------------------------------------------------")

    if security_group_bool:

        print("-------------------------------------------------------------")
        print(security_group_name + " deleted")
        logging.info(security_group_name + " deleted")
        print("-------------------------------------------------------------")
    else:
        print("-------------------------------------------------------------")
        print(security_group_name + " not found")
        logging.info(security_group_name + " not found")
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
            print("deleting all instances")
            logging.info("deleting all instances")
            print(" . ")

            waiter.wait(InstanceIds=delete_instances_ids)

            print(" . ")
            print("Instances deleted")
            logging.info("Instances deleted")
            print("-------------------------------------------------------------")
        else:
            print("-------------------------------------------------------------")
            print("No instances to delete")
            logging.info("No instances to delete")
            print("-------------------------------------------------------------")
            return

    except Exception as e:
        print("-------------------------------------------------------------")
        print("ERROR")
        logging.info("ERROR")
        print("-------------------------------------------------------------")
        print(e)
        logging.info(e)

# =====================================================================================================================


def delete_image(ec2, image_name):
    images = ec2.describe_images(Filters=[
        {
            'Name': 'name',
            'Values': [image_name, ]
        },
    ])

    if len(images['Images']) < 1:
        print("-------------------------------------------------------------")
        print(image_name + " not found")
        logging.info(image_name + " not found")
        print("-------------------------------------------------------------")
        return
    else:
        image_id = images['Images'][0]['ImageId']
        ec2.deregister_image(ImageId=image_id)
        print("-------------------------------------------------------------")
        print(image_name + " deleted")
        logging.info(image_name + " deleted")
        print("-------------------------------------------------------------")

# =====================================================================================================================


def delete_target_group(client_load_balancer, targetGP_name):
    try:
        targetGPS = client_load_balancer.describe_target_groups(Names=[
                                                                targetGP_name])
    except:
        print("-------------------------------------------------------------")
        print(targetGP_name + " not found")
        logging.info(targetGP_name + " not found")
        print("-------------------------------------------------------------")
        return

    targetGP_arn = targetGPS['TargetGroups'][0]['TargetGroupArn']
    client_load_balancer.delete_target_group(TargetGroupArn=targetGP_arn)

    print("-------------------------------------------------------------")
    print(targetGP_name + " deleted")
    logging.info(targetGP_name + " deleted")
    print("-------------------------------------------------------------")

# =====================================================================================================================


def delete_load_balancer(ec2_load_balancer, load_balancer_name):
    try:
        load_balancers = ec2_load_balancer.describe_load_balancers(Names=[
                                                                   load_balancer_name])

    except:
        print("-------------------------------------------------------------")
        print(load_balancer_name + " not found")
        logging.info(load_balancer_name + " not found")
        print("-------------------------------------------------------------")
        return

    for loadbalancer in load_balancers['LoadBalancers']:

        ec2_load_balancer.delete_load_balancer(
            LoadBalancerArn=loadbalancer['LoadBalancerArn'])
        load_balancer_arn = loadbalancer['LoadBalancerArn']

    print("-------------------------------------------------------------")
    print(load_balancer_name + " deleted")
    logging.info(load_balancer_name + " deleted")
    print("-------------------------------------------------------------")
    return load_balancer_arn

# =====================================================================================================================


def delete_launch_configuration(ec2_auto_scalling, launch_configuration_name):
    try:
        print("-------------------------------------------------------------")
        print("deleting launch configuration")
        logging.info("deleting launch configuration")
        print(" . ")

        ec2_auto_scalling.delete_launch_configuration(
            LaunchConfigurationName=launch_configuration_name
        )

        print(" . ")
        print(launch_configuration_name + " deleted")
        logging.info(launch_configuration_name + " deleted")
        print("-------------------------------------------------------------")

    except:
        print("-------------------------------------------------------------")
        print(launch_configuration_name + " not found")
        logging.info(launch_configuration_name + " not found")
        print("-------------------------------------------------------------")
        return

# =====================================================================================================================


def delete_auto_scalling(ec2, auto_scalling_name):
    try:
        print("-------------------------------------------------------------")
        print("Deleting auto scalling group")
        logging.info("Deleting auto scalling group")
        print(" . ")

        ec2.delete_auto_scaling_group(
            AutoScalingGroupName=auto_scalling_name,
            ForceDelete=True
        )

        print(" . ")
        print(auto_scalling_name + " deleted")
        logging.info(auto_scalling_name + " deleted")
        print("-------------------------------------------------------------")

    except:
        print("-------------------------------------------------------------")
        print(auto_scalling_name + " not found")
        logging.info(auto_scalling_name + " not found")
        print("-------------------------------------------------------------")
