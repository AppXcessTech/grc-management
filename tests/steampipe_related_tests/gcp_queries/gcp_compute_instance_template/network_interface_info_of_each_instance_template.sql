select
  name,
  id,
  i ->> 'name' as name,
  split_part(i ->> 'network', '/', 10) as network_name,
  p ->> 'name' as access_config_name,
  p ->> 'networkTier' as access_config_network_tier,
  p ->> 'type' as access_config_type
from
  gcp_compute_instance_template,
  jsonb_array_elements(instance_network_interfaces) as i,
  jsonb_array_elements(i -> 'accessConfigs') as p;