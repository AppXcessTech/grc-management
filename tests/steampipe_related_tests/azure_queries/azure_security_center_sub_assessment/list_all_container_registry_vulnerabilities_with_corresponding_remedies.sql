select
  container_registry_vulnerability_properties,
  remediation,
  resource_details
from
  azure_security_center_sub_assessment
where
  container_registry_vulnerability_properties ->> 'AssessedResourceType' =  'ContainerRegistryVulnerability';