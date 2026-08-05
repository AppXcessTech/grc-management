select
  dataset_id,
  location,
  ls as access_policy
from
  gcp_bigquery_dataset,
  jsonb_array_elements(access) as ls
where
  ls ->> 'specialGroup' = 'allAuthenticatedUsers'
  or ls ->> 'iamMember' = 'allUsers';