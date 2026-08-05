select
  repository_name,
  r -> 'selection' ->> 'tagStatus' as tag_status,
  r -> 'selection' ->> 'countType' as count_type
from
  aws_ecr_repository,
  jsonb_array_elements(lifecycle_policy -> 'rules') as r
where
  (
    (r -> 'selection' ->> 'tagStatus' <> 'untagged')
    and (
      r -> 'selection' ->> 'countType' <> 'sinceImagePushed'
    )
  );