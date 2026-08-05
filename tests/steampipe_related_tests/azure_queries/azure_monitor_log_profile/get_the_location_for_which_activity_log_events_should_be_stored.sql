select
  p.name,
  p.id,
  p.storage_account_id,
  l as location
from
  azure_monitor_log_profile as p,
  jsonb_array_elements_text(locations) as l;