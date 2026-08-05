select
  repository_name,
  r ->> 'AppliedScanFilters' as applied_scan_filters,
  r ->> 'RepositoryArn' as repository_arn,
  r ->> 'ScanFrequency' as scan_frequency,
  r ->> 'ScanOnPush' as scan_on_push
from
  aws_ecr_repository,
  jsonb_array_elements(repository_scanning_configuration -> 'ScanningConfigurations') as r;