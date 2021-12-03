import boto3
from createFunctions import *
from deleteFunctions import *

# VARIABLES
# ==============================================================================================================

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

# ==============================================================================================================

# CREATING SECURITY GROUPS
# ==============================================================================================================

sec_group_database = create_security_group(
    ec2_ohio, security_GP_db_name, security_group_IP_rules_database)
sec_group_django = create_security_group(
    ec2_north_virginia, security_GP_django_name, security_group_IP_rules_django)

# ==============================================================================================================

# CREATING INSTANCES
# ==============================================================================================================

database_instance_script = """
#cloud-config

runcmd:
- cd /
- sudo apt update
- sudo apt install postgresql postgresql-contrib -y
- sudo su - postgres
- sudo -u postgres psql -c "CREATE USER cloud WITH PASSWORD 'cloud';"
- sudo -u postgres psql -c "CREATE DATABASE tasks;"
- sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tasks TO cloud;"
- sudo echo "listen_addresses = '*'" >> /etc/postgresql/10/main/postgresql.conf
- sudo echo "host all all 0.0.0.0/0 trust" >> /etc/postgresql/10/main/pg_hba.conf
- sudo ufw allow 5432/tcp -y
- sudo systemctl restart postgresql
"""

django_instance_script = """
#cloud-config

runcmd:
- cd /home/ubuntu 
- sudo apt update -y
- git clone https://github.com/roguetaver/tasks
- cd tasks
- sed -i "s/node1/PLACEHOLDER/g" ./portfolio/settings.py
- ./install.sh
- sudo ufw allow 8080/tcp -y
- sudo reboot
"""

database_instance, database_IP, database_ID = create_instance(
    ohio_region,
    image_ohio_id,
    sec_group_database,
    database_instance_script,
    database_instance_name,
    ec2_ohio
)

django_instance_script = django_instance_script.replace(
    "PLACEHOLDER", str(database_IP))

django_instance, django_IP, django_ID = create_instance(
    north_virginia_region,
    image_north_virginia_id,
    sec_group_django,
    django_instance_script,
    django_instance_name,
    ec2_north_virginia
)


# ==============================================================================================================

# CREATING IMAGES
# ==============================================================================================================

django_image_id = create_image(ec2_north_virginia,
                               django_ID,
                               waiter_ami,
                               django_image_name
                               )

delete_all_instances(
    ec2_north_virginia,
    waiter_north_virginia_instance
)

# ==============================================================================================================

# CREATING TARGET GROUP
# ==============================================================================================================

targetGroup = create_target_group(
    ec2_north_virginia, ec2_load_balancer, target_GP_name)

# ==============================================================================================================

# CREATING LOAD BALANCER
# ==============================================================================================================


load_balancer, load_balancer_arn = create_load_balancer(
    ec2_north_virginia,
    ec2_load_balancer,
    sec_group_django,
    waiter_load_balancer,
    load_balancer_name
)
# ==============================================================================================================

# CREATING LAUNCH CONFIGURATION AMI
# ==============================================================================================================

create_launch_config_ami(
    ec2_auto_scalling_group,
    django_image_id,
    sec_group_django,
    launch_config_name
)

# ==============================================================================================================

# CREATING AUTO SCALLING
# ==============================================================================================================

create_auto_scalling(
    ec2_auto_scalling_group,
    ec2_north_virginia,
    targetGroup,
    auto_scalling_name,
    launch_config_name
)

# ==============================================================================================================

# LOAD BALANCER INTEGRATION
# ==============================================================================================================

attach_load_balancer(ec2_auto_scalling_group, targetGroup, auto_scalling_name)

# ==============================================================================================================

# CREATING LISTENER
# ==============================================================================================================

create_listener(
    ec2_load_balancer,
    targetGroup,
    load_balancer_arn
)

# ==============================================================================================================

# CREATING AUTO SCALLING POLICY
# ==============================================================================================================

create_auto_scalling_group_policy(
    ec2_auto_scalling_group, targetGroup, load_balancer_arn, auto_scalling_name, auto_scalling_policy_name)

# ==============================================================================================================
