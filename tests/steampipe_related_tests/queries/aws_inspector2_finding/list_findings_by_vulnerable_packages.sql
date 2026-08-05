select
  arn,
  finding_account_id,
  first_observed_at,
  fix_available,
  exploit_available,
  vulnerable_package
from
  aws_inspector2_finding
where
  vulnerable_package = '[{"architecture": "arc", "epoch": "231321", "name": "myVulere", "release": "v0.2.0", "sourceLambdaLayerArn": "arn:aws:lambda:us-west-2:123456789012:layer:my-layer:1", "sourceLayerHash": "dbasjkhda872", "version": "v0.1.0"}]';