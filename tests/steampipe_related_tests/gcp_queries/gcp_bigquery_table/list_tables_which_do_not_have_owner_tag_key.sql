select
  dataset_id,
  location
from
  gcp_bigquery_table
where
  tags -> 'owner' is null;