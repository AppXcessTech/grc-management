select
  instance_name,
  count(*) as database_count
from
  gcp_sql_database
group by
  instance_name;