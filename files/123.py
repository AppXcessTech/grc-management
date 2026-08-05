import boto3
from botocore.exceptions import ClientError

def check_ec2():
    try:
        ec2 = boto3.client("ec2")
        ec2.describe_instances(MaxResults=5)
        print("EC2: OK ✅")
    except ClientError as e:
        print(f"EC2: FAIL ❌ -> {e.response['Error']['Code']}")

def check_s3():
    try:
        s3 = boto3.client("s3")
        s3.list_buckets()
        print("S3: OK ✅")
    except ClientError as e:
        print(f"S3: FAIL ❌ -> {e.response['Error']['Code']}")

def check_rds():
    try:
        rds = boto3.client("rds")
        rds.describe_db_instances()
        print("RDS: OK ✅")
    except ClientError as e:
        print(f"RDS: FAIL ❌ -> {e.response['Error']['Code']}")

def check_lambda():
    try:
        lambda_client = boto3.client("lambda")
        lambda_client.list_functions(MaxItems=5)
        print("Lambda: OK ✅")
    except ClientError as e:
        print(f"Lambda: FAIL ❌ -> {e.response['Error']['Code']}")

def check_identity():
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print("STS Identity:", identity)
    except ClientError as e:
        print(f"STS: FAIL ❌ -> {e.response['Error']['Code']}")

if __name__ == "__main__":
    print("Checking AWS permissions...\n")
    check_identity()
    check_ec2()
    check_s3()
    check_rds()
    check_lambda()
