select
  name,
  split_part(subnet ->> 'id', '/', 11) subnet,
  region
from
  azure_route_table
  cross join jsonb_array_elements(subnets) as subnet;