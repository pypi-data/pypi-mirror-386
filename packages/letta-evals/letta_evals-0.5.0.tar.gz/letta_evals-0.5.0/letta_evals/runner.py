import inspect
import json
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import anyio
import yaml
from letta_client import AgentState, AsyncLetta, LettaMessageUnion, LlmConfig
from rich.console import Console

from letta_evals.datasets.loader import load_dataset
from letta_evals.graders.agent_judge import AgentJudgeGrader
from letta_evals.graders.base import Grader
from letta_evals.graders.rubric import RubricGrader
from letta_evals.graders.tool import ToolGrader
from letta_evals.models import (
    GradeResult,
    LettaJudgeGraderSpec,
    MetricAggregate,
    Metrics,
    ModelJudgeGraderSpec,
    ModelMetrics,
    RunnerResult,
    RunStatistics,
    Sample,
    SampleResult,
    SuiteSpec,
    ToolGraderSpec,
)
from letta_evals.streaming import StreamingReader, StreamingWriter
from letta_evals.targets.agent import AgentTarget
from letta_evals.targets.base import Target
from letta_evals.types import GateMetric, TargetKind
from letta_evals.utils import load_object
from letta_evals.visualization.base import ProgressCallback
from letta_evals.visualization.factory import ProgressStyle, create_progress_callback

logger = logging.getLogger(__name__)


class Runner:
    """Main evaluation runner."""

    def __init__(
        self,
        suite: SuiteSpec,
        max_concurrent: int,
        progress_callback: Optional[ProgressCallback] = None,
        cached_results: Optional[RunnerResult] = None,
        output_path: Optional[Path] = None,
        letta_api_key: Optional[str] = None,
        letta_base_url: Optional[str] = None,
        letta_project_id: Optional[str] = None,
    ):
        self.suite: SuiteSpec = suite

        env_api_key = os.getenv("LETTA_API_KEY")
        env_base_url = os.getenv("LETTA_BASE_URL")
        env_project_id = os.getenv("LETTA_PROJECT_ID")

        # priority: cli arg > yaml suite config > env var
        token = letta_api_key or self.suite.target.api_key or env_api_key
        base_url = letta_base_url or self.suite.target.base_url or env_base_url
        self.project_id = letta_project_id or self.suite.target.project_id or env_project_id

        client_kwargs: dict[str, object] = {"timeout": self.suite.target.timeout}
        if base_url:
            client_kwargs["base_url"] = base_url
        if token:
            client_kwargs["token"] = token

        self.client = AsyncLetta(**client_kwargs)

        self.graders: Optional[Dict[str, Grader]] = None
        self._init_graders()

        self.results: List[SampleResult] = []
        self.max_concurrent = max_concurrent
        self.semaphore = anyio.Semaphore(max_concurrent)
        self.progress_callback = progress_callback
        self.model_configs = self._load_model_configs()
        self.cached_results = cached_results
        self._cached_trajectories: Dict[int, Dict[str, SampleResult]] = (
            self._build_trajectory_cache() if cached_results else {}
        )
        self._setup_executed = False
        self.stream_writer: Optional[StreamingWriter] = None
        self.output_path = output_path

    def _load_model_configs(self) -> List[Optional[LlmConfig | str]]:
        """Load model configurations and handles if specified."""
        has_configs = self.suite.target.model_configs is not None
        has_handles = self.suite.target.model_handles is not None

        if not has_configs and not has_handles:
            return [None]  # no model configs or handles, use default

        if has_configs and has_handles:
            raise ValueError("Cannot specify both model_configs and model_handles in target spec")

        configs = []

        # load model configs from JSON files
        if has_configs:
            model_configs_dir = Path(__file__).parent / "llm_model_configs"
            for config_name in self.suite.target.model_configs:
                config_path = model_configs_dir / f"{config_name}.json"
                if not config_path.exists():
                    raise ValueError(f"Model config not found at path: {config_path}")

                with open(config_path, "r") as f:
                    config_data = json.load(f)
                    llm_config = LlmConfig(**config_data)
                    configs.append(llm_config)

        # load model handles as strings
        if has_handles:
            for handle in self.suite.target.model_handles:
                configs.append(handle)

        return configs

    def _create_target(self, llm_config: Optional[LlmConfig | str] = None) -> Target:
        """Create target from spec, optionally with model config or handle."""
        if self.suite.target.kind == TargetKind.AGENT:
            # check both before reassigning
            model_handle = llm_config if isinstance(llm_config, str) else None
            actual_llm_config = llm_config if isinstance(llm_config, LlmConfig) else None

            return AgentTarget(
                client=self.client,
                agent_id=self.suite.target.agent_id,
                agent_file=self.suite.target.agent_file,
                agent_script=self.suite.target.agent_script,
                base_dir=self.suite.target.base_dir,
                llm_config=actual_llm_config,
                model_handle=model_handle,
                max_retries=self.suite.target.max_retries,
            )
        else:
            raise ValueError(f"Unknown target kind: {self.suite.target.kind}")

    def _init_graders(self) -> None:
        """Initialize grader(s) from spec."""
        if self.suite.graders:
            self.graders = {}
            for key, gspec in self.suite.graders.items():
                if isinstance(gspec, ToolGraderSpec):
                    self.graders[key] = ToolGrader(
                        function=gspec.function,
                        extractor=gspec.extractor,
                        extractor_config=gspec.extractor_config,
                        base_dir=gspec.base_dir,
                    )
                elif isinstance(gspec, ModelJudgeGraderSpec):
                    self.graders[key] = RubricGrader(
                        prompt=gspec.prompt,
                        model=gspec.model,
                        temperature=gspec.temperature,
                        provider=gspec.provider,
                        max_retries=gspec.max_retries,
                        timeout=gspec.timeout,
                        extractor=gspec.extractor,
                        extractor_config=gspec.extractor_config,
                        base_dir=gspec.base_dir,
                        rubric_vars=gspec.rubric_vars,
                    )
                elif isinstance(gspec, LettaJudgeGraderSpec):
                    # use default agent file if not provided
                    agent_file = gspec.agent_file
                    judge_tool_name = gspec.judge_tool_name
                    if agent_file is None:
                        agent_file = Path(__file__).parent / "graders/letta-evals-judge-agent.af"
                        judge_tool_name = "submit_grade"

                    self.graders[key] = AgentJudgeGrader(
                        agent_file=agent_file,
                        prompt=gspec.prompt,
                        client=self.client,
                        project_id=self.project_id,
                        judge_tool_name=judge_tool_name,
                        extractor=gspec.extractor,
                        extractor_config=gspec.extractor_config,
                        base_dir=gspec.base_dir,
                        rubric_vars=gspec.rubric_vars,
                    )
                else:
                    raise ValueError(f"Unknown grader spec type: {type(gspec)}")
        else:
            raise ValueError("Suite must define 'graders'")

    def _requires_agent_state(self) -> bool:
        """Check if any grader requires agent_state for extraction."""
        if self.graders:
            return any(grader.requires_agent_state for grader in self.graders.values())
        return False

    async def _run_setup(self) -> None:
        """Execute the setup function if specified."""
        if self._setup_executed:
            return

        if not self.suite.setup_script:
            return

        try:
            logger.info(f"Running setup script: {self.suite.setup_script}")
            setup_func = load_object(self.suite.setup_script, self.suite.base_dir)
            if not hasattr(setup_func, "_is_suite_setup"):
                raise ValueError(f"Setup function must be decorated with @suite_setup: {self.suite.setup_script}")

            if inspect.iscoroutinefunction(setup_func):
                await setup_func(self.client)
            else:
                setup_func(self.client)

            self._setup_executed = True
            logger.info("Setup completed successfully")

        except Exception as e:
            logger.error(f"Error running setup script: {e}")
            raise RuntimeError(f"Setup failed: {e}") from e

    def _build_trajectory_cache(self) -> Dict[int, Dict[str, SampleResult]]:
        """Build a cache of sample results indexed by sample_id -> model_name -> SampleResult."""
        cache: Dict[int, Dict[str, SampleResult]] = defaultdict(dict)
        if self.cached_results:
            for result in self.cached_results.results:
                # use model_name as key, or None if not specified
                model_key = result.model_name if result.model_name else None
                cache[result.sample.id][model_key] = result
        return cache

    async def _get_or_run_trajectory(
        self, sample: Sample, llm_config: Optional[LlmConfig | str], retrieve_agent_state: bool = False
    ) -> tuple[List[List[LettaMessageUnion]], str, str, Optional[list[dict]], Optional[AgentState]]:
        """Return (trajectory, agent_id, model_name, agent_usage, agent_state) using cache or by running the target.

        If cache is enabled and contains an exact match, use it; otherwise run the target.
        """
        sample_id = sample.id
        # extract model name from either LlmConfig or string handle
        if isinstance(llm_config, LlmConfig):
            model_name = llm_config.model
        elif isinstance(llm_config, str):
            model_name = llm_config
        else:
            model_name = None

        if self.cached_results:
            cached_result: Optional[SampleResult] = None
            cached_models = self._cached_trajectories.get(sample_id)

            if cached_models:
                if model_name is not None:
                    cached_result = cached_models.get(model_name)
                else:
                    if len(cached_models) == 1:
                        cached_result = next(iter(cached_models.values()))
                        model_name = cached_result.model_name

            if cached_result is not None:
                if self.progress_callback:
                    await self.progress_callback.agent_loading(sample_id, model_name=model_name, from_cache=True)
                return (
                    cached_result.trajectory,
                    cached_result.agent_id,
                    model_name,
                    getattr(cached_result, "agent_usage", None),
                    getattr(cached_result, "agent_state", None),
                )

        target = self._create_target(llm_config)
        target_result = await target.run(
            sample,
            progress_callback=self.progress_callback,
            project_id=self.project_id,
            retrieve_agent_state=retrieve_agent_state,
        )
        return (
            target_result.trajectory,
            target_result.agent_id,
            target_result.model_name,
            target_result.agent_usage,
            target_result.agent_state,
        )

    async def run_sample(self, sample: Sample, llm_config: Optional[LlmConfig | str] = None) -> SampleResult:
        """Run a single sample through target and grader."""
        sample_id = sample.id
        # extract model name from either LlmConfig or string handle
        if isinstance(llm_config, LlmConfig):
            model_name = llm_config.model
        elif isinstance(llm_config, str):
            model_name = llm_config
        else:
            model_name = None

        async with self.semaphore:
            agent_id = None
            try:
                if self.progress_callback:
                    await self.progress_callback.sample_started(sample_id, model_name=model_name)

                # check if any grader needs agent_state
                retrieve_agent_state = self._requires_agent_state()
                trajectory, agent_id, model_name, agent_usage, agent_state = await self._get_or_run_trajectory(
                    sample, llm_config, retrieve_agent_state=retrieve_agent_state
                )

                if self.progress_callback:
                    await self.progress_callback.grading_started(sample_id, agent_id=agent_id, model_name=model_name)

                grades_dict: Optional[Dict[str, GradeResult]] = {}
                submissions_dict: Optional[Dict[str, str]] = {}
                for key, grader in self.graders.items():  # type: ignore[union-attr]
                    gr, sub = await grader.grade(sample, trajectory, agent_state=agent_state)
                    grades_dict[key] = gr
                    submissions_dict[key] = sub
                # Determine gating metric key
                gate_key = self._gate_metric_key()
                gate_grade = grades_dict.get(gate_key) if gate_key in grades_dict else next(iter(grades_dict.values()))
                gate_submission = (
                    submissions_dict.get(gate_key)
                    if gate_key in submissions_dict
                    else next(iter(submissions_dict.values()))
                )
                grade_result, submission = gate_grade, gate_submission

                if self.progress_callback:
                    passed = self._check_sample_pass(grade_result.score)
                    metric_scores = None
                    metric_pass = None
                    metric_rationales = None
                    if self.graders is not None and grades_dict is not None:
                        metric_scores = {k: v.score for k, v in grades_dict.items()}
                        metric_pass = {k: self._check_sample_pass(v) for k, v in metric_scores.items()}
                        metric_rationales = {k: (v.rationale or "") for k, v in grades_dict.items()}
                    await self.progress_callback.sample_completed(
                        sample_id,
                        passed=passed,
                        agent_id=agent_id,
                        score=grade_result.score,
                        model_name=model_name,
                        metric_scores=metric_scores,
                        metric_pass=metric_pass,
                        rationale=grade_result.rationale,
                        metric_rationales=metric_rationales,
                    )

                return SampleResult(
                    sample=sample,
                    submission=submission,
                    submissions=submissions_dict,
                    trajectory=trajectory,
                    agent_id=agent_id,
                    grade=grade_result,
                    grades=grades_dict,
                    model_name=model_name,
                    agent_usage=agent_usage,
                )
            except Exception as e:
                if self.progress_callback:
                    await self.progress_callback.sample_error(
                        sample_id, str(e), agent_id=agent_id, model_name=model_name
                    )
                raise

    def _validate_rubric_vars(self, samples: List[Sample]) -> None:
        """Validate that all samples have required rubric_vars for configured graders."""
        if not self.suite.graders:
            return

        for grader_key, grader_spec in self.suite.graders.items():
            # check if grader uses rubric_vars (model_judge or letta_judge)
            if not isinstance(grader_spec, (ModelJudgeGraderSpec, LettaJudgeGraderSpec)) or not grader_spec.rubric_vars:
                continue

            for sample in samples:
                if not sample.rubric_vars:
                    raise ValueError(
                        f"Sample {sample.id} is missing rubric_vars field. "
                        f"Grader '{grader_key}' requires variables: {', '.join(grader_spec.rubric_vars)}"
                    )

                missing_vars = [var for var in grader_spec.rubric_vars if var not in sample.rubric_vars]
                if missing_vars:
                    raise ValueError(
                        f"Sample {sample.id} is missing required rubric variables for grader '{grader_key}': "
                        f"{', '.join(missing_vars)}"
                    )

    async def run(self) -> RunnerResult:
        """Run evaluation on all samples."""
        await self._run_setup()

        samples = list(
            load_dataset(self.suite.dataset, max_samples=self.suite.max_samples, sample_tags=self.suite.sample_tags)
        )

        # validate rubric variables before running any samples
        self._validate_rubric_vars(samples)

        self.results = []
        # prepare config for both streaming and final result
        config: Dict[str, Any] = {
            "target": json.loads(self.suite.target.model_dump_json()),
            "gate": json.loads(self.suite.gate.model_dump_json()),
        }
        if self.suite.graders:
            config["graders"] = {k: json.loads(v.model_dump_json()) for k, v in self.suite.graders.items()}

        # initialize streaming writer if output path is provided
        if self.output_path:
            self.stream_writer = StreamingWriter(self.output_path, self.suite.name, config)
            await self.stream_writer.initialize()

        try:
            async with anyio.create_task_group() as tg:
                for llm_config in self.model_configs:
                    for sample in samples:

                        async def run_and_append(s, cfg):
                            try:
                                result = await self.run_sample(s, llm_config=cfg)
                                self.results.append(result)
                                if self.stream_writer:
                                    await self.stream_writer.append_result(result)
                            except Exception as e:
                                # extract model name from either LlmConfig or string handle
                                if isinstance(cfg, LlmConfig):
                                    model_name = cfg.model
                                elif isinstance(cfg, str):
                                    model_name = cfg
                                else:
                                    model_name = None
                                logger.error(f"Error running sample {s.id} with model {model_name}: {e}")
                                if self.progress_callback:
                                    await self.progress_callback.sample_error(s.id, str(e), model_name=model_name)

                                error_result = SampleResult(
                                    sample=s,
                                    submission="",
                                    submissions=None,
                                    trajectory=[],
                                    agent_id=None,
                                    grade=GradeResult(score=0.0, rationale=f"Error: {str(e)[:200]}"),
                                    grades=None,
                                    model_name=model_name,
                                    agent_usage=None,
                                )
                                self.results.append(error_result)
                                if self.stream_writer:
                                    await self.stream_writer.append_result(error_result)

                        tg.start_soon(run_and_append, sample, llm_config)

            metrics = self._calculate_metrics()
            gates_passed = self._check_gates(metrics)

            # write final metrics if streaming
            if self.stream_writer:
                await self.stream_writer.write_metrics(metrics, gates_passed)

            return RunnerResult(
                suite=self.suite.name, config=config, results=self.results, metrics=metrics, gates_passed=gates_passed
            )
        except BaseException:
            # On interruption or errors, write a best-effort summary for a valid JSONL
            try:
                metrics = self._calculate_metrics()
                gates_passed = self._check_gates(metrics)
                if self.stream_writer:
                    await self.stream_writer.write_metrics(metrics, gates_passed)
            finally:
                # Re-raise to preserve original error/interrupt semantics
                raise

    def _calculate_metrics(self) -> Metrics:
        """Calculate aggregate metrics from results.

        - total: success + error (all results)
        - total_attempted: success only (completed without error)
        - metrics: dict of metric_key -> pass rate percentage
        - avg_score: mean across all results (including error results)
        - per_model: same semantics per model (based on gate metric key)
        """
        total = len(self.results)
        if total == 0:
            return Metrics(
                total=0,
                total_attempted=0,
                avg_score_attempted=0.0,
                avg_score_total=0.0,
                passed_attempts=0,
                failed_attempts=0,
                metrics={},
            )

        # success = completed without error; error results have empty trajectory or missing agent_id
        def is_success(r: SampleResult) -> bool:
            return (r.agent_id is not None) and bool(r.trajectory)

        attempted = sum(1 for r in self.results if is_success(r))

        # Determine per-metric aggregates if multiple graders
        by_metric: Dict[str, MetricAggregate] = {}
        if self.graders is not None:
            for metric_key in self.graders.keys():
                m_scores = [r.grades[metric_key].score for r in self.results if r.grades and metric_key in r.grades]
                m_avg_attempted = sum(m_scores) / len(m_scores) if m_scores else 0.0
                m_avg_total = sum(m_scores) / len(self.results) if m_scores else 0.0
                m_passed = sum(
                    1
                    for r in self.results
                    if is_success(r)
                    and r.grades
                    and metric_key in r.grades
                    and self._check_sample_pass(r.grades[metric_key].score)
                )
                m_pass_rate = (m_passed / attempted) * 100.0 if attempted > 0 else 0.0
                by_metric[metric_key] = MetricAggregate(
                    avg_score_attempted=m_avg_attempted,
                    avg_score_total=m_avg_total,
                    pass_rate=m_pass_rate,
                    passed_attempts=m_passed,
                    failed_attempts=(attempted - m_passed),
                )

        metrics_dict: Dict[str, float] = {}
        if self.graders is not None:
            gate_key = self._gate_metric_key()
            for key, agg in by_metric.items():
                metrics_dict[key] = agg.pass_rate

            agg = (
                by_metric.get(gate_key)
                if gate_key in by_metric
                else (next(iter(by_metric.values())) if by_metric else None)
            )
            avg_score_attempted = agg.avg_score_attempted if agg else 0.0
            avg_score_total = agg.avg_score_total if agg else 0.0
            passed_attempts = agg.passed_attempts if agg else 0
        else:
            scores = [r.grade.score for r in self.results]
            avg_score_attempted = sum(scores) / len(scores) if scores else 0.0
            avg_score_total = sum(scores) / len(self.results) if scores else 0.0
            passed_attempts = sum(1 for r in self.results if is_success(r) and self._check_sample_pass(r.grade.score))
            # For single grader case, use a default key
            default_key = "default"
            metrics_dict[default_key] = (passed_attempts / attempted) * 100.0 if attempted > 0 else 0.0

        per_model = None
        if self.suite.target.model_configs or self.suite.target.model_handles:
            model_results = defaultdict(list)
            for result in self.results:
                model_results[result.model_name].append(result)

            per_model = []
            for model_name, results in model_results.items():
                model_attempted = sum(1 for r in results if is_success(r))
                model_metrics_dict: Dict[str, float] = {}

                if self.graders is not None:
                    gate_key = self._gate_metric_key()
                    # Calculate pass rate for each metric
                    for metric_key in self.graders.keys():
                        metric_passed = sum(
                            1
                            for r in results
                            if is_success(r)
                            and r.grades
                            and metric_key in r.grades
                            and self._check_sample_pass(r.grades[metric_key].score)
                        )
                        model_metrics_dict[metric_key] = (
                            (metric_passed / model_attempted) * 100.0 if model_attempted > 0 else 0.0
                        )

                    model_scores = [r.grades[gate_key].score for r in results if r.grades and gate_key in r.grades]
                    model_passed = sum(
                        1
                        for r in results
                        if is_success(r)
                        and r.grades
                        and gate_key in r.grades
                        and self._check_sample_pass(r.grades[gate_key].score)
                    )
                else:
                    model_scores = [r.grade.score for r in results]
                    model_passed = sum(1 for r in results if is_success(r) and self._check_sample_pass(r.grade.score))
                    default_key = "default"
                    model_metrics_dict[default_key] = (
                        (model_passed / model_attempted) * 100.0 if model_attempted > 0 else 0.0
                    )

                model_avg_attempted = sum(model_scores) / len(model_scores) if model_scores else 0.0
                model_avg_total = sum(model_scores) / len(results) if model_scores else 0.0

                per_model.append(
                    ModelMetrics(
                        model_name=model_name,
                        total=len(results),
                        total_attempted=model_attempted,
                        avg_score_attempted=model_avg_attempted,
                        avg_score_total=model_avg_total,
                        passed_samples=model_passed,
                        failed_samples=(model_attempted - model_passed),
                        metrics=model_metrics_dict,
                    )
                )

        return Metrics(
            total=total,
            total_attempted=attempted,
            avg_score_attempted=avg_score_attempted,
            avg_score_total=avg_score_total,
            passed_attempts=passed_attempts,
            failed_attempts=(attempted - passed_attempts),
            per_model=per_model,
            by_metric=by_metric if by_metric else None,
            metrics=metrics_dict,
        )

    def _check_sample_pass(self, score: float) -> bool:
        """Check if an individual score satisfies the per-sample pass criteria."""
        return self.suite.gate.check_sample(score)

    def _check_gates(self, metrics: Metrics) -> bool:
        """Check if the configured gate metric is satisfied."""
        metric_kind = self.suite.gate.metric
        gate_key = self._gate_metric_key()
        # recompute a lightweight aggregate for gate metric from current results
        if metric_kind == GateMetric.AVG_SCORE:
            scores = [r.grades[gate_key].score for r in self.results if r.grades and gate_key in r.grades]
            value = (sum(scores) / len(scores)) if scores else 0.0
        elif metric_kind == GateMetric.ACCURACY:
            # accuracy over attempted
            def is_success(r: SampleResult) -> bool:
                return (r.agent_id is not None) and bool(r.trajectory)

            attempted = sum(1 for r in self.results if is_success(r))
            passed = sum(
                1
                for r in self.results
                if is_success(r)
                and r.grades
                and gate_key in r.grades
                and self._check_sample_pass(r.grades[gate_key].score)
            )
            value = (passed / attempted) * 100.0 if attempted > 0 else 0.0
        else:
            value = 0.0
        return self.suite.gate._compare(value, self.suite.gate.op, self.suite.gate.value)

    def _gate_metric_key(self) -> str:
        """Return the selected metric key (grader name) for gating.

        If not specified, uses the only grader if single, otherwise the first in order.
        """
        if self.suite.gate.metric_key:
            return self.suite.gate.metric_key
        if self.graders is not None and len(self.graders) > 0:
            # return first key (deterministic by insertion order)
            return next(iter(self.graders.keys()))
        return "default"


def _calculate_run_statistics(all_metrics: List[Metrics], runs_passed: int, suite: SuiteSpec) -> RunStatistics:
    """Calculate aggregate statistics across multiple runs."""
    import statistics

    num_runs = len(all_metrics)

    avg_scores_attempted = [m.avg_score_attempted for m in all_metrics]
    avg_scores_total = [m.avg_score_total for m in all_metrics]

    mean_avg_score_attempted = statistics.mean(avg_scores_attempted)
    std_avg_score_attempted = statistics.stdev(avg_scores_attempted) if num_runs > 1 else 0.0

    mean_avg_score_total = statistics.mean(avg_scores_total)
    std_avg_score_total = statistics.stdev(avg_scores_total) if num_runs > 1 else 0.0

    mean_scores: Dict[str, float] = {}
    std_scores: Dict[str, float] = {}

    if suite.graders:
        for metric_key in suite.graders.keys():
            metric_values = []
            for m in all_metrics:
                if m.by_metric and metric_key in m.by_metric:
                    metric_values.append(m.by_metric[metric_key].avg_score_attempted)

            if metric_values:
                mean_scores[metric_key] = statistics.mean(metric_values)
                std_scores[metric_key] = statistics.stdev(metric_values) if len(metric_values) > 1 else 0.0

    return RunStatistics(
        num_runs=num_runs,
        runs_passed=runs_passed,
        mean_avg_score_attempted=mean_avg_score_attempted,
        std_avg_score_attempted=std_avg_score_attempted,
        mean_avg_score_total=mean_avg_score_total,
        std_avg_score_total=std_avg_score_total,
        mean_scores=mean_scores,
        std_scores=std_scores,
        individual_run_metrics=all_metrics,
    )


async def _write_aggregate_statistics(output_path: Path, run_statistics: RunStatistics) -> None:
    """Write aggregate statistics to a JSON file."""
    stats_file = output_path / "aggregate_stats.json"
    output_path.mkdir(parents=True, exist_ok=True)

    def _write() -> None:
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(json.loads(run_statistics.model_dump_json()), f, indent=2)

    await anyio.to_thread.run_sync(_write)


async def run_suite(
    suite_path: Path,
    max_concurrent: int,
    *,
    custom_progress_callback: Optional[ProgressCallback] = None,
    progress_style: ProgressStyle | str = ProgressStyle.NONE,
    cached_results_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    letta_api_key: Optional[str] = None,
    letta_base_url: Optional[str] = None,
    letta_project_id: Optional[str] = None,
    num_runs: Optional[int] = None,
) -> RunnerResult:
    """Load and run a suite from YAML file."""
    if custom_progress_callback is not None:
        style_val = progress_style if isinstance(progress_style, ProgressStyle) else ProgressStyle(progress_style)
        if style_val != ProgressStyle.NONE:
            raise ValueError(
                "Cannot specify both 'custom_progress_callback' and 'progress_style'. "
                "Use custom_progress_callback for custom implementations, or progress_style for built-in styles."
            )

    with open(suite_path, "r") as f:
        yaml_data = yaml.safe_load(f)

    suite = SuiteSpec.from_yaml(yaml_data, base_dir=suite_path.parent)

    actual_num_runs = num_runs if num_runs is not None else (suite.num_runs or 1)

    # Multiple runs don't make sense with cached results (trajectories would be identical)
    if actual_num_runs > 1 and cached_results_path:
        raise ValueError("Cannot use --num-runs > 1 with --cached (results would be identical)")

    cached_results = None
    if cached_results_path:
        if not cached_results_path.exists():
            raise ValueError(f"Cached results file not found: {cached_results_path}")

        cached_results = await StreamingReader.to_runner_result(cached_results_path)

        cached_sample_map = {result.sample.id: result.sample for result in cached_results.results}
        samples = list(load_dataset(suite.dataset, max_samples=suite.max_samples, sample_tags=suite.sample_tags))

        for sample in samples:
            if sample.id in cached_sample_map:
                cached_sample = cached_sample_map[sample.id]
                if cached_sample.input != sample.input:
                    raise ValueError(
                        f"Sample ID {sample.id} input mismatch: dataset has '{sample.input}' but cache has '{cached_sample.input}'"
                    )

    samples = list(load_dataset(suite.dataset, max_samples=suite.max_samples, sample_tags=suite.sample_tags))
    if suite.target.model_configs:
        num_models = len(suite.target.model_configs)
    elif suite.target.model_handles:
        num_models = len(suite.target.model_handles)
    else:
        num_models = 1
    total_evaluations = len(samples) * num_models

    metric_labels = None
    if suite.graders:
        metric_labels = {key: (gspec.display_name or key) for key, gspec in suite.graders.items()}

    if custom_progress_callback is not None:
        progress_cb = custom_progress_callback
    else:
        # Accept string value for style for external callers
        style_val = progress_style
        if isinstance(style_val, str):
            try:
                style_val = ProgressStyle(style_val)
            except ValueError:
                style_val = ProgressStyle.NONE
        progress_cb = create_progress_callback(
            style=style_val,  # type: ignore[arg-type]
            suite=suite,
            total_evaluations=total_evaluations,
            console=Console() if style_val == ProgressStyle.RICH else None,
            max_concurrent=max_concurrent,
            cached_mode=(cached_results_path is not None),
            metric_labels=metric_labels,
        )

    if actual_num_runs > 1:
        all_run_results: List[RunnerResult] = []
        all_metrics: List[Metrics] = []
        runs_passed = 0

        for run_idx in range(actual_num_runs):
            run_output_path = None
            if output_path:
                run_output_path = output_path / f"run_{run_idx + 1}"

            runner = Runner(
                suite,
                max_concurrent=max_concurrent,
                progress_callback=progress_cb,
                cached_results=cached_results,
                output_path=run_output_path,
                letta_api_key=letta_api_key,
                letta_base_url=letta_base_url,
                letta_project_id=letta_project_id,
            )

            if progress_cb is not None:
                if run_idx == 0:
                    await progress_cb.start()
                else:
                    progress_cb.reset()

            try:
                result = await runner.run()
                all_run_results.append(result)
                all_metrics.append(result.metrics)
                if result.gates_passed:
                    runs_passed += 1
            finally:
                if progress_cb is not None and run_idx == actual_num_runs - 1:
                    # stop live display first, then show summary
                    progress_cb.stop()
                    run_statistics = _calculate_run_statistics(all_metrics, runs_passed, suite)
                    final_result_temp = all_run_results[-1]
                    final_result_temp.run_statistics = run_statistics
                    final_result_temp.gates_passed = runs_passed > 0
                    await progress_cb.suite_completed(final_result_temp)

        run_statistics = _calculate_run_statistics(all_metrics, runs_passed, suite)

        if output_path:
            await _write_aggregate_statistics(output_path, run_statistics)

        final_result = all_run_results[-1]
        final_result.run_statistics = run_statistics
        final_result.gates_passed = runs_passed > 0
        return final_result
    else:
        runner = Runner(
            suite,
            max_concurrent=max_concurrent,
            progress_callback=progress_cb,
            cached_results=cached_results,
            output_path=output_path,
            letta_api_key=letta_api_key,
            letta_base_url=letta_base_url,
            letta_project_id=letta_project_id,
        )

        if progress_cb is not None:
            await progress_cb.start()
        try:
            result = await runner.run()
            return result
        finally:
            if progress_cb is not None:
                # stop live display first, then show summary
                progress_cb.stop()
                await progress_cb.suite_completed(result)
