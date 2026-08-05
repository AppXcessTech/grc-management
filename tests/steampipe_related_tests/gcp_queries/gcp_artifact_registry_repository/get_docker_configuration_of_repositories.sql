select
  name,
  docker_config -> 'ImmutableTags' as immutable_tags,
  docker_config ->> 'ForceSendFields' as force_send_fields,
  docker_config ->> 'NullFields' as null_fields
from
  gcp_artifact_registry_repository;