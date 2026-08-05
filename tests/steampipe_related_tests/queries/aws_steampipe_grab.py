import os
import re
import time
import requests

BASE_URL = "https://raw.githubusercontent.com/turbot/steampipe-plugin-aws/main/docs/tables"

TABLES = [
    "aws_accessanalyzer_analyzer",              # AWS Access Analyzer
    "aws_accessanalyzer_finding",                # AWS Access Analyzer (findings)
    "aws_ec2_autoscaling_group",                 # AWS Autoscaling Group
    "aws_acm_certificate",                       # AWS Certificate Manager
    "aws_cloudtrail_trail",                      # AWS CloudTrail
    "aws_cloudwatch_log_group",                  # AWS CloudWatch Log Group
    "aws_cloudwatch_alarm",                      # AWS CloudWatch Metric Alarm
    "aws_codecommit_repository",                 # AWS CodeCommit Repo
    "aws_config_configuration_recorder",         # AWS Config Recorder
    "aws_iam_credential_report",                 # AWS Credential Report (IAM)
    "aws_docdb_cluster",                         # AWS DocumentDB Cluster
    "aws_dynamodb_table",                        # AWS DynamoDB Table
    "aws_ebs_volume",                            # AWS EBS Volume
    "aws_ec2_instance",                          # AWS EC2 Instance
    "aws_ecr_repository",                        # AWS ECR Container Repository
    "aws_ecr_image_scan_finding",                # AWS ECR Container Vulnerability
    "aws_ecs_cluster",                           # AWS ECS Cluster
    "aws_ecs_service",                           # AWS ECS Service
    "aws_ecs_task",                              # AWS ECS Standalone Task
    "aws_efs_file_system",                       # AWS EFS File System
    "aws_eks_cluster",                           # AWS EKS Cluster
    "aws_eks_node_group",                        # AWS EKS Node (closest match -- table is node GROUP level, not per-node)
    "aws_vpc_flow_log",                          # AWS Flow Log
    "aws_iam_group",                             # AWS Group (IAM)
    "aws_guardduty_detector",                    # AWS Guard Duty Detector
    "aws_guardduty_finding",                     # AWS Guard Duty (findings -- not in your list, but likely needed alongside detector)
    "aws_identitystore_user",                    # AWS IAM Identity Center User
    "aws_iam_policy",                            # AWS IAM Policy
    "aws_iam_user",                              # AWS IAM User
    "aws_inspector2_finding",                    # AWS Inspector Vulnerability (Inspector2 -- current gen)
    "aws_kms_key",                               # AWS KMS Key
    "aws_lambda_function",                       # AWS Lambda Function
    "aws_ec2_application_load_balancer",         # AWS Load Balancer (ALB)
    "aws_ec2_network_load_balancer",             # AWS Load Balancer (NLB)
    "aws_ec2_classic_load_balancer",             # AWS Load Balancer (Classic -- only if legacy ELBs are in scope)
    "aws_vpc_network_acl",                       # AWS Network ACL
    "aws_organizations_account",                 # AWS Organization Account
    "aws_iam_account_password_policy",           # AWS Password Policy (IAM)
    "aws_rds_db_instance",                       # AWS RDS Instance
    "aws_redshift_cluster",                      # AWS Redshift Cluster
    "aws_iam_role",                              # AWS Role (IAM)
    "aws_vpc_route_table",                       # AWS Route Table
    "aws_s3_bucket",                             # AWS S3 Bucket
    "aws_vpc_security_group",                    # AWS Security Group
    "aws_securityhub_hub",                       # AWS Security Hub
    "aws_securityhub_finding",                   # AWS Security Hub (findings -- not in your list, but likely needed alongside hub)
    "aws_sqs_queue",                             # AWS SQS Queue
    "aws_vpc_subnet",                            # AWS Subnet
    "aws_vpc",                                   # AWS VPC
]

OUTPUT_ROOT = "queries"

os.makedirs(OUTPUT_ROOT, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ### Heading followed by the next sql+postgres block
PATTERN = re.compile(
    r"###\s+(.*?)\n.*?```sql\+postgres\s*(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

for table in TABLES:
    url = f"{BASE_URL}/{table}.md"

    print(f"Fetching {table}...")

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()

        markdown = response.text

        matches = PATTERN.findall(markdown)

        if not matches:
            print("❌ No queries found.")
            continue

        table_dir = os.path.join(OUTPUT_ROOT, table)
        os.makedirs(table_dir, exist_ok=True)

        for heading, query in matches:

            # Convert heading into a safe filename
            filename = heading.lower().strip()
            filename = re.sub(r"[^\w\s-]", "", filename)
            filename = re.sub(r"\s+", "_", filename)

            output_file = os.path.join(table_dir, f"{filename}.sql")

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(query.strip())

        print(f"✅ Saved {len(matches)} queries.")

        time.sleep(0.5)

    except Exception as e:
        print(f"❌ {table}: {e}")
