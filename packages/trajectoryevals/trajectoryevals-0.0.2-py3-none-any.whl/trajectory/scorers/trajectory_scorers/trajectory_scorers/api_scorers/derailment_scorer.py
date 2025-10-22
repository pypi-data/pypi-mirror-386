"""
`judgeval` answer relevancy scorer

TODO add link to docs page for this scorer

"""

# Internal imports
from trajectory.scorers.api_scorer import APIScorerConfig
from trajectory.constants import APIScorerType


class DerailmentScorer(APIScorerConfig):
    score_type: APIScorerType = APIScorerType.DERAILMENT
