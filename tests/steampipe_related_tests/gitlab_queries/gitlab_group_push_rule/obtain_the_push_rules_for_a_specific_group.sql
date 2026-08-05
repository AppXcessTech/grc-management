select
  id,
  created_at,
  commit_message_regex,
  commit_message_negative_regex,
  branch_name_regex,
  deny_delete_tag,
  member_check,
  prevent_secrets,
  author_email_regex,
  file_name_regex,
  max_file_size,
  commit_committer_check,
  reject_unsigned_commits
from
  gitlab_group_push_rule
where
  group_id = 14597683;