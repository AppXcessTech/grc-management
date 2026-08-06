select
 id,
 display_name,
 real_name,
 email,
 (regexp_match(email, '@(.+)')) [ 1 ] as domain,
 (regexp_match(tz, '^.+/(.+)')) [ 1 ] as city,
 (regexp_match(tz, '^(.+)/')) [ 1 ] as region,
 updated
from
  slack_user;