select
  server_vulnerability_properties,
  remediation,
  resource_details
from
  azure_security_center_sub_assessment
where
  server_vulnerability_properties ->> 'AssessedResourceType' =  'ServerVulnerabilityAssessment';