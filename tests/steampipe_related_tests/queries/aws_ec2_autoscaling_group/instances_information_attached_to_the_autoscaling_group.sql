select
  name as autoscaling_group_name,
  ins_detail ->> 'InstanceId' as instance_id,
  ins_detail ->> 'InstanceType' as instance_type,
  ins_detail ->> 'AvailabilityZone' as az,
  ins_detail ->> 'HealthStatus' as health_status,
  ins_detail ->> 'LaunchConfigurationName' as launch_configuration_name,
  ins_detail -> 'LaunchTemplate' ->> 'LaunchTemplateName' as launch_template_name,
  ins_detail -> 'LaunchTemplate' ->> 'Version' as launch_template_version,
  ins_detail ->> 'ProtectedFromScaleIn' as protected_from_scale_in
from
  aws_ec2_autoscaling_group,
  jsonb_array_elements(instances) as ins_detail;