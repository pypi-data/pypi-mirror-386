"""
This module contains utility functions for judge models.
"""

import litellm
from typing import Optional, Union, Tuple, List

from trajectory.common.exceptions import InvalidJudgeModelError
from trajectory.judges import TrajectoryJudge, LiteLLMJudge, TogetherJudge, MixtureOfJudges
from trajectory.constants import (
    TOGETHER_SUPPORTED_MODELS,
    JUDGMENT_SUPPORTED_MODELS,
    ACCEPTABLE_MODELS,
)

LITELLM_SUPPORTED_MODELS = set(litellm.model_list)


def create_judge(
    model: Optional[Union[str, List[str], TrajectoryJudge]] = None,
) -> Tuple[TrajectoryJudge, bool]:
    """
    Creates a judge model from string(s) or a judgeval judge object.

    If `model` is a single string, it is assumed to be a judge model name.
    If `model` is a list of strings, it is assumed to be a list of judge model names (for MixtureOfJudges).
    If `model` is a judgeval judge object, it is returned as is.

    Returns a tuple of (initialized judgevalBaseLLM, using_native_model boolean)
    If no model is provided, uses GPT4o as the default judge.
    """
    if model is None:  # default option
        return LiteLLMJudge(model="gpt-4.1"), True
    if not isinstance(model, (str, list, TrajectoryJudge)):
        raise InvalidJudgeModelError(
            f"Model must be a string, list of strings, or a judgeval judge object. Got: {type(model)} instead."
        )
    # If model is already a valid judge type, return it and mark native
    if isinstance(model, (TrajectoryJudge, LiteLLMJudge, TogetherJudge, MixtureOfJudges)):
        return model, True

    # Either string or List[str]
    if isinstance(model, list):
        for m in model:
            if m in JUDGMENT_SUPPORTED_MODELS:
                raise NotImplementedError(
                    """Judgment models are not yet supported for local scoring.
                    Please either set the `use_judgment` flag to True or use 
                    non-Judgment models."""
                )
            if m not in ACCEPTABLE_MODELS:
                raise InvalidJudgeModelError(f"Invalid judge model chosen: {m}")
        return MixtureOfJudges(models=model), True
    # If model is a string, check that it corresponds to a valid model
    if model in LITELLM_SUPPORTED_MODELS:
        return LiteLLMJudge(model=model), True
    if model in TOGETHER_SUPPORTED_MODELS:
        return TogetherJudge(model=model), True
    if model in JUDGMENT_SUPPORTED_MODELS:
        raise NotImplementedError(
            """Judgment models are not yet supported for local scoring.
            Please either set the `use_judgment` flag to True or use 
            non-Judgment models."""
        )
    else:
        raise InvalidJudgeModelError(f"Invalid judge model chosen: {model}")
