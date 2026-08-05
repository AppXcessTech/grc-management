select
  name,
  uid,
  type,
  location
from
  gcp_firestore_database
where
  type = 'FIRESTORE_NATIVE';