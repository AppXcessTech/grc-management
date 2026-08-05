select
  name,
  endpoint -> 'locations' as location,
  endpoint -> 'service' as service
from
  azure_subnet
  cross join jsonb_array_elements(service_endpoints) as endpoint;