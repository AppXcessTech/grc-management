"""
Dynamic Steampipe-based AWS resource discovery.
Uses STEAMPIPE_TABLE_TO_TYPE from mappers/canonical_map.py to determine
which tables to query and how to map each discovered resource to a
CanonicalType.

This mode is scoped to **asset inventory**: each table is queried for its
identifier column only (``arn`` by default) so the inventory knows *what
exists* (arn + provider + canonical type) without hydrating every column.

Performance design:
  - Inventory queries select only the id column (no hydrate columns → no
    permission-gated API calls, faster, fewer warnings)
  - Table queries run in parallel via ThreadPoolExecutor (max 5 concurrent)
  - Per-query timeout (120s) + overall timeout (600s) prevent hanging
"""
import json
import re
import tempfile
import subprocess
import logging
import concurrent.futures
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, NoCredentialsError

from app.mappers.canonical_map import STEAMPIPE_TABLE_TO_TYPE
from app.services.steampipe_process import (
    ImportCancelledError,
    NetworkUnavailableError,
    MAX_QUERY_ATTEMPTS,
    handle_query_failure,
    kill_all,
    register,
    set_network_probe_url,
    unregister,
)

BOTO_CFG = BotoConfig(connect_timeout=5, read_timeout=10, retries={"max_attempts": 1})
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tuning knobs
# ---------------------------------------------------------------------------
MAX_CONCURRENT_QUERIES = 5       # Steampipe processes to run in parallel
PER_QUERY_TIMEOUT_SEC = 120      # Seconds before a single table query is abandoned
OVERALL_TIMEOUT_SEC = 600        # Seconds before the entire import is abandoned

# ---------------------------------------------------------------------------
# Inventory-mode identifier column per table
# ---------------------------------------------------------------------------
# Asset inventory only needs a stable identifier per resource — the ARN.
# Querying just the id column instead of ``select *`` skips every hydrate
# column (which can call extra AWS APIs the import role isn't authorised for
# and fail the whole query) and makes imports much faster.
#
# Almost every AWS Steampipe table exposes ``arn``. A handful don't, so they
# are mapped to the column the YAML rule uses as its canonical id.
TABLE_ID_COLUMN: dict[str, str] = {
    # Account-level policy — there is no ARN; one row per account.
    "aws_iam_account_password_policy": "account_id",
    # One row per IAM user, identified by the user's ARN.
    "aws_iam_credential_report": "user_arn",
    "aws_identitystore_user": "name",
    "aws_ecr_image_scan_finding": "name",
    "aws_vpc_flow_log": "flow_log_id",
}


def _table_select_sql(table_name: str) -> str:
    """Build the inventory SELECT for a table — just its identifier column.

    Defaults to ``arn``; tables without an ARN column are looked up in
    ``TABLE_ID_COLUMN``.
    """
    id_col = TABLE_ID_COLUMN.get(table_name, "arn")
    return f"select {id_col} from {table_name};"



# ===================================================================
# 1. Table-to-type mapping — imported from mappers/canonical_map.py
# ===================================================================


# ===================================================================
# 2. Helper: resolve a stable resource_id from a row
# ===================================================================
def resolve_resource_id(row: dict) -> str:
    """Pick the best identifier from a Steampipe row.

    Priority: arn -> name -> common AWS identifier fields -> first column value.
    """
    for key in (
        "arn",
        "name",
        "resource_id",
        "id",
        # AWS resource identifiers
        "instance_id",
        "function_name",
        "role_name",
        "user_name",
        "group_name",
        "bucket",
        "bucket_name",
        "cluster_name",
        "cluster_identifier",
        "db_instance_identifier",
        "db_cluster_identifier",
        "repository_name",
        "queue_url",
        "topic_name",
        "stream_name",
        "table_name",
        "log_group_name",
        "alarm_name",
        "secret_name",
        "key_id",
        "certificate_arn",
        "load_balancer_arn",
        "trail_arn",
        "detector_id",
        "analyzer_arn",
        "hub_arn",
        "volume_id",
        "snapshot_id",
        "subnet_id",
        "vpc_id",
        "security_group_id",
        "network_acl_id",
        "route_table_id",
        "flow_log_id",
    ):
        val = row.get(key)
        if val and isinstance(val, str):
            return val
    # Last resort - first non-null value
    for v in row.values():
        if v and isinstance(v, str):
            return v
    return "unknown"


# ===================================================================
# 3. Extract tags from a row (handles both dict and list-of-dicts)
# ===================================================================
def extract_tags(row: dict) -> list[dict] | dict | None:
    """Normalise tags to [{Key, Value}, ...] or dict."""
    raw = row.get("tags") or row.get("Tags") or row.get("TagSet")
    if isinstance(raw, list):
        if raw and isinstance(raw[0], dict):
            if "Key" in raw[0] or "key" in raw[0]:
                return raw  # already formatted
            return [{"Key": t.get("key", t.get("Key", "")), "Value": t.get("value", t.get("Value", ""))} for t in raw]
    if isinstance(raw, dict):
        return raw
    return None


# ===================================================================
# 4. Run a single Steampipe query (synchronous, with timeout)
# ===================================================================
def run_query(sql: str, install_dir: str, timeout_sec: int = PER_QUERY_TIMEOUT_SEC) -> list[dict]:
    """Execute a Steampipe SQL query and return parsed rows.

    Returns rows on success, empty list on failure.
    Permission warnings and other errors are logged and also returned via side-channel
    (the caller can check their own stderr capture).
    """
    cmd = ["steampipe", "query", sql, "--install-dir", install_dir, "--output", "json"]
    for attempt in range(MAX_QUERY_ATTEMPTS):
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
            if res.returncode != 0:
                if handle_query_failure(res.stderr or ""):
                    logger.warning(
                        "Network recovered — retrying query (attempt %d)", attempt + 1,
                    )
                    continue
                stderr_snippet = res.stderr[:500].strip()
                logger.warning("Steampipe query returned %d: %s", res.returncode, stderr_snippet)
                return []
            # Check stderr for permission warnings even on success (partial results)
            if res.stderr and res.stderr.strip():
                logger.warning("Steampipe query stderr (table may have partial results): %s", res.stderr[:500])
            data = json.loads(res.stdout)
            rows = data.get("rows", [])
            logger.debug("  Query returned %d rows", len(rows))
            return rows
        except subprocess.TimeoutExpired:
            if handle_query_failure("", timed_out=True):
                logger.warning(
                    "Network recovered — retrying timed-out query (attempt %d)", attempt + 1,
                )
                continue
            logger.warning("Steampipe query timed out after %ds: %.80s...", timeout_sec, sql)
            return []
        except json.JSONDecodeError as e:
            logger.warning("Steampipe JSON parse error: %s", e)
            return []
        except NetworkUnavailableError:
            raise
        except Exception as e:
            logger.warning("Steampipe query failed: %s", e)
            return []
    return []


# Regex patterns to parse AWS permission errors into structured components
# Pattern 1: "service:Action" (e.g., "ec2:DescribeInstances", "s3:ListAllMyBuckets")
_AWS_ACTION_RE = re.compile(r"([a-z0-9]+):([A-Za-z0-9]+)")
# Pattern 2: "operation error SERVICE: ActionName" (AWS SDK v3 style)
_AWS_OP_ERROR_RE = re.compile(r"operation error\s+([A-Za-z0-9]+):\s+([A-Za-z0-9]+)")
# Pattern 3: Extract resource from "on resource: <arn>"
_AWS_RESOURCE_RE = re.compile(r"on resource:\s+(\S+)")
# Pattern 4: "(Service: AmazonSERVICE; ...)" style
_AWS_SERVICE_TAG_RE = re.compile(r"\(Service:\s+Amazon([A-Za-z0-9]+)")


def _parse_permission_error(line: str, table_name: str = "") -> dict | None:
    """
    Parse a single permission error line into structured components.

    Returns dict with keys: service, action, resource, table, message
    or None if the line doesn't contain a permission error.
    """
    lower = line.lower()
    # Check if this line contains a permission error
    has_permission_keyword = any(kw in lower for kw in [
        "accessdenied", "access denied", "not authorized", "unauthorizedoperation",
        "authorizationerror", "unauthorized", "permission denied", "not have permission",
        "insufficient privileges", "insufficientpermissions",
        "is not authorized to perform",
    ])
    if not has_permission_keyword:
        return None

    service: str | None = None
    action: str | None = None
    resource: str | None = None

    # Try pattern 1: "service:Action" (e.g., "ec2:DescribeInstances")
    action_match = _AWS_ACTION_RE.search(line)
    if action_match:
        svc_prefix = action_match.group(1)
        action_name = action_match.group(2)
        # Map common AWS service prefixes to display names
        SERVICE_PREFIX_MAP = {
            "ec2": "EC2", "s3": "S3", "iam": "IAM", "lambda": "Lambda",
            "rds": "RDS", "dynamodb": "DynamoDB", "sqs": "SQS", "sns": "SNS",
            "kms": "KMS", "cloudtrail": "CloudTrail", "cloudwatch": "CloudWatch",
            "logs": "CloudWatch Logs", "eks": "EKS", "ecs": "ECS",
            "ecr": "ECR", "elb": "ELB", "elasticloadbalancing": "ELB",
            "acm": "ACM", "route53": "Route53", "apigateway": "API Gateway",
            "secretsmanager": "Secrets Manager", "ssm": "SSM",
            "config": "Config", "guardduty": "GuardDuty",
            "inspector": "Inspector", "securityhub": "SecurityHub",
            "organizations": "Organizations", "waf": "WAF",
            "shield": "Shield", "kinesis": "Kinesis",
            "redshift": "Redshift", "elasticache": "ElastiCache",
            "sts": "STS", "autoscaling": "Auto Scaling",
        }
        service = SERVICE_PREFIX_MAP.get(svc_prefix, svc_prefix.upper())
        action = action_name

    # Try pattern 2: "operation error SERVICE: Action" (AWS SDK v3)
    if not action:
        op_match = _AWS_OP_ERROR_RE.search(line)
        if op_match:
            service = op_match.group(1)
            action = op_match.group(2)

    # Try pattern 4: "(Service: AmazonXXX; ...)" to get service name
    if not service:
        tag_match = _AWS_SERVICE_TAG_RE.search(line)
        if tag_match:
            service = tag_match.group(1)

    # Try pattern 3: extract resource ARN from "on resource: <arn>"
    resource_match = _AWS_RESOURCE_RE.search(line)
    if resource_match:
        resource = resource_match.group(1)

    # If we couldn't parse service/action, derive from table name
    if not service and table_name:
        # Convert "aws_ec2_instance" -> "EC2"
        parts = table_name.split("_")
        if len(parts) >= 2 and parts[0] == "aws":
            table_svc = parts[1].upper()
            service = {
                "EC2": "EC2", "S3": "S3", "IAM": "IAM", "RDS": "RDS",
                "LAMBDA": "Lambda", "KMS": "KMS", "ELB": "ELB", "SQS": "SQS",
                "DYNAMODB": "DynamoDB", "CLOUDTRAIL": "CloudTrail",
                "GUARDDUTY": "GuardDuty", "REDSHIFT": "Redshift",
                "EKS": "EKS", "ECS": "ECS", "ECR": "ECR",
            }.get(table_svc, table_svc)

    msg = line[:300].strip()
    return {
        "service": service or "Unknown",
        "action": action or "Unknown",
        "resource": resource or "",
        "table": table_name,
        "message": msg,
    }


def _extract_permission_warnings(stderr: str, table_name: str = "") -> list[dict]:
    """
    Extract permission-related warning messages from stderr output.

    Returns structured warnings as list of dicts with:
      - service: AWS service name (EC2, S3, IAM, etc.)
      - action:  The API action that was denied (DescribeInstances, ListBuckets, etc.)
      - resource: The resource ARN or identifier
      - table:   The Steampipe table that was being queried
      - message: The raw error message
    """
    if not stderr:
        return []
    seen = set()
    warnings = []
    for line in stderr.split("\n"):
        line = line.strip()
        if not line:
            continue
        parsed = _parse_permission_error(line, table_name)
        if parsed:
            # Deduplicate by service+action
            dedup_key = f"{parsed['service']}:{parsed['action']}"
            if dedup_key not in seen:
                seen.add(dedup_key)
                warnings.append(parsed)
    return warnings


# ===================================================================
# 5. Query a single table and convert rows to resource entries
# ===================================================================
def _query_table(
    table_name: str,
    canonical_type: str,
    install_dir: str,
    default_region: str,
    default_account_id: str,
) -> tuple[list[dict], list[dict]]:
    """Query a single Steampipe table via a minimal id-column SELECT.

    Asset-inventory mode: each row carries only the identifier column, so
    every resource resolves to ``arn`` (or the table's fallback id). Rows
    with no resolvable id are skipped to avoid ``unknown`` collisions on the
    (organization, provider, provider_resource_id) unique constraint.

    Returns:
        (entries, structured_permission_warnings)
    """
    sql = _table_select_sql(table_name)
    cmd = ["steampipe", "query", sql, "--install-dir", install_dir, "--output", "json"]
    warnings: list[dict] = []
    rows: list[dict] = []

    for attempt in range(MAX_QUERY_ATTEMPTS):
        proc = None
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            register(proc)
            stdout, stderr = proc.communicate(timeout=PER_QUERY_TIMEOUT_SEC)
            res = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)

            # Check stderr for permission warnings on this table
            if res.stderr and res.stderr.strip():
                perm_warnings = _extract_permission_warnings(res.stderr, table_name)
                if perm_warnings:
                    warnings.extend(perm_warnings)
                    logger.warning("Permission warnings for table %s: %s", table_name, [w["message"] for w in perm_warnings])

            if res.returncode != 0:
                if handle_query_failure(res.stderr or ""):
                    logger.warning(
                        "Network recovered — retrying %s (attempt %d)", table_name, attempt + 1,
                    )
                    continue
                logger.warning("Steampipe query returned %d for %s: %s", res.returncode, table_name, res.stderr[:500])
                return [], warnings

            data = json.loads(res.stdout)
            rows = data.get("rows", [])
            logger.debug("  %s -> %d rows", table_name, len(rows))
            break
        except subprocess.TimeoutExpired:
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
            if handle_query_failure("", timed_out=True):
                logger.warning(
                    "Network recovered — retrying timed-out query for %s (attempt %d)", table_name, attempt + 1,
                )
                continue
            logger.warning("Steampipe query timed out for %s", table_name)
            return [], warnings + [{
                "service": "Timeout",
                "action": "Query",
                "resource": "",
                "table": table_name,
                "message": f"Query for {table_name} timed out after {PER_QUERY_TIMEOUT_SEC}s",
            }]
        except json.JSONDecodeError as e:
            logger.warning("Steampipe JSON parse error for %s: %s", table_name, e)
            return [], warnings
        except NetworkUnavailableError:
            raise
        except Exception as e:
            logger.warning("Steampipe query failed for %s: %s", table_name, e)
            return [], warnings
        finally:
            if proc:
                unregister(proc)
    else:
        # Loop exhausted after repeated network flaps — give up on this table
        return [], warnings

    if not rows:
        return [], warnings

    entries = []
    for row in rows:
        rid = resolve_resource_id(row)
        # Skip rows with no identifier — they'd collide on the
        # (organization, provider, provider_resource_id) unique constraint.
        if not rid or rid == "unknown":
            logger.debug("Skipping row from %s with no resolvable id", table_name)
            continue
        row_region = row.get("region") or default_region
        tags = extract_tags(row)

        # The ARN (via `rid`) is the single identifier for AWS resources — the
        # YAML rules resolve display_name from $.arn during ingestion, so no
        # name-based display fields are computed here.
        entry = {
            "resource_type": table_name,
            "resource_id": rid,
            "canonical_type": canonical_type,
            "region": row_region,
            "account_id": row.get("account_id") or default_account_id,
            "tags": tags,
            "details": row,
        }

        # Extract common relationship references
        relationships = {}
        for ref_key in ("vpc_id", "VpcId", "subnet_id", "SubnetId", "cluster_name", "ClusterName"):
            if ref_key in row:
                rel_name = ref_key.replace("_id", "").replace("Id", "")
                relationships[rel_name] = row[ref_key]
        if relationships:
            entry["relationships"] = relationships

        entries.append(entry)

    return entries, warnings


# ===================================================================
# 6. Main import function
# ===================================================================
async def import_aws_resources_via_steampipe(
    role_arn: str,
    account_name: Optional[str] = None,
    external_id: Optional[str] = None,
    region: str = "us-east-1",
    db=None,
    progress_callback: Optional[callable] = None,
) -> dict:
    """
    Discover AWS resources via Steampipe.

    Flow:
      1. Assume the target IAM role
      2. Create a temporary Steampipe config directory
      3. Read the YAML rules to know which tables to query
      4. For each table, run a minimal id-column SELECT (``arn`` by default)
         **in parallel** (up to MAX_CONCURRENT_QUERIES at a time, each with a
         timeout)
      5. Map each result to the appropriate canonical type
      6. Return structured data ready for ingestion
    """
    # ---------------------------------------------------------------
    # 1. Assume role
    # ---------------------------------------------------------------
    credentials = _assume_role(role_arn, external_id, region)

    # ---------------------------------------------------------------
    # 2. Get account ID
    # ---------------------------------------------------------------
    sts_client = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    ).client("sts", config=BOTO_CFG, region_name=region)
    account_id = sts_client.get_caller_identity()["Account"]

    # ---------------------------------------------------------------
    # 3. Load table-to-type mapping
    # ---------------------------------------------------------------
    if not STEAMPIPE_TABLE_TO_TYPE:
        logger.error("STEAMPIPE_TABLE_TO_TYPE is empty - check mappers/canonical_map.py")
        return {"account_id": account_id, "resources_discovered": 0, "resources_detail": []}

    # ---------------------------------------------------------------
    # 4. Create temp config and run queries in parallel
    # ---------------------------------------------------------------
    with tempfile.TemporaryDirectory() as temp_dir:
        # Symlink Steampipe installation folders
        steampipe_home = Path.home() / ".steampipe"
        for folder in ["plugins", "db", "internal"]:
            src = steampipe_home / folder
            dst = Path(temp_dir) / folder
            if src.exists() and not dst.exists():
                dst.symlink_to(src, target_is_directory=True)

        # Write aws.spc with assumed credentials
        config_dir = Path(temp_dir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        spc = f"""
connection "aws" {{
  plugin = "aws"
  regions = ["{region}"]
  access_key = "{credentials['AccessKeyId']}"
  secret_key = "{credentials['SecretAccessKey']}"
  session_token = "{credentials['SessionToken']}"
}}
"""
        (config_dir / "aws.spc").write_text(spc)

        # Point the network gate at the AWS STS endpoint so a connectivity
        # probe checks the same network path the Steampipe plugin uses.
        set_network_probe_url("https://sts.amazonaws.com")

        # Build the list of table-query tasks
        tasks = []
        for table_name, canonical_type in STEAMPIPE_TABLE_TO_TYPE.items():
            tasks.append((table_name, canonical_type, temp_dir, region, account_id))

        all_resources: list[dict] = []
        all_warnings: list[dict] = []

        logger.info(
            "Starting parallel discovery of %d tables (max %d concurrent, %ds per-query timeout)",
            len(tasks), MAX_CONCURRENT_QUERIES, PER_QUERY_TIMEOUT_SEC,
        )

        # Notify initial progress
        if progress_callback:
            progress_callback({
                "total_tables": len(tasks),
                "completed_tables": 0,
                "current_table": "",
                "resources_found": 0,
                "message": f"Starting discovery of {len(tasks)} resource types...",
                "warnings": [],
            })

        completed = 0

        # Run table queries in the thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_QUERIES) as pool:
            future_map = {
                pool.submit(_query_table, t, ct, td, r, aid): t
                for t, ct, td, r, aid in tasks
            }

            # Use as_completed to report progress as each table finishes
            try:
                for future in concurrent.futures.as_completed(future_map, timeout=OVERALL_TIMEOUT_SEC):
                    table = future_map[future]
                    completed += 1
                    try:
                        entries, table_warnings = future.result()
                        if entries:
                            logger.info("  %s -> %d resources", table, len(entries))
                            all_resources.extend(entries)
                        else:
                            logger.debug("  %s -> 0 resources", table)
                        if table_warnings:
                            all_warnings.extend(table_warnings)
                    except concurrent.futures.CancelledError:
                        logger.warning("  %s -> cancelled (timeout)", table)
                        all_warnings.append({
                            "service": "Timeout",
                            "action": "Query",
                            "resource": "",
                            "table": table,
                            "message": f"Query for {table} was cancelled due to overall timeout",
                        })
                    except (ImportCancelledError, NetworkUnavailableError):
                        raise
                    except Exception as e:
                        logger.warning("  %s -> error: %s", table, e)
                        all_warnings.append({
                            "service": "Error",
                            "action": "Unknown",
                            "resource": "",
                            "table": table,
                            "message": f"{table}: {str(e)[:200]}",
                        })

                    # Report progress after each table completes
                    if progress_callback:
                        progress_callback({
                            "total_tables": len(tasks),
                            "completed_tables": completed,
                            "current_table": table,
                            "resources_found": len(all_resources),
                            "message": f"Queried {table} ({completed}/{len(tasks)})",
                            "warnings": all_warnings[-20:],  # last 20 warnings to avoid bloating
                        })
            except concurrent.futures.TimeoutError:
                logger.warning("Overall import timeout reached after %ds — processing partial results", OVERALL_TIMEOUT_SEC)
                all_warnings.append({
                    "service": "Timeout",
                    "action": "Import",
                    "resource": "",
                    "table": "",
                    "message": f"Import timed out after {OVERALL_TIMEOUT_SEC}s — only partial results available",
                })
            except (ImportCancelledError, NetworkUnavailableError):
                # Cancellation requested or network outage — cancel queued
                # table tasks so the executor's shutdown(wait=True) below does
                # NOT drain the whole queue before the outcome is honoured.
                # Re-kill any newly spawned Steampipe subprocesses (workers may
                # have dequeued the next task and registered a fresh process
                # after the cancel endpoint's initial kill) so shutdown returns
                # immediately.
                for future, table in future_map.items():
                    if not future.done():
                        future.cancel()
                        logger.debug("Cancelled pending future for table %s", table)
                kill_all()
                raise

            # Cancel any pending futures that didn't complete
            for future, table in future_map.items():
                if not future.done():
                    future.cancel()
                    logger.debug("Cancelled pending future for table %s", table)

            tables_with_data = {r["resource_type"] for r in all_resources}
            logger.info(
                "Discovery complete: %d total resources from %d tables with %d warnings",
                len(all_resources), len(tables_with_data), len(all_warnings),
            )

    # ---------------------------------------------------------------
    # 5. Build final result
    # ---------------------------------------------------------------
    discovery_run_id = str(uuid4())
    raw_api_records = []
    for r in all_resources:
        service = _derive_service(r["resource_type"])
        raw_api_records.append({
            "discovery_run_id": discovery_run_id,
            "provider": "AWS",
            "account_id": account_id,
            "region": r.get("region"),
            "service": service,
            "resource_type": r["resource_type"],
            "provider_resource_id": r["resource_id"],
            "api_call": "steampipe_query",
            "api_response": r["details"],
        })

    if db and raw_api_records:
        from app.models.raw_api_response import RawApiResponse
        db.add_all([RawApiResponse(**rec) for rec in raw_api_records])
        # NOT committing here — caller is responsible for the full transaction
        # lifecycle so that a network failure mid-import rolls back everything.

    asset_results = [{**r, "action": "discovered"} for r in all_resources]

    return {
        "account_id": account_id,
        "resources_discovered": len(all_resources),
        "resources": asset_results,
        "resources_detail": all_resources,
        "warnings": all_warnings,
    }


# ===================================================================
# Helper: STS Assume Role
# ===================================================================
def _assume_role(role_arn: str, external_id: Optional[str] = None, region: str = "us-east-1") -> dict:
    sts = boto3.client("sts", config=BOTO_CFG, region_name=region)
    kwargs = {"RoleArn": role_arn, "RoleSessionName": "AppXcessSteampipeSession"}
    if external_id:
        kwargs["ExternalId"] = external_id
    return sts.assume_role(**kwargs)["Credentials"]


def validate_connection(role_arn: str, external_id: Optional[str] = None, region: str = "us-east-1") -> dict:
    """Validate an AWS IAM role connection by assuming the role and getting caller identity."""
    try:
        credentials = _assume_role(role_arn, external_id, region)
        sts = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        ).client("sts", config=BOTO_CFG, region_name=region)
        account_id = sts.get_caller_identity()["Account"]
        return {"success": True, "account_id": account_id}
    except (ClientError, NoCredentialsError) as e:
        return {"success": False, "error": str(e)}


_RESOURCE_TO_SERVICE: dict[str, str] = {
    "s3_bucket": "S3",
    "EC2": "EC2",
    "SecurityGroup": "EC2",
    "Volume": "EC2",
    "VPC": "EC2",
    "Subnet": "EC2",
    "RDS": "RDS",
    "Lambda": "Lambda",
    "IAMUser": "IAM",
    "IAMRole": "IAM",
    "IAMGroup": "IAM",
    "IAMPolicy": "IAM",
    "PasswordPolicy": "IAM",
    "CredentialReport": "IAM",
    "KMSKey": "KMS",
    "CloudTrail": "CloudTrail",
    "Config": "Config",
    "OrganizationAccount": "Organizations",
    "ELBv2": "ELBv2",
    "ELB": "ELB",
    "GuardDuty": "GuardDuty",
    "AccessAnalyzer": "AccessAnalyzer",
    "Inspector2": "Inspector2",
    "SecurityHub": "SecurityHub",
    "CloudWatch": "CloudWatch",
    "CloudWatchLogs": "CloudWatchLogs",
    "DynamoDB": "DynamoDB",
    "SQS": "SQS",
    "ECSCluster": "ECS",
    "ECSService": "ECS",
    "ECSTask": "ECS",
    "EKSCluster": "EKS",
    "EKSNode": "EKS",
    "EFS": "EFS",
    "ECRRepository": "ECR",
    "Redshift": "Redshift",
    "NetworkACL": "EC2",
    "RouteTable": "EC2",
    "AutoScalingGroup": "AutoScaling",
    "Certificate": "ACM",
    "FlowLog": "EC2",
    "CodeCommit": "CodeCommit",
    "DocumentDB": "DocumentDB",
}


def _derive_service(resource_type: str) -> str:
    """Derive the AWS service name from a resource type."""
    return _RESOURCE_TO_SERVICE.get(resource_type, resource_type)
