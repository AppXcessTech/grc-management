select
  dataset_id,
  location
from
  gcp_bigquery_dataset
where
  tags -> 'owner' is null;