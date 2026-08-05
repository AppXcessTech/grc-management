select
  type,
  count(*) as backup_count
from
  gcp_sql_backup
group by
  type;