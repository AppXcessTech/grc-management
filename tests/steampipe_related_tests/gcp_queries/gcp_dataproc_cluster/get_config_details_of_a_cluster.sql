select
  cluster_name,
  config -> 'endpointConfig' as endpoint_config,
  config -> 'configBucket' as config_bucket,
  config -> 'shieldedInstanceConfig' as shielded_instance_config,
  config -> 'masterConfig' as master_config
from
  gcp_dataproc_cluster
where
  cluster_name = 'cluster-5824';