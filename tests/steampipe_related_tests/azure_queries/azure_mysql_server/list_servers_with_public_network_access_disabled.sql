select
  name,
  id,
  public_network_access
from
  azure_mysql_server
where
  public_network_access = 'Disabled';