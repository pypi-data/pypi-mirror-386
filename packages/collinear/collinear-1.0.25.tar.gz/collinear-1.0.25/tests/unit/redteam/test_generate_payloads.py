"""Tests for building generate-and-evaluate payloads."""

from collinear.redteam.payloads import build_generate_and_evaluate_payload
from collinear.redteam.schemas import ModelConfig
from collinear.redteam.schemas import RedteamConfig


def _cfg() -> RedteamConfig:
    attacker = ModelConfig(model="a")
    target = ModelConfig(model="b")
    eval_ = ModelConfig(model="c")
    return RedteamConfig(
        attacker=attacker,
        target=target,
        evaluation=eval_,
        judge_template="JT",
        scoring_policy="SP",
        detailed_policy="DP",
        target_system_prompt="TSP",
    )


def test_build_generate_payload_includes_required_and_optional_fields() -> None:
    """Builder includes attacker/target/evaluation, generator and optional fields."""
    # Default generator mirrors evaluation config.
    payload = build_generate_and_evaluate_payload(
        _cfg(),
        intents=["a", "b"],
    )
    required = {
        "attacker_config",
        "target_config",
        "evaluation_config",
        "generator_config",
    }
    assert required <= payload.keys()
    assert payload["custom_judge_prompt"] == "JT"
    assert payload["custom_scoring_policy"] == "SP"
    assert payload["custom_detailed_policy"] == "DP"
    assert payload["target_system_prompt"] == "TSP"
    assert payload["intents"] == ["a", "b"]
