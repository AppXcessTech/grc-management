select
  name,
  ip ->> 'ipAddress' as ip_address,
  ip ->> 'type' as type
from
  gcp_sql_database_instance,
  jsonb_array_elements(ip_addresses) as ip;