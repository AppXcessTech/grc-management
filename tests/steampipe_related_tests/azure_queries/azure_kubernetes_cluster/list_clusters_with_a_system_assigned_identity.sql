select
  name,
  id,
  location,
  type,
  identity ->> 'type' as identity_type,
  sku
from
  azure_kubernetes_cluster
where
  identity ->> 'type' = 'SystemAssigned';