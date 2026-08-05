select
  hub_arn,
  auto_enable_controls,
  administrator_account ->> 'AccountId' as administrator_account_id,
  administrator_account ->> 'InvitationId' as administrator_invitation_id,
  administrator_account ->> 'InvitedAt' as administrator_invitation_time,
  administrator_account ->> 'MemberStatus' as administrator_status
from
  aws_securityhub_hub
where
  administrator_account is not null;