select
  name,
  p -> 'action' ->> 'storageClass'  as storage_class,
  p -> 'action' ->> 'type'  as action_type,
  p -> 'condition' ->> 'age' as age_in_days
from
  gcp_storage_bucket,
  jsonb_array_elements(lifecycle_rules) as p;