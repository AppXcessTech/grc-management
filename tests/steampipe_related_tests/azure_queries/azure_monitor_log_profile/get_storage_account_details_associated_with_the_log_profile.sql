select
  l.name,
  l.type,
  s.access_tier,
  s.kind,
  s.blob_change_feed_enabled,
  s.blob_container_soft_delete_enabled,
  s.enable_https_traffic_only,
  s.encryption_key_source
from
  azure_monitor_log_profile as l,
  azure_storage_account as s
where
  l.storage_account_id = s.id