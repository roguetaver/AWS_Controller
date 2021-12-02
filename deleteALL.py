import boto3
from createFunctions import *
from deleteFunctions import *

# ==============================================================================================================
# INITIAL SETUP
# ==============================================================================================================

NORTH_VIRGINIA_REGION = "us-east-1"
OHIO_REGION = "us-east-2"

AMI_ID_NORTH_VIRGINIA_ID = "ami-0279c3b3186e54acd"
AMI_ID_OHIO_ID = "ami-020db2c14939a8efb"

security_GP_db_name = "database_securityGP"
security_GP_django_name = "django_securityGP"

ec2_north_virginia = boto3.client('ec2', region_name=NORTH_VIRGINIA_REGION)
ec2_ohio = boto3.client('ec2', region_name=OHIO_REGION)
ec2_load_balancer = boto3.client('elbv2', region_name=NORTH_VIRGINIA_REGION)
ec2_auto_scalling = boto3.client(
    'autoscaling', region_name=NORTH_VIRGINIA_REGION)

targetGP_name = "target-GP-load-balancer"
DJANGO_image_name = "DJANGO_image"
LoadBalancer_name = "LoadBalancerT"
database_instance_name = "database_instance"
django_instance_name = "django_instance"
launch_config_name = "launch_configuration_ami"
auto_scalling_name = "autoScallingGP"

WAITER_AMI = ec2_north_virginia.get_waiter('image_available')
WAITER_CREATE_LOAD_BALANCER = ec2_load_balancer.get_waiter(
    'load_balancer_available')
WAITER_NORTH_VIRGINIA_INSTANCE = ec2_north_virginia.get_waiter(
    'instance_terminated')
WAITER_OHIO_INSTANCE = ec2_ohio.get_waiter('instance_terminated')

# ==============================================================================================================
# DELETING
# ==============================================================================================================

delete_load_balancer(ec2_load_balancer, LoadBalancer_name)

delete_auto_scalling(ec2_auto_scalling, auto_scalling_name)

delete_launch_configuration(ec2_auto_scalling, launch_config_name)

delete_image(ec2_north_virginia, DJANGO_image_name)

delete_all_instances(
    ec2_north_virginia,
    WAITER_NORTH_VIRGINIA_INSTANCE
)

delete_all_instances(
    ec2_ohio,
    WAITER_OHIO_INSTANCE
)

delete_target_group(ec2_load_balancer, targetGP_name)

delete_sec_group(ec2_ohio, security_GP_db_name)
delete_sec_group(ec2_north_virginia, security_GP_django_name)
