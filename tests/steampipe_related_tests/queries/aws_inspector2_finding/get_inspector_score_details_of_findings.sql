select
  arn,
  inspector_score_details -> 'AdjustedCvss' ->> 'Score' as adjusted_cvss_score,
  inspector_score_details -> 'AdjustedCvss' ->> 'ScScoreSourceore' as adjusted_cvss_source_score,
  inspector_score_details -> 'AdjustedCvss' ->> 'ScoScoringVectorre' as adjusted_cvss_scoring_vector,
  inspector_score_details -> 'AdjustedCvss' ->> 'Version' as adjusted_cvss_version,
  inspector_score_details -> 'AdjustedCvss' -> 'Adjustments' as adjusted_cvss_adjustments,
  inspector_score_details -> 'AdjustedCvss' ->> 'CvssSource' as adjusted_cvss_cvss_source
from
  aws_inspector2_finding;