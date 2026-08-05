select
  name,
  id,
  type,
  server_security_alert_policy
from
  azure_mysql_server
where
  resource_group = 'demo'
  and name = 'server-test-for-pr';