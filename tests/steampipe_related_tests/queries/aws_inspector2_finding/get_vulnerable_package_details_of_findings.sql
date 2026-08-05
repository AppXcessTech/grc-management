select
  f.arn,
  f.vulnerability_id,
  v ->> 'Name' as vulnerability_package_name,
  v ->> 'Version' as vulnerability_package_version,
  v ->> 'Arch' as vulnerability_package_arch,
  v ->> 'Epoch' as vulnerability_package_epoch,
  v ->> 'FilePath' as vulnerability_package_file_path,
  v ->> 'FixedInVersion' as vulnerability_package_fixed_in_version,
  v ->> 'PackageManager' as vulnerability_package_package_manager,
  v ->> 'Release' as vulnerability_package_release,
  v ->> 'Remediation' as vulnerability_package_remediation,
  v ->> 'SourceLambdaLayerArn' as source_lambda_layer_arn,
  v ->> 'Name' as source_layer_hash
from
  aws_inspector2_finding as f,
  jsonb_array_elements(vulnerable_packages) as v;