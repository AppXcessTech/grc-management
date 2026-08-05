select
  repository_name,
  r ->> 'RepositoryArn' as repository_arn,
  r ->> 'ScanFrequency' as scan_frequency
from
  aws_ecr_repository,
  jsonb_array_elements(repository_scanning_configuration -> 'ScanningConfigurations') as r
where
  r ->> 'ScanFrequency' = 'MANUAL';