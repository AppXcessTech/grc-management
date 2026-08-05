select
  name,
  create_time,
  description,
  size_bytes,
  format
from
  gcp_artifact_registry_repository
where
  format = 'DOCKER';