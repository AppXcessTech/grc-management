select
  name as workspace_name,
  id as workspace_id,
  encryption -> 'CmkKey' ->> 'keyVaultUrl' as cmk_key_vault_url,
  encryption -> 'CmkKey' ->> 'name' as cmk_key_name,
  encryption ->> 'CmkStatus' as cmk_status,
  encryption -> 'DoubleEncryptionEnabled' as double_encryption_enabled
from
  azure_synapse_workspace;