select
  instance_id,
  launch_template_data -> 'ImageId' as image_id,
  launch_template_data -> 'Placement' as placement,
  launch_template_data -> 'DisableApiStop' as disable_api_stop,
  launch_template_data -> 'MetadataOptions' as metadata_options,
  launch_template_data -> 'NetworkInterfaces' as network_interfaces,
  launch_template_data -> 'BlockDeviceMappings' as block_device_mappings,
  launch_template_data -> 'CapacityReservationSpecification' as capacity_reservation_specification
from
  aws_ec2_instance;