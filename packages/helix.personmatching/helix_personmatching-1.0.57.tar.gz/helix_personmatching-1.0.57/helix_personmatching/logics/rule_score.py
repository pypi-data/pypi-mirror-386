import json
from dataclasses import dataclass
from typing import List, Optional

from helix_personmatching.logics.rule_attribute_score import RuleAttributeScore
from helix_personmatching.models.rules.RuleWeight import RuleWeight
from helix_personmatching.utils.json_serializer import EnhancedJSONEncoder


@dataclass
class RuleScore:
    id_source: str
    id_target: str
    rule_name: str
    rule_description: str
    rule_score: float
    attribute_scores: List[RuleAttributeScore]
    rule_unweighted_score: float
    rule_weight: RuleWeight
    rule_boost: Optional[float] = None

    def to_json(self) -> str:
        return json.dumps(self, cls=EnhancedJSONEncoder)
