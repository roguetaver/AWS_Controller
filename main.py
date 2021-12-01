import os
import boto3
from utils import *

# INITIAL SETUP
# ==============================================================================================================

NORTH_VIRGINIA_REGION = "us-east-1"
OHIO_REGION = "us-east-2"

AMI_ID_NORTH_VIRGINIA_ID = "ami-0279c3b3186e54acd"
AMI_ID_OHIO_ID = "ami-020db2c14939a8efb"

security_GP_db_name = "database_securityGP"
security_GP_django_name = "django_securityGP"

# ==============================================================================================================

# CLIENT CONNECTION WITH EC2
# ==============================================================================================================

ec2_north_virginia = boto3.client('ec2', region_name=NORTH_VIRGINIA_REGION)
ec2_ohio = boto3.client('ec2', region_name=OHIO_REGION)

# ==============================================================================================================

# DELETING
# ==============================================================================================================

WAITER_NORTH_VIRGINIA_INSTANCE = ec2_north_virginia.get_waiter(
    'instance_terminated')
WAITER_OHIO_INSTANCE = ec2_ohio.get_waiter('instance_terminated')

delete_all_instances(
    ec2_north_virginia,
    WAITER_NORTH_VIRGINIA_INSTANCE
)

delete_all_instances(
    ec2_ohio,
    WAITER_OHIO_INSTANCE
)

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
  - sed -i "s/node1/POSTGRES_IP/g" ./portfolio/settings.py
  - ./install.sh
  - sudo ufw allow 8080/tcp -y
  - sudo reboot
  """

database_instance_name = "database_instance"
django_instance_name = "django_instance"

database_instance, POSTGRES_IP = create_instance(
    OHIO_REGION,
    AMI_ID_OHIO_ID,
    sec_group_database,
    database_instance_script,
    database_instance_name
)
command_django = django_instance_script.replace("IP_REPLACE", str(POSTGRES_IP))

django_instance, DJANGO_IP = create_instance(
    NORTH_VIRGINIA_REGION,
    AMI_ID_NORTH_VIRGINIA_ID,
    sec_group_django,
    django_instance_script,
    django_instance_name
)

delete_all_instances(
    ec2_north_virginia,
    WAITER_NORTH_VIRGINIA_INSTANCE
)
delete_all_instances(
    ec2_ohio,
    WAITER_OHIO_INSTANCE
)

delete_sec_group(ec2_ohio, security_GP_db_name)
delete_sec_group(ec2_north_virginia, security_GP_django_name)
