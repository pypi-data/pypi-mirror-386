from trajectory.scorers.api_scorer import APIScorerConfig
from trajectory.constants import APIScorerType
from trajectory.data import ExampleParams
from typing import List


class AnswerRelevancyScorer(APIScorerConfig):
    score_type: APIScorerType = APIScorerType.ANSWER_RELEVANCY
    required_params: List[ExampleParams] = [
        ExampleParams.INPUT,
        ExampleParams.ACTUAL_OUTPUT,
    ]
