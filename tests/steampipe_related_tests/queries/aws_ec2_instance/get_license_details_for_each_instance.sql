select
  instance_id,
  instance_type,
  instance_state,
  l ->> 'LicenseConfigurationArn' as license_configuration_arn
from
  aws_ec2_instance,
  jsonb_array_elements(licenses) as l;