select
  name,
  location_type,
  n -> 'management' ->> 'autoUpgrade' node_auto_upgrade
from
  gcp_kubernetes_cluster,
  jsonb_array_elements(node_pools) as n
where
  n -> 'management' ->> 'autoUpgrade' = 'true';