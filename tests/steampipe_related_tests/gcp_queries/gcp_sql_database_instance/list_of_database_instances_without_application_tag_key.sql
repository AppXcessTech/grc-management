select
  name,
  tags
from
  gcp_sql_database_instance
where
  not tags :: JSONB ? 'application';