select
  repository_name,
  r ->> 'RepositoryArn' as repository_arn,
  r ->> 'ScanOnPush' as scan_on_push
from
  aws_ecr_repository,
  jsonb_array_elements(repository_scanning_configuration -> 'ScanningConfigurations') as r
where
 r ->> 'ScanOnPush' = 'false';