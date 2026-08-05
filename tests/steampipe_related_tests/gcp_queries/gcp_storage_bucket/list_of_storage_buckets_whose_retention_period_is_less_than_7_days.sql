select
  name,
  retention_policy ->> 'retentionPeriod' as retention_period
from
  gcp_storage_bucket
where
  retention_policy ->> 'retentionPeriod' < 604800 :: text;