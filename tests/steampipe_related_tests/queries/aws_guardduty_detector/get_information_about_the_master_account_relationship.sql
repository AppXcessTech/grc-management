select 
  detector_id,
  master_account ->> 'AccountId' as master_account_id,
  master_account ->> 'InvitationId' as invitation_id, 
  master_account ->> 'RelationshipStatus' as relationship_status 
from    
  aws_guardduty_detector
where master_account is not null;