select
  name,
  id,
  location,
  type,
  kubernetes_version
from
  azure_kubernetes_cluster
where
  kubernetes_version < '1.20.5';