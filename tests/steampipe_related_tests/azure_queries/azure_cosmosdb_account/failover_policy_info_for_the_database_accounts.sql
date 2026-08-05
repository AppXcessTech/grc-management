select
  name,
  fp ->> 'failoverPriority' as failover_priority,
  fp ->> 'locationName' as location_name
from
  azure_cosmosdb_account
  cross join jsonb_array_elements(failover_policies) as fp;