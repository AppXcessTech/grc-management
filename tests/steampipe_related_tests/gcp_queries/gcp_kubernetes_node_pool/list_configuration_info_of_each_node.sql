select
  name,
  cluster_name,
  config ->> 'diskSizeGb' as disk_size_gb,
  config ->> 'diskType' as disk_type,
  config ->> 'imageType' as image_type,
  config ->> 'machineType' as machine_type,
  config -> 'metadata' ->> 'disable-legacy-endpoints' as disable_legacy_endpoints,
  config ->> 'serviceAccount' as machine_type,
  config -> 'shieldedInstanceConfig' ->> 'enableIntegrityMonitoring' as enable_integrity_monitoring
from
  gcp_kubernetes_node_pool;