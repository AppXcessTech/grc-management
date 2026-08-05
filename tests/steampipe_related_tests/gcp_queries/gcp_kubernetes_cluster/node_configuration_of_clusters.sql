select
  name,
  node_config ->> 'Disksizegb' as disk_size_gb,
  node_config ->> 'Disktype' as disk_type,
  node_config ->> 'Imagetype' as image_type,
  node_config ->> 'Machinetype' as machine_type,
  node_config ->> 'Disktype' as disk_type,
  node_config -> 'Metadata' ->> 'disable-legacy-endpoints' as disable_legacy_endpoints,
  node_config ->> 'Serviceaccount' as service_account,
  node_config -> 'Shieldedinstanceconfig' ->> 'EnableIntegrityMonitoring' as enable_integrity_monitoring
from
  gcp_kubernetes_cluster;