import boto3
from createFunctions import *
from deleteFunctions import *

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

# ==============================================================================================================

# CREATING SECURITY GROUPS
# ==============================================================================================================

sec_group_database = create_sec_group(
    ec2_ohio, security_GP_db_name, Security_IP_Database)
sec_group_django = create_sec_group(
    ec2_north_virginia, security_GP_django_name, Security_IP_Django)

# ==============================================================================================================

# CREATING INSTANCES
# ==============================================================================================================

database_instance_script = """
  # cloud-config
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
  # cloud-config
  runcmd:
  - cd /home/ubuntu
  - sudo apt update -y
  - git clone https://github.com/roguetaver/tasks
  - cd tasks
  - sed -i "s/node1/POSTGRES_IP/g" ./portfolio/settings.py
  - ./install.sh
  - sudo ufw allow 8080/tcp -y
  - sudo reboot
  """

database_instance, database_IP, database_ID = create_instance(
    OHIO_REGION,
    AMI_ID_OHIO_ID,
    sec_group_database,
    database_instance_script,
    database_instance_name,
    ec2_ohio
)
command_django = django_instance_script.replace("IP_REPLACE", str(database_IP))

django_instance, DJANGO_IP, DJANGO_ID = create_instance(
    NORTH_VIRGINIA_REGION,
    AMI_ID_NORTH_VIRGINIA_ID,
    sec_group_django,
    django_instance_script,
    django_instance_name,
    ec2_north_virginia
)

# ==============================================================================================================

# CREATING IMAGES
# ==============================================================================================================

DJANGO_AMI_ID = create_image(ec2_north_virginia,
                             DJANGO_ID,
                             WAITER_AMI,
                             DJANGO_image_name
                             )

delete_all_instances(
    ec2_north_virginia,
    WAITER_NORTH_VIRGINIA_INSTANCE
)

# ==============================================================================================================

# CREATING TARGET GROUP
# ==============================================================================================================

targetGroup = create_target_group(
    ec2_north_virginia, ec2_load_balancer, targetGP_name)

# ==============================================================================================================

# CREATING LOAD BALANCER
# ==============================================================================================================


load_balancer, LOAD_BALANCER_ARN = create_loadbalancer(
    ec2_north_virginia,
    ec2_load_balancer,
    sec_group_django,
    WAITER_CREATE_LOAD_BALANCER,
    LoadBalancer_name
)
# ==============================================================================================================

# CREATING LAUNCH CONFIGURATION AMI
# ==============================================================================================================

create_launch_config_ami(
    ec2_auto_scalling,
    DJANGO_AMI_ID,
    sec_group_django,
    launch_config_name
)

# ==============================================================================================================

# CREATING AUTO SCALLING
# ==============================================================================================================

create_auto_scalling(
    ec2_auto_scalling,
    ec2_north_virginia,
    targetGroup,
    auto_scalling_name,
    launch_config_name
)

# ==============================================================================================================

# LOAD BALANCER INTEGRATION
# ==============================================================================================================

attach_load_balancer(ec2_auto_scalling, targetGroup, auto_scalling_name)

# ==============================================================================================================

# CREATING AUTO SCALLING POLICY
# ==============================================================================================================

create_auto_scalling_policy(
    ec2_auto_scalling, targetGroup, LOAD_BALANCER_ARN)

# ==============================================================================================================

# CREATING LISTENER
# ==============================================================================================================

create_listener(
    ec2_load_balancer,
    targetGroup,
    LOAD_BALANCER_ARN
)
