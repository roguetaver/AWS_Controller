import boto3
from createFunctions import *
from deleteFunctions import *

# VARIABLES
# ==============================================================================================================

logging.info("-------------------------------------------------------------")
logging.info("RESET ALL INIT")
logging.info("-------------------------------------------------------------")

north_virginia_region = "us-east-1"
ohio_region = "us-east-2"

image_north_virginia_id = "ami-0279c3b3186e54acd"
image_ohio_id = "ami-020db2c14939a8efb"

ec2_north_virginia = boto3.client('ec2', region_name=north_virginia_region)
ec2_ohio = boto3.client('ec2', region_name=ohio_region)
ec2_load_balancer = boto3.client('elbv2', region_name=north_virginia_region)
ec2_auto_scalling_group = boto3.client(
    'autoscaling', region_name=north_virginia_region)

security_GP_db_name = "Database_security_GP-T"
security_GP_django_name = "Django_security_GP-T"
target_GP_name = "Target-GP-load-balancer-T"
django_image_name = "Django-image-T"
load_balancer_name = "Load-balancer-T"
database_instance_name = "Database-instance-T"
django_instance_name = "Django-instance-T"
launch_config_name = "Launch-configuration-ami-T"
auto_scalling_name = "Auto-Scalling-GP-T"
auto_scalling_policy_name = "Auto-scalling-policy"

waiter_ami = ec2_north_virginia.get_waiter('image_available')
waiter_load_balancer = ec2_load_balancer.get_waiter(
    'load_balancer_available')
waiter_north_virginia_instance = ec2_north_virginia.get_waiter(
    'instance_terminated')
waiter_ohio_instance = ec2_ohio.get_waiter('instance_terminated')

# ==============================================================================================================

# DELETING
# ==============================================================================================================
delete_load_balancer(ec2_load_balancer, load_balancer_name)

delete_auto_scalling(ec2_auto_scalling_group, auto_scalling_name)

delete_launch_configuration(ec2_auto_scalling_group, launch_config_name)

delete_image(ec2_north_virginia, django_image_name)

delete_all_instances(
    ec2_north_virginia,
    waiter_north_virginia_instance
)

delete_all_instances(
    ec2_ohio,
    waiter_ohio_instance
)

delete_target_group(ec2_load_balancer, target_GP_name)

delete_security_group(ec2_ohio, security_GP_db_name)
delete_security_group(ec2_north_virginia, security_GP_django_name)


logging.info("-------------------------------------------------------------")
logging.info("RESET ALL END")
logging.info("-------------------------------------------------------------")
