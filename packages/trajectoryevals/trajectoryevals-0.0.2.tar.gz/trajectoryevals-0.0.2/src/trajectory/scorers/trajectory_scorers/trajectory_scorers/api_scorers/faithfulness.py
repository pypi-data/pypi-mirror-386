"""
`judgeval` faithfulness scorer

TODO add link to docs page for this scorer

"""

# Internal imports
from trajectory.scorers.api_scorer import APIScorerConfig
from trajectory.constants import APIScorerType
from trajectory.data import ExampleParams
from typing import List


class FaithfulnessScorer(APIScorerConfig):
    score_type: APIScorerType = APIScorerType.FAITHFULNESS
    required_params: List[ExampleParams] = [
        ExampleParams.INPUT,
        ExampleParams.ACTUAL_OUTPUT,
        ExampleParams.RETRIEVAL_CONTEXT,
    ]
