"""Orchestrator for red-team evaluation workflow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from collinear.redteam.client import RedteamClient
from collinear.redteam.client import RedteamHandle
from collinear.redteam.payloads import build_generate_and_evaluate_payload
from collinear.redteam.payloads import build_redteam_payload

if TYPE_CHECKING:
    from collinear.redteam.schemas import RedteamConfig


class RedteamOrchestrator:
    """Coordinates red-team evaluation workflow.

    Responsible for:
    - Managing the transport client lifecycle
    - Building API payloads from configuration
    - Initiating evaluations and returning handles for polling
    """

    def __init__(self, *, timeout: float = 30.0) -> None:
        """Initialize the orchestrator.

        Args:
            timeout: HTTP request timeout in seconds

        """
        self.timeout = timeout
        self.client: RedteamClient | None = None

    @property
    def redteam_client(self) -> RedteamClient:
        """Lazy-load the redteam transport client."""
        if self.client is None:
            self.client = RedteamClient(timeout=self.timeout)
        return self.client

    def run(
        self,
        config: RedteamConfig,
        *,
        generate_plans: bool = False,
        intents: list[str] | None = None,
        generator_config: dict[str, object] | None = None,
        max_prompts: int | None = None,
        auto_verify: bool = True,
        verify_scoring_criteria: str | None = None,
    ) -> RedteamHandle:
        """Execute a red-team evaluation.

        If ``intents`` are provided, automatically uses the generate-and-evaluate
        endpoint. Otherwise, uses the evaluate endpoint which loads pre-existing
        strategies from the dataset.

        Args:
            config: Validated red-team configuration.
            generate_plans: Whether to use plan generation plus evaluate flow
                (deprecated and automatically inferred from intents).
            intents: Optional intents for generation. Providing intents
                automatically triggers plan generation.
            generator_config: Optional LLM config for generation (dict form).
            max_prompts: Optional limit on behaviors to load from the dataset
                (evaluate only).
            auto_verify: Whether to automatically verify results with GPT-5 judge
                after evaluation completes. Defaults to True.
            verify_scoring_criteria: Optional custom scoring criteria for verification.
                If not provided, uses default medical policy criteria.

        Returns:
            Handle for polling evaluation status and retrieving results.

        """
        # Auto-infer generate_plans from intents presence
        if intents is not None:
            generate_plans = True

        if generate_plans:
            payload = build_generate_and_evaluate_payload(
                config,
                intents=intents,
                generator_config=generator_config,
            )
            started = self.redteam_client.start_generate_and_evaluate(payload)
            err_msg = "SDK generate-and-evaluate did not return an evaluation_id."
        else:
            payload = build_redteam_payload(config, max_prompts=max_prompts)
            started = self.redteam_client.start(payload)
            err_msg = "SDK redteam evaluate did not return an evaluation_id."

        eval_id = str(started.get("evaluation_id") or "")
        if not eval_id:
            raise RuntimeError(err_msg)

        return RedteamHandle(
            api=self.redteam_client,
            evaluation_id=eval_id,
            initial=started,
            auto_verify=auto_verify,
            verify_scoring_criteria=verify_scoring_criteria,
        )
