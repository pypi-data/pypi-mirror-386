"""Generate command for producing input datasets."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from dotenv import dotenv_values

from ..config_loader import load_experiment_config
from ..input_generator import GenerationSettings, generate_inputs
from ..llm_generator import DEFAULT_STRATEGIES
from ..validators import parse_variation_strategies
from ..constants import DEFAULT_CONFIG_PATH, DEFAULT_ROOT_DIR_NAME
from ..project_paths import (
    resolve_config_path,
    resolve_project_relative,
    resolve_root_dir,
)
from fluxloop.schemas import InputGenerationMode, VariationStrategy

app = typer.Typer()
console = Console()


@app.command()
def inputs(
    config_file: Path = typer.Option(
        DEFAULT_CONFIG_PATH,
        "--config",
        "-c",
        help="Path to experiment configuration file",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        help="Project name under the FluxLoop root",
    ),
    root: Path = typer.Option(
        Path(DEFAULT_ROOT_DIR_NAME),
        "--root",
        help="FluxLoop root directory",
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to write generated inputs file (defaults to setting.yaml -> inputs_file)",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of inputs to generate",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print planned generation without creating a file",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Allow overwriting an existing output file",
    ),
    mode: Optional[InputGenerationMode] = typer.Option(
        None,
        "--mode",
        case_sensitive=False,
        help="Generation mode: deterministic or llm",
    ),
    strategy: List[str] = typer.Option(  # type: ignore[assignment]
        None,
        "--strategy",
        "-s",
        help="Variation strategy to request (repeatable)",
    ),
    llm_provider: Optional[str] = typer.Option(
        None,
        "--llm-provider",
        help="Override LLM provider for input generation",
    ),
    llm_model: Optional[str] = typer.Option(
        None,
        "--llm-model",
        help="Override LLM model identifier",
    ),
    llm_api_key: Optional[str] = typer.Option(
        None,
        "--llm-api-key",
        help="API key for LLM provider (falls back to FLUXLOOP_LLM_API_KEY)",
    ),
    from_recording: Optional[Path] = typer.Option(
        None,
        "--from-recording",
        help="Use a recorded call (JSONL) as template for generated inputs",
    ),
):
    """Generate input variations for review before running experiments."""
    resolved_config = resolve_config_path(config_file, project, root)
    if not resolved_config.exists():
        console.print(f"[red]Error:[/red] Configuration file not found: {config_file}")
        raise typer.Exit(1)

    # Generating inputs should not require the inputs file to exist yet.
    require_inputs_file = False

    # Load environment variables (project-level overrides root-level)
    env_values: Dict[str, str] = {}

    resolved_root = resolve_root_dir(root)
    root_env_path = resolved_root / ".env"
    if root_env_path.exists():
        env_values.update(
            {
                key: value
                for key, value in dotenv_values(root_env_path).items()
                if value is not None
            }
        )

    if project:
        project_env_path = resolve_project_relative(Path(".env"), project, root)
        if project_env_path.exists():
            env_values.update(
                {
                    key: value
                    for key, value in dotenv_values(project_env_path).items()
                    if value is not None
                }
            )

    try:
        config = load_experiment_config(
            resolved_config,
            require_inputs_file=require_inputs_file,
        )
    except Exception as exc:
        console.print(f"[red]Error loading configuration:[/red] {exc}")
        raise typer.Exit(1)

    # Determine output path (CLI option overrides config)
    output_path = output_file or Path(config.inputs_file or "inputs/generated.yaml")
    resolved_output = resolve_project_relative(output_path, project, root)

    if resolved_output.exists() and not overwrite and not dry_run:
        console.print(
            f"[red]Error:[/red] Output file already exists: {resolved_output}\n"
            "Use --overwrite to replace it."
        )
        raise typer.Exit(1)

    console.print(f"📋 Loading configuration from: [cyan]{resolved_config}[/cyan]")

    strategies: Optional[List[VariationStrategy]] = None
    if strategy:
        strategies = parse_variation_strategies(strategy)

    # Apply CLI overrides to configuration
    if mode:
        config.input_generation.mode = mode
        if mode == InputGenerationMode.LLM:
            config.input_generation.llm.enabled = True

    if llm_provider:
        config.input_generation.llm.provider = llm_provider
        config.input_generation.llm.enabled = True

    if llm_model:
        config.input_generation.llm.model = llm_model
        config.input_generation.llm.enabled = True

    resolved_api_key = (
        llm_api_key
        or config.input_generation.llm.api_key
        or env_values.get("FLUXLOOP_LLM_API_KEY")
        or env_values.get("OPENAI_API_KEY")
        or os.getenv("FLUXLOOP_LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    if resolved_api_key:
        config.input_generation.llm.api_key = resolved_api_key

    if (
        config.input_generation.mode == InputGenerationMode.LLM
        and not config.input_generation.llm.api_key
    ):
        console.print(
            "[yellow]Warning:[/yellow] LLM mode requested but no API key provided."
        )

    settings = GenerationSettings(
        limit=limit,
        dry_run=dry_run,
        mode=mode,
        strategies=strategies,
        llm_api_key_override=llm_api_key,
    )

    recording_template = None
    if from_recording:
        try:
            recording_template = _load_recording_template(from_recording, config)
            console.print(
                "📝 Generating inputs from recording"
                f"\n  → Base content: [cyan]{recording_template['base_content'][:60]}[/cyan]"
            )
        except Exception as exc:
            console.print(f"[red]Failed to load recording template:[/red] {exc}")
            raise typer.Exit(1)

    try:
        result = generate_inputs(config, settings, recording_template=recording_template)
    except Exception as exc:
        console.print(f"[red]Generation failed:[/red] {exc}")
        if "--debug" in sys.argv:
            console.print_exception()
        raise typer.Exit(1)

    if dry_run:
        console.print("\n[yellow]Dry run mode - no file written[/yellow]")
        console.print(f"Planned inputs: {len(result.entries)}")
        return

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(result.to_yaml(), encoding="utf-8")

    strategies_used = result.metadata.get("strategies") or [s.value for s in DEFAULT_STRATEGIES]

    console.print(
        "\n[bold green]Generation complete![/bold green]"
        f"\n📝 Inputs written to: [cyan]{resolved_output}[/cyan]"
        f"\n✨ Total inputs: [green]{len(result.entries)}[/green]"
        f"\n🧠 Mode: [magenta]{result.metadata.get('generation_mode', 'deterministic')}[/magenta]"
        f"\n🎯 Strategies: [cyan]{', '.join(strategy for strategy in strategies_used)}[/cyan]"
    )


def _load_recording_template(path: Path, config: "ExperimentConfig") -> Dict[str, object]:
    target_path = path
    if not target_path.is_absolute():
        source_dir = config.get_source_dir()
        if source_dir:
            target_path = (source_dir / target_path).resolve()
        else:
            target_path = target_path.resolve()

    if not target_path.exists():
        raise FileNotFoundError(f"Recording file not found: {target_path}")

    with target_path.open("r", encoding="utf-8") as handle:
        first_line = handle.readline()

    if not first_line:
        raise ValueError(f"Recording file is empty: {target_path}")

    try:
        record = json.loads(first_line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in recording file {target_path}: {exc}")

    kwargs = record.get("kwargs", {})
    base_content = _extract_content(kwargs)
    if not base_content:
        sample = json.dumps(kwargs, indent=2)[:500]
        raise ValueError(
            "Unable to locate textual content in recording. "
            "Expected keys such as data.content, input, input_text, message, query, text, or content." \
            f"\nRecording snapshot:\n{sample}"
        )

    return {
        "base_content": base_content,
        "full_kwargs": kwargs,
        "target": record.get("target"),
    }


def _extract_content(kwargs: Dict[str, Any]) -> Optional[str]:
    content_paths = [
        "data.content",
        "input",
        "input_text",
        "message",
        "query",
        "text",
        "content",
    ]

    for path in content_paths:
        try:
            current: Any = kwargs
            for part in path.split('.'):
                current = current[part]
            if isinstance(current, str) and current:
                return current
        except (KeyError, TypeError):
            continue

    return None
