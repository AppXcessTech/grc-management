select
  name,
  id,
  location,
  type,
  identity,
  enable_rbac,
  sku
from
  azure_kubernetes_cluster
where
  not enable_rbac;