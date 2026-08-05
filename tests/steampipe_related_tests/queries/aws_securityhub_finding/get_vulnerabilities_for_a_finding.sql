select
  title,
  v ->> 'Id' as vulnerabilitie_id,
  v -> 'Vendor' ->> 'Name' as vendor_name,
  v -> 'Vendor' ->> 'Url' as vendor_url,
  v -> 'Vendor' ->> 'VendorCreatedAt' as vendor_created_at,
  v -> 'Vendor' ->> 'VendorSeverity' as vendor_severity,
  v -> 'Vendor' ->> 'VendorUpdatedAt' as vendor_updated_at,
  v ->> 'Cvss' as cvss,
  v ->> 'ReferenceUrls' as reference_urls,
  v ->> 'RelatedVulnerabilities' as related_vulnerabilities,
  v ->> 'VulnerablePackages' as vulnerable_packages
from
  aws_securityhub_finding,
  jsonb_array_elements(vulnerabilities) as v
where
  title = 'EC2 instance involved in SSH brute force attacks.';