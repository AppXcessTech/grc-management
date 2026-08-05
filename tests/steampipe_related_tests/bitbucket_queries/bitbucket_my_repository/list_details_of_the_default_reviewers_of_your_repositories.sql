with default_reviewers as (
  select
  full_name as repository_name,
  r ->> 'AccountId' as reviewer_account_id,
  r ->> 'Uuid' as reviewer_uuid,
  r ->> 'DisplayName' as reviewer_display_name,
  r ->> 'Type' as reviewer_type
from
  bitbucket_my_repository,
  jsonb_array_elements(default_reviewers) as r
)
select
  repository_name,
  reviewer_account_id,
  reviewer_uuid,
  reviewer_display_name,
  reviewer_type
from
  default_reviewers;