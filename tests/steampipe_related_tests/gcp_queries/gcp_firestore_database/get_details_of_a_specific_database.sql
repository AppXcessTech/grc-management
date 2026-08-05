select
  name,
  uid,
  type,
  location,
  create_time,
  version_retention_period,
  earliest_version_time
from
  gcp_firestore_database
where
  title = '(default)';