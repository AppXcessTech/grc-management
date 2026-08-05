select
  i.name as image_name,
  i.id image_id,
  i.instance_properties ->> 'machineType' as machine_type,
  t.creation_timestamp as machine_type_creation_timestamp,
  t.memory_mb as machine_type_memory_mb,
  t.maximum_persistent_disks as machine_type_maximum_persistent_disks,
  t.is_shared_cpu as machine_type_is_shared_cpu,
  t.zone as machine_type_zone,
  t.deprecated as machine_type_deprecated
from
  gcp_compute_machine_image as i,
  gcp_compute_machine_type as t
where
  t.name = (i.instance_properties ->> 'machineType') and t.zone = split_part(i.source_instance, '/', 9);