select
  vm.name as instance_name,
  d.name as disk_name,
  d.source_image
from
  gcp_compute_instance as vm,
  jsonb_array_elements(vm.disks) as vmd,
  gcp_compute_disk as d
where
  vmd ->> 'source' = d.self_link
  and (vmd ->> 'boot') :: bool
  and d.source_image like '%debian-10-buster-v20201014';