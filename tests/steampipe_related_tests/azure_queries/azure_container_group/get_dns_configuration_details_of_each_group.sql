select
  name,
  id,
  dns_config -> 'NameServers' as name_servers,
  dns_config ->> 'SearchDomains' as search_domains,
  dns_config ->> 'Options' as options
from
  azure_container_group;