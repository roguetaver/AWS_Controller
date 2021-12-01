#this command is used to check if you are authenticated to aws

import boto3
iam = boto3.client("iam")

for user in iam.list_users()["Users"]:
    print("")
    print(user["UserName"])
    print(user["UserId"])
    print(user["Arn"])
    print(user["CreateDate"])