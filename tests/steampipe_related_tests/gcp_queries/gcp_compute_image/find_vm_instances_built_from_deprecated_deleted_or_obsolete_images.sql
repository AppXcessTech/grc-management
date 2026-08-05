select
  vm.name as instance_name,
  d.name as disk_name,
  img.name as image,
  img.creation_timestamp as image_creation_time,
  age(img.creation_timestamp) as image_age,
  img.deprecation_state
from
  gcp_compute_instance as vm,
  jsonb_array_elements(vm.disks) as vmd,
  gcp_compute_disk as d,
  gcp_compute_image as img
where
  vmd ->> 'source' = d.self_link
  and (vmd ->> 'boot') :: bool
  and d.source_image = img.self_link
  and deprecation_state != 'ACTIVE';