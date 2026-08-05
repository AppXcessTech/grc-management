select
  name,
  template ->> 'Annotations' as template_annotations,
  template ->> 'Containers' as containers,
  template ->> 'EncryptionKey' as encryption_key,
  template ->> 'ExecutionEnvironment' as execution_environment,
  template ->> 'Revision' as revision,
  template ->> 'Scaling' as scaling,
  template ->> 'ServiceAccount' as service_account,
  template ->> 'SessionAffinity' as session_affinity,
  template ->> 'Timeout' as timeout,
  template ->> 'Volumes' as volumes,
  template ->> 'VpcAccess' as vpc_access
from
  gcp_cloud_run_service;