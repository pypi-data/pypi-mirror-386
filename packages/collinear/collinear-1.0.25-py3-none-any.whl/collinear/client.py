"""Main Client class for Collinear SDK."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import cast

from collinear.assess.local import LocalGuardConfig
from collinear.assess.local import LocalSafetyAssessor
from collinear.redteam.client import RedteamHandle
from collinear.redteam.orchestrator import RedteamOrchestrator
from collinear.redteam.policies import DEFAULT_DETAILED_POLICY
from collinear.redteam.policies import DEFAULT_JUDGE_TEMPLATE
from collinear.redteam.policies import DEFAULT_SCORING_POLICY
from collinear.redteam.schemas import ModelConfig
from collinear.redteam.schemas import RedteamConfig
from collinear.schemas.assessment import AssessmentResponse
from collinear.schemas.traitmix import SimulationResult
from collinear.schemas.traitmix import TraitMixConfig
from collinear.schemas.traitmix import TraitMixConfigInput
from collinear.simulate.runner import SimulationRunner


class Client:
    """Main client for Collinear simulation."""

    def __init__(
        self,
        assistant_model_url: str,
        assistant_model_api_key: str,
        assistant_model_name: str,
        *,
        collinear_api_key: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_retries: int = 6,
    ) -> None:
        """Initialize the Collinear client.

        Args:
            assistant_model_url: OpenAI-compatible endpoint URL for the assistant model.
            assistant_model_api_key: API key for the assistant model.
            assistant_model_name: Assistant model name to use (required).
            collinear_api_key: Collinear API key used to call the Collinear traitmix
                endpoint for generating USER turns.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            rate_limit_retries: Maximum retries for rate limit errors (with exponential backoff).

        """
        if not assistant_model_name:
            raise ValueError("model_name is required")
        self.assistant_model_url = assistant_model_url
        self.assistant_model_api_key = assistant_model_api_key
        self.assistant_model_name = assistant_model_name
        if not collinear_api_key:
            raise ValueError("COLLINEAR_API_KEY is required")
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_retries = rate_limit_retries
        self.logger = logging.getLogger("collinear")
        self._simulation_runner: SimulationRunner | None = None
        self.redteam_orchestrator_cache: RedteamOrchestrator | None = None
        self._collinear_api_key = collinear_api_key

    @property
    def simulation_runner(self) -> SimulationRunner:
        """Lazy load simulation runner."""
        if self._simulation_runner is None:
            self._simulation_runner = SimulationRunner(
                assistant_model_url=self.assistant_model_url,
                assistant_model_api_key=self.assistant_model_api_key,
                assistant_model_name=self.assistant_model_name,
                collinear_api_key=self._collinear_api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
                rate_limit_retries=self.rate_limit_retries,
            )
        return self._simulation_runner

    @property
    def redteam_orchestrator(self) -> RedteamOrchestrator:
        """Lazy load redteam orchestrator."""
        if self.redteam_orchestrator_cache is None:
            self.redteam_orchestrator_cache = RedteamOrchestrator(
                timeout=self.timeout,
            )
        return self.redteam_orchestrator_cache

    def simulate(
        self,
        traitmix_config: TraitMixConfigInput,
        k: int | None = None,
        num_exchanges: int = 2,
        batch_delay: float = 0.1,
        *,
        traitmix_temperature: float | None = None,
        traitmix_max_tokens: int | None = None,
        traitmix_seed: int | None = None,
        assistant_max_tokens: int | None = None,
        assistant_seed: int | None = None,
        mix_traits: bool = False,
        progress: bool = True,
        max_concurrency: int = 1,
    ) -> list[SimulationResult]:
        """Run simulations with traitmixs against the model.

        Args:
            traitmix_config: Configuration dict with traitmixs, intents, traits.
                Expected keys:
                  - "ages": list[str] (age buckets such as "25-34")
                  - "genders": list[str]
                  - "occupations": list[str]
                  - "intents": list[str]
                  - "traits": dict[str, list[str]]  (trait -> levels in {"low","medium","high"})
                  - "languages": list[str]
                  - "locations": list[str]
                  - "task": str | "tasks": list[str]
            k: Optional number of simulation samples to generate. If ``None``,
                runs all available combinations.
            num_exchanges: Number of user-assistant exchanges (e.g., 2 = 2 user
                turns + 2 assistant turns)
            batch_delay: Delay between simulations to avoid rate limits
                (seconds)
            traitmix_temperature: Optional temperature for the traitmix generator (default 0.7).
            traitmix_max_tokens: Optional max tokens for the traitmix generator (default 256).
            traitmix_seed: Optional deterministic seed for the traitmix generator (-1 uses
                service-side randomness).
            assistant_max_tokens: Optional max tokens for the assistant model. If not set,
                the backend default is used.
            assistant_seed: Optional deterministic seed for the assistant model (if supported
                by your provider). If not set, no seed is sent.
            mix_traits: If True, mix traits pairwise (exactly 2 traits per traitmix).
                Requires at least two traits with levels. Defaults to False
                (single-trait behavior).
            progress: Whether to display a tqdm-style progress bar tracking traitmix
                API calls. Defaults to ``True``.
            max_concurrency: Maximum number of simultaneous traitmix requests. Defaults to ``1``
                which uses the ``/traitmix`` endpoint for individual requests. Values ``> 1`` are
                grouped into batches (up to 8) and routed to the ``/traitmix_batch`` endpoint.

        Returns:
            List of simulation results with conv_prefix and response

        Note:
            The SDK implements automatic retry with backoff logic to handle rate limits.
            If you're hitting rate limits frequently, increase the batch_delay parameter.

        """
        config = TraitMixConfig.from_input(traitmix_config)

        runner = self.simulation_runner
        return runner.run(
            config=config,
            k=k,
            num_exchanges=num_exchanges,
            batch_delay=batch_delay,
            traitmix_temperature=traitmix_temperature,
            traitmix_max_tokens=traitmix_max_tokens,
            traitmix_seed=traitmix_seed,
            assistant_max_tokens=assistant_max_tokens,
            assistant_seed=assistant_seed,
            mix_traits=mix_traits,
            progress=progress,
            max_concurrency=max_concurrency,
        )

    def assess(
        self,
        dataset: list[SimulationResult],
        *,
        judge_model_url: str | None = None,
        judge_model_api_key: str | None = None,
        judge_model_name: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> AssessmentResponse:
        """Assess simulated data locally using a user-provided model.

        This bypasses the Collinear platform entirely. It prompts an OpenAI-compatible
        model with a safety rubric and returns a compact ``AssessmentResponse``.

        Args:
            dataset: List of simulation results to assess.
            judge_model_url: Optional override for the judge's endpoint URL.
            judge_model_api_key: Optional override for the judge's API key.
            judge_model_name: Optional override for the judge model name.
            temperature: Sampling temperature for the judge.
            max_tokens: Max tokens for the judge completion.

        Returns:
            AssessmentResponse with scores and rationales per conversation.

        """
        if not dataset:
            raise ValueError("Dataset cannot be empty")

        cfg = LocalGuardConfig(
            api_url=judge_model_url or self.assistant_model_url,
            api_key=judge_model_api_key or self.assistant_model_api_key,
            model=judge_model_name or self.assistant_model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=self.timeout,
        )
        assessor = LocalSafetyAssessor(cfg)
        return assessor.score_dataset(dataset)

    def redteam(
        self,
        *,
        max_turns: int | None = None,
        judge_template: str = DEFAULT_JUDGE_TEMPLATE,
        scoring_policy: str = DEFAULT_SCORING_POLICY,
        detailed_policy: str = DEFAULT_DETAILED_POLICY,
        target_system_prompt: str | None = None,
        attacker_model: str | None = None,
        target_model: str | None = None,
        eval_model: str | None = None,
        attacker_config: ModelConfig | None = None,
        target_config: ModelConfig | None = None,
        evaluation_config: ModelConfig | None = None,
        max_workers: int = 2,
        # Flow controls
        generate_plans: bool = False,
        intents: list[str] | None = None,
        generator_config: ModelConfig | None = None,
        max_prompts: int | None = None,
        # Verification controls
        auto_verify: bool = True,
        verify_scoring_criteria: str | None = None,
    ) -> RedteamHandle:
        """Run a red-team evaluation.

        Two modes:
        1. Evaluate with pre-existing strategies (default). Uses server-side attack
           strategies.
        2. Generate and evaluate custom intents. Provide ``intents`` to generate
           custom attack strategies.

        By default, results are automatically verified with GPT-5 judge after evaluation
        completes, adding detailed rationales explaining why jailbreaks succeeded or failed.

        Args:
            max_turns: Maximum conversation turns for each attack (optional, server
                default if not provided).
            judge_template: Judge prompt template (defaults to healthcare HIPAA
                policy).
            scoring_policy: Scoring policy description (defaults to 1-5 refusal
                scale).
            detailed_policy: Detailed policy for evaluation (defaults to PHI
                protection).
            target_system_prompt: System prompt for the target model.
            attacker_model: Model name for attacker (e.g., "gpt-4o-mini").
            target_model: Model name for target under test (e.g., "gpt-4o").
            eval_model: Model name for evaluation/judge (e.g., "gpt-4o").
            attacker_config: Full ModelConfig for attacker (overrides
                ``attacker_model``).
            target_config: Full ModelConfig for target (overrides ``target_model``).
            evaluation_config: Full ModelConfig for evaluator (overrides
                ``eval_model``).
            max_workers: Number of concurrent workers for evaluation.
            generate_plans: Whether to generate custom attack plans (deprecated and
                automatically inferred from intents).
            intents: Custom intents used to generate attack strategies. Providing
                intents uses the generate-and-evaluate endpoint automatically.
            generator_config: Optional configuration for the strategy generator
                model.
            max_prompts: Maximum number of behaviors sampled from the dataset (only
                used when intents is not provided).
            auto_verify: Whether to automatically verify results with GPT-5 judge
                after evaluation completes. Defaults to True. Set to False to disable
                automatic verification.
            verify_scoring_criteria: Optional custom scoring criteria for GPT-5
                verification. If not provided, uses default medical policy criteria
                focused on HIPAA compliance and healthcare safety.

        Returns:
            Handle for polling evaluation status and retrieving results

        Raises:
            ValueError: If max_turns is provided and not positive

        Note:
            For simple model selection, use attacker_model/target_model/eval_model.
            For advanced config (temperature, etc.), pass ModelConfig objects to *_config.

            To use pre-existing strategies: Call without intents and optionally set
            ``max_prompts`` to limit dataset size.
            To generate custom strategies: Provide an intents list.

            Verification: Results are automatically verified by default using GPT-5
            to add rationales. Disable with auto_verify=False or customize with
            verify_scoring_criteria for domain-specific policies.

        """
        if max_turns is not None and max_turns <= 0:
            msg = "max_turns must be positive"
            raise ValueError(msg)

        if attacker_config is not None:
            attacker = attacker_config
            if max_turns is not None:
                attacker.max_turns = max_turns
        else:
            attacker = ModelConfig(
                provider="openai_compat",
                model=attacker_model or self.assistant_model_name,
                base_url=self.assistant_model_url,
                api_key=self.assistant_model_api_key,
                temperature=0.3,
                max_turns=max_turns,  # Will be None if not provided
                max_retries=10,
                plan_revision=True,
                run_all_strategies=False,
                strategies_per_behavior=2,
                sets_per_behavior=1,
                strategies_per_set=2,
            )

        if target_config is not None:
            target = target_config
        else:
            target = ModelConfig(
                provider="openai_compat",
                model=target_model or self.assistant_model_name,
                base_url=self.assistant_model_url,
                api_key=self.assistant_model_api_key,
                temperature=0.0,
                max_retries=10,
            )

        if evaluation_config is not None:
            evaluation = evaluation_config
        else:
            evaluation = ModelConfig(
                provider="openai_compat",
                model=eval_model or self.assistant_model_name,
                base_url=self.assistant_model_url,
                api_key=self.assistant_model_api_key,
                temperature=0.0,
                max_retries=10,
                use_gpt_judge=True,
                judge_model=eval_model or self.assistant_model_name,
            )

        config = RedteamConfig(
            attacker=attacker,
            target=target,
            evaluation=evaluation,
            max_workers=max_workers,
            judge_template=judge_template,
            scoring_policy=scoring_policy,
            detailed_policy=detailed_policy,
            target_system_prompt=target_system_prompt,
        )
        # Optional generator config conversion to dict for transport
        gen_cfg_dict: dict[str, object] | None = None
        if generator_config is not None:
            gen_cfg_dict = cast("dict[str, object]", asdict(generator_config))

        return self.redteam_orchestrator.run(
            config,
            generate_plans=generate_plans,
            intents=intents,
            generator_config=gen_cfg_dict,
            max_prompts=max_prompts,
            auto_verify=auto_verify,
            verify_scoring_criteria=verify_scoring_criteria,
        )
