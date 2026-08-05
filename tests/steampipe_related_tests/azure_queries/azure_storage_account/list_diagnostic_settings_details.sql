select
  name,
  jsonb_pretty(diagnostic_settings) as diagnostic_settings
from
  azure_storage_account;