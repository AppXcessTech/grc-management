select
  name,
  format,
  mode,
  create_time
from
  gcp_artifact_registry_repository
where
  mode = 'STANDARD_REPOSITORY';