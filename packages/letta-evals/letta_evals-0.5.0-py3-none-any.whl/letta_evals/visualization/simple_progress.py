from __future__ import annotations

from typing import Dict, Optional

from rich.console import Console

from letta_evals.visualization.base import ProgressCallback


class SimpleProgress(ProgressCallback):
    """Clean hierarchical progress callback for CI and non-interactive terminals.

    Uses visual hierarchy with indentation and simple unicode symbols to make
    evaluation progress easy to scan in logs.
    """

    def __init__(self, suite_name: str, total_samples: int, console: Optional[Console] = None):
        self.suite_name = suite_name
        self.total_samples = total_samples
        self.console = console or Console()
        self._current_sample = None

    async def start(self) -> None:
        self.console.print("━" * 60)
        self.console.print(f"[bold cyan]Suite:[/] {self.suite_name}")
        self.console.print(f"[bold cyan]Samples:[/] {self.total_samples}")
        self.console.print("━" * 60)
        self.console.print()

    def stop(self) -> None:
        self.console.print()
        self.console.print("━" * 60)
        self.console.print("[bold cyan]Suite completed[/]")
        self.console.print("━" * 60)

    def reset(self) -> None:
        """Reset state for a new run"""
        self._current_sample = None

    async def sample_started(
        self, sample_id: int, agent_id: Optional[str] = None, model_name: Optional[str] = None
    ) -> None:
        # track current sample to avoid printing header multiple times
        self._current_sample = (sample_id, model_name)
        model_text = f" [dim]({model_name})[/]" if model_name else ""
        agent_text = f" [dim]agent={agent_id}[/]" if agent_id else ""
        self.console.print(f"[bold cyan]▸ Sample [{sample_id}]{model_text}{agent_text}[/]")

    async def agent_loading(
        self, sample_id: int, agent_id: Optional[str] = None, model_name: Optional[str] = None, from_cache: bool = False
    ) -> None:
        prefix = self._format_prefix(sample_id, agent_id, model_name)
        cache_text = " [dim](cached)[/]" if from_cache else ""
        self.console.print(f"{prefix} [dim]•[/] Loading agent{cache_text}")

    async def message_sending(
        self,
        sample_id: int,
        message_num: int,
        total_messages: int,
        agent_id: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        prefix = self._format_prefix(sample_id, agent_id, model_name)
        self.console.print(f"{prefix} [dim]•[/] Sending messages {message_num}/{total_messages}")

    async def grading_started(
        self, sample_id: int, agent_id: Optional[str] = None, model_name: Optional[str] = None
    ) -> None:
        prefix = self._format_prefix(sample_id, agent_id, model_name)
        self.console.print(f"{prefix} [dim]•[/] Grading...")

    async def sample_completed(
        self,
        sample_id: int,
        passed: bool,
        agent_id: Optional[str] = None,
        score: Optional[float] = None,
        model_name: Optional[str] = None,
        metric_scores: Optional[Dict[str, float]] = None,
        metric_pass: Optional[Dict[str, bool]] = None,
        rationale: Optional[str] = None,
        metric_rationales: Optional[Dict[str, str]] = None,
    ) -> None:
        prefix = self._format_prefix(sample_id, agent_id, model_name)
        status = "[bold green]✓ PASS[/]" if passed else "[bold red]✗ FAIL[/]"
        parts = [f"{prefix} {status}"]

        if score is not None:
            parts.append(f"score={score:.2f}")

        if metric_scores:
            metric_bits = ", ".join(f"{k}={v:.2f}" for k, v in metric_scores.items())
            parts.append(metric_bits)

        self.console.print("  ".join(parts))

    async def sample_error(
        self, sample_id: int, error: str, agent_id: Optional[str] = None, model_name: Optional[str] = None
    ) -> None:
        prefix = self._format_prefix(sample_id, agent_id, model_name)
        self.console.print(f"{prefix} [bold yellow]⚠ ERROR[/]: {error}")

    async def suite_completed(self, result):
        """Display summary results after evaluation completes"""
        from rich.table import Table

        from letta_evals.constants import MAX_SAMPLES_DISPLAY
        from letta_evals.models import GateSpec

        self.console.print()
        self.console.print("[bold]Evaluation Results:[/bold]")
        self.console.print("=" * 50)

        # overall metrics
        metrics = result.metrics
        self.console.print("\n[bold]Overall Metrics:[/bold]")
        self.console.print(f"  Total samples: {metrics.total}")
        self.console.print(f"  Total attempted: {metrics.total_attempted}")
        errors = metrics.total - metrics.total_attempted
        errors_pct = (errors / metrics.total * 100.0) if metrics.total > 0 else 0.0
        self.console.print(f"  Errored: {errors_pct:.1f}% ({errors}/{metrics.total})")
        self.console.print(f"  Average score (attempted): {metrics.avg_score_attempted:.2f}")
        self.console.print(f"  Average score (total): {metrics.avg_score_total:.2f}")

        # gate status
        gate = result.config["gate"]
        gate_op = gate["op"]
        gate_value = gate["value"]
        gate_metric = gate.get("metric", "avg_score")

        op_symbols = {"gt": ">", "gte": "≥", "lt": "<", "lte": "≤", "eq": "="}
        op_symbol = op_symbols.get(gate_op, gate_op)

        status = "[green]PASSED[/green]" if result.gates_passed else "[red]FAILED[/red]"
        self.console.print(f"\n[bold]Gate:[/bold] {gate_metric} {op_symbol} {gate_value:.2f} → {status}")

        # sample results table
        self.console.print("\n[bold]Sample Results:[/bold]")

        total_samples = len(result.results)
        samples_to_display = result.results[:MAX_SAMPLES_DISPLAY]

        if total_samples > MAX_SAMPLES_DISPLAY:
            self.console.print(f"[dim]Showing first {MAX_SAMPLES_DISPLAY} of {total_samples} samples[/dim]")

        table = Table(show_header=True)
        table.add_column("Sample", style="cyan")
        table.add_column("Agent ID", style="dim cyan")
        table.add_column("Model", style="yellow")
        table.add_column("Passed", style="white")

        # determine available metrics
        metric_keys = []
        metric_labels = {}
        if "graders" in result.config and isinstance(result.config["graders"], dict):
            for k, gspec in result.config["graders"].items():
                metric_keys.append(k)
                metric_labels[k] = gspec.get("display_name") or k

        # add score columns per metric
        for mk in metric_keys:
            lbl = metric_labels.get(mk, mk)
            table.add_column(f"{lbl} score", style="white")

        gate_spec = GateSpec(**result.config["gate"])

        for sample_result in samples_to_display:
            score_val = sample_result.grade.score
            passed = "✓" if gate_spec.check_sample(score_val) else "✗"

            # build per-metric score cells
            cells = []
            for mk in metric_keys:
                g = sample_result.grades.get(mk) if sample_result.grades else None
                if g is None:
                    cells.append("-")
                else:
                    try:
                        s_val = float(getattr(g, "score", None))
                    except Exception:
                        try:
                            s_val = float(g.get("score"))
                        except Exception:
                            s_val = None
                    score_cell = f"{s_val:.2f}" if s_val is not None else "-"
                    cells.append(score_cell)

            table.add_row(
                f"Sample {sample_result.sample.id + 1}",
                sample_result.agent_id or "-",
                sample_result.model_name or "-",
                passed,
                *cells,
            )

        self.console.print(table)

        if total_samples > MAX_SAMPLES_DISPLAY:
            self.console.print(
                f"[dim]... and {total_samples - MAX_SAMPLES_DISPLAY} more samples (see output file for complete results)[/dim]"
            )

    def _format_prefix(self, sample_id: int, agent_id: Optional[str], model_name: Optional[str]) -> str:
        """format a compact prefix for substeps to show which sample they belong to."""
        parts = [f"[dim]\\[[/][cyan]{sample_id}[/][dim]][/]"]
        if model_name:
            parts.append(f"[dim]({model_name})[/]")
        if agent_id:
            parts.append(f"[dim]agent={agent_id}[/]")
        return "".join(parts)
