select
  name,
  cleanup_policy_dry_run,
  create_time,
  kms_key_name
from
  gcp_artifact_registry_repository
where
  kms_key_name = '';