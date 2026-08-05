select
  dataset_id,
  location,
  kms_key_name
from
  gcp_bigquery_dataset
where
  kms_key_name is null;