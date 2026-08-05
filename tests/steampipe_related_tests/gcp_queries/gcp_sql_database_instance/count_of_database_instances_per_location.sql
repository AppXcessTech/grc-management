select
  location,
  count(*) instance_count
from
  gcp_sql_database_instance
group by
  location;