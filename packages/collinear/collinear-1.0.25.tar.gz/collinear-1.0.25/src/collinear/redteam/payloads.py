"""Pure functions for constructing red-team API payloads."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING
from typing import cast

if TYPE_CHECKING:
    from collinear.redteam.schemas import RedteamConfig


def build_redteam_payload(
    config: RedteamConfig,
    *,
    max_prompts: int | None = None,
) -> dict[str, object]:
    """Construct API payload from validated config.

    Args:
        config: Validated red-team configuration
        max_prompts: Optional limit on number of behaviors to load from dataset

    Returns:
        JSON-serializable payload for the redteam API

    Note:
        selected_behaviors is not included in the payload. The attack plan is
        loaded automatically on the server.

    """
    payload: dict[str, object] = {
        "attacker_config": cast("dict[str, object]", dataclasses.asdict(config.attacker)),
        "target_config": cast("dict[str, object]", dataclasses.asdict(config.target)),
        "evaluation_config": cast("dict[str, object]", dataclasses.asdict(config.evaluation)),
        "max_workers": config.max_workers,
    }

    if max_prompts is not None:
        payload["max_prompts"] = max_prompts

    if config.judge_template is not None:
        payload["custom_judge_prompt"] = config.judge_template

    if config.scoring_policy is not None:
        payload["custom_scoring_policy"] = config.scoring_policy

    if config.detailed_policy is not None:
        payload["custom_detailed_policy"] = config.detailed_policy

    if config.target_system_prompt is not None:
        payload["target_system_prompt"] = config.target_system_prompt

    return payload


def build_generate_and_evaluate_payload(
    config: RedteamConfig,
    *,
    intents: list[str] | None = None,
    generator_config: dict[str, object] | None = None,
) -> dict[str, object]:
    """Construct API payload for generate-and-evaluate.

    Args:
        config: Validated red-team configuration used to fill attacker/target/evaluation.
        intents: Optional list of behavior intents to generate strategies for.
        generator_config: LLM configuration used for plan generation. If ``None``,
            falls back to the evaluation model configuration.

    Returns:
        JSON-serializable payload matching the backend contract.

    """
    payload: dict[str, object] = {
        "attacker_config": cast("dict[str, object]", dataclasses.asdict(config.attacker)),
        "target_config": cast("dict[str, object]", dataclasses.asdict(config.target)),
        "evaluation_config": cast("dict[str, object]", dataclasses.asdict(config.evaluation)),
    }

    # Optional generator configuration: default to evaluation config if not provided
    gen_cfg: dict[str, object] = (
        generator_config
        if generator_config is not None
        else cast("dict[str, object]", dataclasses.asdict(config.evaluation))
    )
    payload["generator_config"] = gen_cfg

    # Optional custom parameters
    if config.judge_template is not None:
        payload["custom_judge_prompt"] = config.judge_template
    if config.scoring_policy is not None:
        payload["custom_scoring_policy"] = config.scoring_policy
    if config.detailed_policy is not None:
        payload["custom_detailed_policy"] = config.detailed_policy
    if config.target_system_prompt is not None:
        payload["target_system_prompt"] = config.target_system_prompt

    if intents:
        payload["intents"] = intents

    return payload
