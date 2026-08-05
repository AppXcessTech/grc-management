select
  name,
  encryption_properties ->> 'VaultBaseURL' as vault_base_url,
  encryption_properties ->> 'KeyName' as key_name,
  encryption_properties ->> 'KeyVersion' as key_version,
  region
from
  azure_container_group;