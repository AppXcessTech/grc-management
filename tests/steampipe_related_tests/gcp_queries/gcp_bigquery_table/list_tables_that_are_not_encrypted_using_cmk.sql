select
  table_id,
  dataset_id,
  location,
  kms_key_name
from
  gcp_bigquery_table
where
  kms_key_name is null;