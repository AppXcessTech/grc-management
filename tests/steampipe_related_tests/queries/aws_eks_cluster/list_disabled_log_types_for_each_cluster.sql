select
  name,
  i ->> 'Enabled' as enabled,
  i ->> 'Types' as types
from
  aws_eks_cluster,
  jsonb_array_elements(logging -> 'ClusterLogging') as i
where
  i ->> 'Enabled' = 'false';