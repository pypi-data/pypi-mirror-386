"""Utilities for generating input datasets."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence

import yaml

from fluxloop.schemas import (
    ExperimentConfig,
    InputGenerationMode,
    PersonaConfig,
    VariationStrategy,
)

from .llm_generator import DEFAULT_STRATEGIES, LLMGenerationError, generate_llm_inputs

if TYPE_CHECKING:
    from .llm_generator import LLMClient


@dataclass
class GenerationSettings:
    """Options controlling input generation."""

    limit: Optional[int] = None
    dry_run: bool = False
    mode: Optional[InputGenerationMode] = None
    strategies: Optional[Sequence[VariationStrategy]] = None
    use_cache: bool = True
    llm_api_key_override: Optional[str] = None
    llm_client: Optional["LLMClient"] = None


@dataclass
class GeneratedInput:
    """Represents a single generated input entry."""

    input: str
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Container for generation output."""

    entries: List[GeneratedInput]
    metadata: Dict[str, object]

    def to_yaml(self) -> str:
        payload = {
            "generated_at": dt.datetime.utcnow().isoformat() + "Z",
            "metadata": self.metadata,
            "inputs": [
                {
                    "input": entry.input,
                    "metadata": entry.metadata,
                }
                for entry in self.entries
            ],
        }
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    def to_json(self) -> str:
        return json.dumps(
            {
                "generated_at": dt.datetime.utcnow().isoformat() + "Z",
                "metadata": self.metadata,
                "inputs": [
                    {
                        "input": entry.input,
                        "metadata": entry.metadata,
                    }
                    for entry in self.entries
                ],
            },
            indent=2,
        )


class GenerationError(Exception):
    """Raised when input generation cannot proceed."""


def generate_inputs(
    config: ExperimentConfig,
    settings: GenerationSettings,
    recording_template: Optional[Dict[str, Any]] = None,
) -> GenerationResult:
    """Generate deterministic input entries based on configuration."""
    base_inputs = config.base_inputs
    config_for_generation = config
    if recording_template:
        base_inputs = [
            {
                "input": recording_template["base_content"],
                "metadata": {
                    "source": "recording",
                    "target": recording_template.get("target"),
                },
            }
        ]
        config_for_generation = config.model_copy(update={"base_inputs": base_inputs})

    if not base_inputs:
        raise GenerationError("base_inputs must be defined to generate inputs")

    mode = settings.mode or config_for_generation.input_generation.mode

    if mode == InputGenerationMode.LLM:
        strategies: Sequence[VariationStrategy]
        if settings.strategies and len(settings.strategies) > 0:
            strategies = list(settings.strategies)
        elif config_for_generation.variation_strategies:
            strategies = config_for_generation.variation_strategies
        else:
            strategies = DEFAULT_STRATEGIES

        try:
            raw_entries = generate_llm_inputs(
                config=config_for_generation,
                strategies=strategies,
                settings=settings,
            )
        except LLMGenerationError as exc:
            raise GenerationError(str(exc)) from exc

        entries = [
            GeneratedInput(input=item["input"], metadata=item.get("metadata", {}))
            for item in raw_entries
        ]

        metadata = {
            "config_name": config_for_generation.name,
            "total_base_inputs": len(base_inputs),
            "total_personas": len(config_for_generation.personas),
            "strategies": [strategy.value for strategy in strategies],
            "limit": settings.limit,
            "generation_mode": InputGenerationMode.LLM.value,
            "llm_provider": config_for_generation.input_generation.llm.provider,
            "llm_model": config_for_generation.input_generation.llm.model,
        }

        if recording_template:
            for entry in entries:
                entry.metadata["args_template"] = "use_recorded"
                entry.metadata["template_kwargs"] = recording_template.get("full_kwargs")
            metadata["recording_target"] = recording_template.get("target")
            metadata["recording_base_input"] = recording_template.get("base_content")

        return GenerationResult(entries=entries, metadata=metadata)

    raise GenerationError(
        "Only LLM-based generation is supported. Set input_generation.mode to 'llm'"
    )
