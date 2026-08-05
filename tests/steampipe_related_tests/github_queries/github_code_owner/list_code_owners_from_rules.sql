select
  line,
  pattern,
  users,
  teams,
  pre_comments,
  line_comment,
  repository_full_name
from
  github_code_owner
where
  repository_full_name = 'github/docs'
order by
  line asc;