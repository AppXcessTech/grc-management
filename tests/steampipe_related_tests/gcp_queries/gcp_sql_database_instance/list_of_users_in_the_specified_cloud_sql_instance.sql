select
  name,
  instance_users
from
  gcp_sql_database_instance
where
  name='my-sql-instance';