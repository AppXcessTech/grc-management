select
  name,
  id,
  disk ->> 'deviceName' as disk_device_name,
  disk -> 'initializeParams' ->> 'diskType' as disk_type,
  disk -> 'initializeParams' ->> 'diskSizeGb' as disk_size_gb,
  split_part(
    disk -> 'initializeParams' ->> 'sourceImage',
    '/',
    5
  ) as source_image,
  disk ->> 'mode' as mode
from
  gcp_compute_instance_template,
  jsonb_array_elements(instance_disks) as disk;