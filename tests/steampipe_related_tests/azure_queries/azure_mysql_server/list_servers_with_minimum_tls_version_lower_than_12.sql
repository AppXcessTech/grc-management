select
  name,
  id,
  minimal_tls_version
from
  azure_mysql_server
where
  minimal_tls_version = 'TLS1_0'
  or minimal_tls_version = 'TLS1_1';