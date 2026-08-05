select
  name,
  enable_ddos_protection,
  region,
  resource_group
from
  azure_virtual_network
where
  not enable_ddos_protection;