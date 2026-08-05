import boto3

ROLE_ARN = "arn:aws:iam::410974773014:role/grc_aws"

# Step 1: Assume the role
sts = boto3.client("sts")

response = sts.assume_role(
    RoleArn=ROLE_ARN,
    RoleSessionName="grc-asset-discovery"
)

credentials = response["Credentials"]

# Step 2: Create clients using temporary credentials

ec2 = boto3.client(
    "ec2",
    aws_access_key_id=credentials["AccessKeyId"],
    aws_secret_access_key=credentials["SecretAccessKey"],
    aws_session_token=credentials["SessionToken"],
    region_name="eu-north-1"
)

s3 = boto3.client(
    "s3",
    aws_access_key_id=credentials["AccessKeyId"],
    aws_secret_access_key=credentials["SecretAccessKey"],
    aws_session_token=credentials["SessionToken"]
)

# Step 3: Discover EC2 instances

print("\n=== EC2 Instances ===")

response = ec2.describe_instances()

for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:

        instance_id = instance["InstanceId"]

        name = "Unnamed"

        for tag in instance.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]

        print(f"Name: {name}")
        print(f"Instance ID: {instance_id}")
        print("-" * 40)

# Step 4: Discover S3 buckets

print("\n=== S3 Buckets ===")

response = s3.list_buckets()

for bucket in response["Buckets"]:
    print(bucket["Name"])
