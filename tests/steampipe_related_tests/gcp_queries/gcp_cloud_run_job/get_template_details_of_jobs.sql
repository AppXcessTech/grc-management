select
  name,
  template ->> 'Containers' as containers,
  template ->> 'EncryptionKey' as encryption_key,
  template ->> 'ExecutionEnvironment' as execution_environment,
  template ->> 'MaxRetries' as max_retries,
  template ->> 'ServiceAccount' as service_account,
  template ->> 'Timeout' as timeout,
  template ->> 'Volumes' as volumes,
  template ->> 'VpcAccess' as vpc_access
from
  gcp_cloud_run_job;