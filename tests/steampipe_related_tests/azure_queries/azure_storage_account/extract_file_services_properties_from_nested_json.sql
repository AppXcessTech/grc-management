select
  name,
  fs ->> 'id' as file_service_id,
  fs -> 'sku' ->> 'name' as file_service_sku_name,
  fs -> 'sku' ->> 'tier' as file_service_sku_tier,
  fs ->> 'type' as file_service_type,
  fs -> 'properties' -> 'shareDeleteRetentionPolicy' ->> 'days' as retention_days,
  fs -> 'properties' -> 'shareDeleteRetentionPolicy' ->> 'enabled' as retention_enabled,
  fs -> 'properties' -> 'protocolSettings' -> 'smb' ->> 'versions' as smb_versions,
  fs -> 'properties' -> 'protocolSettings' -> 'smb' ->> 'channelEncryption' as smb_channel_encryption,
  fs -> 'properties' -> 'protocolSettings' -> 'smb' ->> 'authenticationMethods' as smb_auth_methods,
  fs -> 'properties' -> 'protocolSettings' -> 'smb' ->> 'kerberosTicketEncryption' as smb_kerberos_encryption
from
  azure_storage_account,
  jsonb_array_elements(file_services) as fs
where
  file_services is not null;