select
  insert_id,
  log_name,
  proto_payload -> 'authenticationInfo' as authentication_info,
  proto_payload -> 'authorizationInfo' as authorization_info,
  proto_payload -> 'serviceName' as service_name,
  proto_payload -> 'resourceName' as resource_name,
  proto_payload ->> '@type' as proto_payload_type,
  proto_payload ->> 'methodName' as method_name,
  proto_payload ->> 'callerIp' as caller_ip
from
  gcp_logging_log_entry
where
  filter = 'resource.type = "gce_instance" AND (severity = ERROR OR "error")';